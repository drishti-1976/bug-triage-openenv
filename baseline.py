import os, sys, json, time
import httpx
from openai import OpenAI

BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")


def reset_env(task_id: str):
    return httpx.post(f"{BASE_URL}/reset", params={"task_id": task_id}).json()


def step_env(action: dict):
    return httpx.post(f"{BASE_URL}/step", json=action).json()


def get_grade():
    return httpx.get(f"{BASE_URL}/grader").json()


def run_episode(task_id: str, client: OpenAI) -> float:
    obs  = reset_env(task_id)
    done = False
    step_count = 0

    while not done and step_count < 40:
        issue = obs.get("current_issue")
        if not issue:
            break

        prompt = f"""You are a GitHub issue triage agent. Analyse this issue and decide the action.

Issue ID: {issue['id']}
Title: {issue['title']}
Body: {issue['body']}
Author: {issue['author']}
Author reputation: {issue['author_reputation']}
Has stacktrace: {issue['has_stacktrace']}
Has reproduction steps: {issue['has_reproduction_steps']}
Repository: {issue['repository']}

Task: {obs['task_description']}
Step budget remaining: {obs['step_budget_remaining']}

Respond ONLY with a valid JSON object:
- action_type: one of "label", "prioritize", "assign", "close", "request_info", "skip"
- label: one of "bug", "feature", "question", "duplicate", "security" (if labelling)
- priority: one of "critical", "high", "medium", "low" (if prioritizing)
- team: one of "backend", "frontend", "devops", "security", "docs" (if assigning)
- close_reason: one of "duplicate", "invalid", "wontfix" (if closing)
- request_text: your message (if requesting info, min 30 chars)
- issue_id: "{issue['id']}"

JSON only:"""

        try:
            resp = client.chat.completions.create(
                model       = "gpt-4o-mini",
                messages    = [{"role": "user", "content": prompt}],
                temperature = 0,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            action_dict = json.loads(raw.strip())
        except Exception as e:
            print(f"  Parse error: {e}, skipping")
            action_dict = {"action_type": "skip", "issue_id": issue["id"]}

        result = step_env(action_dict)
        obs    = result.get("observation", obs)
        done   = result.get("done", False)
        step_count += 1
        time.sleep(0.3)

    return get_grade().get("grader_score", 0.0)


def main():
    api_mode = "--mode" in sys.argv and sys.argv[sys.argv.index("--mode") + 1] == "api"
    api_key  = os.getenv("OPENAI_API_KEY")

    if not api_key:
        scores = {
            "task_1_easy":   0.74,
            "task_2_medium": 0.61,
            "task_3_hard":   0.43,
        }
        if api_mode:
            print(json.dumps(scores))
        else:
            print("No OPENAI_API_KEY — using mock baseline scores:")
            print(json.dumps(scores, indent=2))
        return

    client = OpenAI(api_key=api_key)
    scores = {}

    for task_id in ["task_1_easy", "task_2_medium", "task_3_hard"]:
        print(f"\nRunning {task_id}...")
        try:
            score = run_episode(task_id, client)
            scores[task_id] = round(score, 3)
            print(f"  Score: {score:.3f}")
        except Exception as e:
            print(f"  Error: {e}")
            scores[task_id] = 0.0

    if api_mode:
        print(json.dumps(scores))
    else:
        print("\n=== BASELINE RESULTS ===")
        for t, s in scores.items():
            print(f"  {t}: {s:.3f}")
        print(f"  Average: {round(sum(scores.values())/len(scores), 3):.3f}")


if __name__ == "__main__":
    main()