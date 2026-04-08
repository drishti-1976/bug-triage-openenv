"""
inference.py — Bug Triage OpenEnv
MANDATORY env vars: API_BASE_URL, MODEL_NAME, HF_TOKEN
"""

import os
import json
import time
import sys
import httpx
from openai import OpenAI

# ── Mandatory env vars ────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN")    or os.getenv("API_KEY", "no-key")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "https://drishti1976-bug-triage-env.hf.space")

# ── OpenAI client ─────────────────────────────────────────────────────────────
client = OpenAI(
    base_url = API_BASE_URL,
    api_key  = HF_TOKEN,
)

TASK_TIME_LIMIT = 360
MAX_STEPS       = 40


# ── Environment helpers ───────────────────────────────────────────────────────

def reset_env(task_id: str) -> dict:
    r = httpx.post(
        f"{ENV_BASE_URL}/reset",
        params={"task_id": task_id},
        timeout=30
    )
    return r.json()


def step_env(action: dict) -> dict:
    r = httpx.post(
        f"{ENV_BASE_URL}/step",
        json=action,
        timeout=30
    )
    return r.json()


def get_grade() -> dict:
    r = httpx.get(f"{ENV_BASE_URL}/grader", timeout=30)
    return r.json()


# ── LLM call ─────────────────────────────────────────────────────────────────

def call_llm(prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model       = MODEL_NAME,
            messages    = [{"role": "user", "content": prompt}],
            temperature = 0.0,
            max_tokens  = 300,
        )
        return completion.choices[0].message.content or ""
    except Exception as e:
        return ""


def parse_action(response: str, issue_id: str) -> dict:
    try:
        raw = response.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return {"action_type": "skip", "issue_id": issue_id}


def build_prompt(issue: dict, obs: dict) -> str:
    return f"""You are a GitHub issue triage agent. Analyse this issue and respond with ONE JSON action.

Issue ID: {issue['id']}
Title: {issue['title']}
Body: {issue['body']}
Author: {issue['author']}
Author reputation: {issue['author_reputation']}
Has stacktrace: {issue['has_stacktrace']}
Has reproduction steps: {issue['has_reproduction_steps']}

Task: {obs['task_description']}
Step budget remaining: {obs['step_budget_remaining']}

Respond ONLY with valid JSON:
{{
  "action_type": "label" | "prioritize" | "assign" | "close" | "request_info" | "skip",
  "label": "bug" | "feature" | "question" | "duplicate" | "security",
  "priority": "critical" | "high" | "medium" | "low",
  "team": "backend" | "frontend" | "devops" | "security" | "docs",
  "close_reason": "duplicate" | "invalid" | "wontfix",
  "request_text": "your message",
  "issue_id": "{issue['id']}"
}}"""


# ── Episode runner ────────────────────────────────────────────────────────────

def run_episode(task_id: str) -> float:
    obs        = reset_env(task_id)
    done       = False
    step_count = 0
    start_time = time.time()

    # ── [START] block ─────────────────────────────────────────────────────────
    print(f"[START] task={task_id}", flush=True)

    while not done and step_count < MAX_STEPS:
        if time.time() - start_time > TASK_TIME_LIMIT:
            print(f"[STEP] step={step_count} reward=0.0 info=timeout", flush=True)
            break

        issue = obs.get("current_issue")
        if not issue:
            break

        # Call LLM or use rule-based fallback if no token
        if HF_TOKEN == "no-key":
            action = rule_agent(issue)
        else:
            prompt   = build_prompt(issue, obs)
            response = call_llm(prompt)
            action   = parse_action(response, issue["id"])

        result     = step_env(action)
        reward_val = result.get("reward", {}).get("value", 0.0)
        obs        = result.get("observation", obs)
        done       = result.get("done", False)
        step_count += 1

        # ── [STEP] block ──────────────────────────────────────────────────────
        print(
            f"[STEP] step={step_count} "
            f"reward={round(reward_val, 3)} "
            f"action={action.get('action_type')} "
            f"issue={issue['id']}",
            flush=True
        )

        time.sleep(0.2)

    grade = get_grade()
    score = round(grade.get("grader_score", 0.0), 3)

    # ── [END] block ───────────────────────────────────────────────────────────
    print(f"[END] task={task_id} score={score} steps={step_count}", flush=True)

    return score


# ── Rule-based fallback agent ─────────────────────────────────────────────────

def rule_agent(issue: dict) -> dict:
    text = (issue["title"] + " " + issue["body"] + " " + issue["author"]).lower()
    if any(w in text for w in ["sql injection", "xss", "vulnerability", "exploit", "security"]):
        label, priority, team = "security", "critical", "security"
    elif any(w in text for w in ["crash", "error", "exception", "broken", "not working", "bug", "fail"]):
        label, priority, team = "bug", "high", "backend"
    elif any(w in text for w in ["feature request", "add support", "would be great", "please add"]):
        label, priority, team = "feature", "medium", "backend"
    elif any(w in text for w in ["how do i", "how to", "documentation", "question"]):
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
            "Could you provide reproduction steps and environment details?"
        )
    return action


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== Bug Triage OpenEnv — Inference Script ===", flush=True)
    print(f"API_BASE_URL : {API_BASE_URL}", flush=True)
    print(f"MODEL_NAME   : {MODEL_NAME}", flush=True)
    print(f"HF_TOKEN     : {'set' if HF_TOKEN != 'no-key' else 'NOT SET — using rule-based agent'}", flush=True)
    print(f"ENV_BASE_URL : {ENV_BASE_URL}", flush=True)
    print("=" * 45, flush=True)

    scores     = {}
    total_start = time.time()

    for task_id in ["task_1_easy", "task_2_medium", "task_3_hard"]:
        try:
            score = run_episode(task_id)
            scores[task_id] = score
        except Exception as e:
            print(f"[END] task={task_id} score=0.0 steps=0 error={e}", flush=True)
            scores[task_id] = 0.0

    print("=" * 45, flush=True)
    print("=== FINAL RESULTS ===", flush=True)
    for task_id, score in scores.items():
        print(f"  {task_id}: {score:.3f}", flush=True)

    avg = round(sum(scores.values()) / len(scores), 3)
    print(f"  Average: {avg:.3f}", flush=True)
    print(f"  Total time: {round(time.time() - total_start)}s", flush=True)
    print(json.dumps(scores), flush=True)


if __name__ == "__main__":
    main()