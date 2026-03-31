from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class GitHubIssue(BaseModel):
    id: str
    number: int
    title: str
    body: str
    author: str
    author_reputation: str        # "trusted", "new", "unknown"
    comments: int
    created_at: str
    has_stacktrace: bool
    has_reproduction_steps: bool
    repository: str


class Observation(BaseModel):
    current_issue: Optional[GitHubIssue]
    inbox_size: int
    issues_processed: int
    current_task_id: str
    task_description: str
    available_actions: List[str]
    step_budget_remaining: int = 0
    reporter_history: Dict[str, str] = {}   # author → reputation signal


class Action(BaseModel):
    action_type: str
    # one of:
    #   "label"       — assign a label
    #   "prioritize"  — set priority
    #   "assign"      — assign to a team
    #   "close"       — close as duplicate/invalid/wontfix
    #   "request_info"— ask reporter for more details
    #   "skip"        — move on without acting

    label: Optional[str] = None
    # one of: "bug", "feature", "question", "duplicate",
    #         "wontfix", "good-first-issue", "security"

    priority: Optional[str] = None
    # one of: "critical", "high", "medium", "low"

    team: Optional[str] = None
    # one of: "backend", "frontend", "devops", "security", "docs"

    close_reason: Optional[str] = None
    # one of: "duplicate", "invalid", "wontfix", "resolved"

    request_text: Optional[str] = None
    # text asking reporter for reproduction steps / env info

    issue_id: Optional[str] = None


class Reward(BaseModel):
    value: float
    reason: str
    partial_credits: Dict[str, float] = {}


class StepResult(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any] = {}


class StateModel(BaseModel):
    task_id: str
    episode_step: int
    total_reward: float
    issues_processed: int
    inbox_size: int
    done: bool
    action_history: List[Dict[str, Any]]