from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.environment import BugTriageEnv
from app.models import Action
from app.tasks import TASKS, GRADERS, make_tasks
import os

app = FastAPI(
    title="Bug Triage OpenEnv",
    description="Real-world GitHub issue triage environment for AI agents",
    version="1.0.0",
)

env = BugTriageEnv()

# Serve static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"status": "ok", "env": "bug-triage-openenv", "version": "1.0.0"}


@app.get("/api")
def api_root():
    return {"status": "ok", "env": "bug-triage-openenv", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/reset")
def reset(task_id: str = "task_1_easy"):
    valid = ["task_1_easy", "task_2_medium", "task_3_hard"]
    if task_id not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task_id '{task_id}'. Choose from {valid}"
        )
    obs = env.reset(task_id=task_id)
    return obs.model_dump()


@app.post("/step")
def step(action: Action):
    result = env.step(action)
    return result.model_dump()


@app.get("/state")
def state():
    return env.state().model_dump()


@app.get("/tasks")
def list_tasks():
    fresh = make_tasks()
    tasks_info = [
        {
            "id":         tid,
            "name":       task["name"],
            "description":task["description"],
            "difficulty": task["difficulty"],
            "max_steps":  task["max_steps"],
            "num_issues": len(task["issues"]),
        }
        for tid, task in fresh.items()
    ]
    action_schema = {
        "action_type":  "string — one of: label, prioritize, assign, close, request_info, skip",
        "label":        "string (optional) — bug | feature | question | duplicate | wontfix | security",
        "priority":     "string (optional) — critical | high | medium | low",
        "team":         "string (optional) — backend | frontend | devops | security | docs",
        "close_reason": "string (optional) — duplicate | invalid | wontfix | resolved",
        "request_text": "string (optional) — message asking reporter for more details",
        "issue_id":     "string (optional) — id of the issue being acted on",
    }
    return {"tasks": tasks_info, "action_schema": action_schema}


@app.get("/grader")
def grader():
    score = env.grade()
    return {
        "task_id":      env.task_id,
        "grader_score": score,
        "episode_done": env.done,
        "action_count": len(env.action_history),
    }


@app.get("/baseline")
def baseline():
    def rule_agent(issue: dict) -> dict:
        text = (
            issue["title"] + " " + issue["body"] + " " + issue["author"]
        ).lower()

        if any(w in text for w in ["sql injection", "xss", "vulnerability",
                                    "security", "exploit", "proof of concept"]):
            label, priority, team = "security", "critical", "security"
        elif any(w in text for w in ["crash", "error", "exception", "broken",
                                      "not working", "bug", "null", "fail"]):
            label, priority, team = "bug", "high", "backend"
        elif any(w in text for w in ["feature request", "add support", "would be great",
                                      "please add", "export", "enhancement"]):
            label, priority, team = "feature", "medium", "backend"
        elif any(w in text for w in ["how do i", "how to", "recommended way",
                                      "documentation", "configure", "question"]):
            label, priority, team = "question", "low", "docs"
        elif any(w in text for w in ["same as issue", "already reported", "duplicate"]):
            label, priority, team = "duplicate", "low", None
        else:
            label, priority, team = "question", "low", None

        action: dict = {
            "action_type": "label",
            "label":       label,
            "priority":    priority,
            "issue_id":    issue["id"],
        }
        if team:
            action["team"] = team
        if label == "duplicate":
            action["action_type"] = "close"
            action["close_reason"] = "duplicate"
        if not issue["has_reproduction_steps"] and not issue["has_stacktrace"] \
                and label not in ("feature", "question", "duplicate"):
            action["action_type"] = "request_info"
            action["request_text"] = (
                "Could you please provide reproduction steps, "
                "your environment details, and any error messages?"
            )
        return action

    scores = {}
    for task_id, task in make_tasks().items():
        action_history = []
        for issue in task["issues"]:
            act = rule_agent(issue)
            act["issue_id"] = issue["id"]
            action_history.append(act)
        scores[task_id] = round(GRADERS[task_id](
            action_history, task["correct_answers"]
        ), 3)

    return {
        "status":  "success",
        "agent":   "rule-based keyword baseline",
        "scores":  scores,
        "average": round(sum(scores.values()) / len(scores), 3),
    }


@app.get("/validate")
def validate():
    return {
        "name":      "bug-triage-openenv",
        "version":   "1.0.0",
        "compliant": True,
        "endpoints": {
            "reset":    "POST /reset",
            "step":     "POST /step",
            "state":    "GET  /state",
            "tasks":    "GET  /tasks",
            "grader":   "GET  /grader",
            "baseline": "GET  /baseline",
        },
        "tasks":  ["task_1_easy", "task_2_medium", "task_3_hard"],
        "models": {
            "observation": "Observation",
            "action":      "Action",
            "reward":      "Reward",
        },
    }