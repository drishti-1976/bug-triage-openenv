import copy
from app.models import (
    Observation, Action, Reward, StepResult, StateModel, GitHubIssue
)
from app.tasks import make_tasks, GRADERS
from app.rewards import compute_reward
from typing import Dict, Any, List


class BugTriageEnv:
    def __init__(self):
        self.task_id:         str               = "task_1_easy"
        self.issues:          List[Dict]        = []
        self.correct_answers: Dict[str, Any]    = {}
        self._current_task:   Dict[str, Any]    = {}
        self.current_index:   int               = 0
        self.episode_step:    int               = 0
        self.total_reward:    float             = 0.0
        self.done:            bool              = False
        self.action_history:  List[Dict[str, Any]] = []
        # reporter reputation tracker: author → list of labels seen
        self.reporter_history: Dict[str, str]  = {}

    def reset(self, task_id: str = "task_1_easy") -> Observation:
        fresh_tasks           = make_tasks()     # new random issues every episode
        self.task_id          = task_id
        task                  = fresh_tasks[task_id]
        self._current_task    = task
        self.issues           = copy.deepcopy(task["issues"])
        self.correct_answers  = task["correct_answers"]
        self.current_index    = 0
        self.episode_step     = 0
        self.total_reward     = 0.0
        self.done             = False
        self.action_history   = []
        self.reporter_history = {}
        return self._make_observation()

    def step(self, action: Action) -> StepResult:
        if self.done:
            return StepResult(
                observation=self._make_observation(),
                reward=Reward(value=0.0, reason="Episode already done"),
                done=True,
                info={"warning": "Episode already finished"}
            )

        task          = self._current_task
        current_issue = self.issues[self.current_index]
        self.episode_step += 1

        # Record action
        action_record               = action.model_dump()
        action_record["issue_id"]   = current_issue["id"]
        action_record["step"]       = self.episode_step
        self.action_history.append(action_record)

        # Update reporter reputation tracker
        author = current_issue.get("author", "unknown")
        if author not in self.reporter_history:
            self.reporter_history[author] = current_issue.get(
                "author_reputation", "unknown"
            )

        # Compute reward
        reward = compute_reward(
            action         = action,
            issue          = current_issue,
            correct_answers= self.correct_answers,
            step           = self.episode_step,
            max_steps      = task["max_steps"],
            action_history = self.action_history,
        )
        self.total_reward += reward.value

        # Terminal actions advance to next issue
        terminal_actions = {"label", "close", "skip"}
        if action.action_type in terminal_actions:
            self.current_index += 1

        # Check done
        self.done = (
            self.current_index >= len(self.issues)
            or self.episode_step >= task["max_steps"]
        )

        return StepResult(
            observation = self._make_observation(),
            reward      = reward,
            done        = self.done,
            info        = {
                "episode_step":     self.episode_step,
                "total_reward":     round(self.total_reward, 3),
                "issues_remaining": max(0, len(self.issues) - self.current_index),
            }
        )

    def state(self) -> StateModel:
        return StateModel(
            task_id          = self.task_id,
            episode_step     = self.episode_step,
            total_reward     = round(self.total_reward, 3),
            issues_processed = self.current_index,
            inbox_size       = len(self.issues),
            done             = self.done,
            action_history   = self.action_history,
        )

    def grade(self) -> float:
        grader = GRADERS.get(self.task_id)
        if grader:
            return grader(self.action_history, self.correct_answers)
        return 0.0

    def _make_observation(self) -> Observation:
        task = self._current_task

        if not task:
            return Observation(
                current_issue        = None,
                inbox_size           = 0,
                issues_processed     = 0,
                current_task_id      = self.task_id,
                task_description     = "Call /reset to start an episode",
                available_actions    = self._available_actions(),
                step_budget_remaining= 0,
                reporter_history     = {},
            )

        if self.current_index < len(self.issues):
            raw        = self.issues[self.current_index]
            issue_data = {k: v for k, v in raw.items() if not k.startswith("_")}
            issue      = GitHubIssue(**issue_data)
        else:
            issue = None

        return Observation(
            current_issue        = issue,
            inbox_size           = len(self.issues),
            issues_processed     = self.current_index,
            current_task_id      = self.task_id,
            task_description     = task["description"],
            available_actions    = self._available_actions(),
            step_budget_remaining= task["max_steps"] - self.episode_step,
            reporter_history     = self.reporter_history,
        )

    def _available_actions(self) -> List[str]:
        return ["label", "prioritize", "assign", "close", "request_info", "skip"]