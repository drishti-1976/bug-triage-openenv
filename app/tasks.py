import random
from typing import Dict, List, Any, Tuple


# ── Dynamic issue generation ──────────────────────────────────────────────────

ISSUE_TEMPLATES = {
    "bug": [
        {
            "title": "App crashes on {os} when opening {feature}",
            "body": "Steps to reproduce:\n1. Open the app\n2. Navigate to {feature}\n3. Crash occurs\n\nStacktrace:\nAttributeError: NoneType at line 42 in {module}.py",
            "author": "dev_{n}@company.com",
            "has_stacktrace": True,
            "has_reproduction_steps": True,
            "repository": "{repo}",
        },
        {
            "title": "NullPointerException in {module} module",
            "body": "Getting a null pointer exception every time I call {feature}. This breaks production.\n\nException: NullPointerException at {module}.java:128",
            "author": "senior_eng_{n}@corp.com",
            "has_stacktrace": True,
            "has_reproduction_steps": False,
            "repository": "{repo}",
        },
        {
            "title": "{feature} not working after latest update",
            "body": "Since the v2.{n} update, {feature} stopped working completely. Rolling back fixes it.",
            "author": "user_{n}@gmail.com",
            "has_stacktrace": False,
            "has_reproduction_steps": True,
            "repository": "{repo}",
        },
    ],
    "feature": [
        {
            "title": "Add support for {feature} in {module}",
            "body": "It would be great if the {module} supported {feature}. Many users have requested this. Here is a proposed API: `{module}.enable_{feature}()`",
            "author": "contributor_{n}@github.com",
            "has_stacktrace": False,
            "has_reproduction_steps": False,
            "repository": "{repo}",
        },
        {
            "title": "Feature request: export data as {feature}",
            "body": "Currently we can only export as JSON. Please add {feature} export. This is a common request on our forum.",
            "author": "power_user_{n}@org.com",
            "has_stacktrace": False,
            "has_reproduction_steps": False,
            "repository": "{repo}",
        },
    ],
    "question": [
        {
            "title": "How do I configure {feature} in {module}?",
            "body": "I have been reading the docs but I cannot figure out how to set up {feature}. Is there an example?",
            "author": "newbie_{n}@gmail.com",
            "has_stacktrace": False,
            "has_reproduction_steps": False,
            "repository": "{repo}",
        },
        {
            "title": "What is the recommended way to use {module}?",
            "body": "The documentation is unclear. Should I use {feature} directly or through the wrapper class?",
            "author": "student_{n}@university.edu",
            "has_stacktrace": False,
            "has_reproduction_steps": False,
            "repository": "{repo}",
        },
    ],
    "security": [
        {
            "title": "SQL injection vulnerability in {module} endpoint",
            "body": "Found a SQL injection in the {module} endpoint. Input is not sanitised before being passed to the query.\n\nProof of concept: `' OR '1'='1`\n\nThis allows unauthorised data access.",
            "author": "security_researcher_{n}@bugbounty.com",
            "has_stacktrace": False,
            "has_reproduction_steps": True,
            "repository": "{repo}",
        },
        {
            "title": "XSS vulnerability via {feature} input field",
            "body": "The {feature} input field does not sanitise HTML. Injecting `<script>alert(1)</script>` executes arbitrary JS.\n\nSeverity: HIGH — affects all users.",
            "author": "pentester_{n}@security.io",
            "has_stacktrace": False,
            "has_reproduction_steps": True,
            "repository": "{repo}",
        },
    ],
    "duplicate": [
        {
            "title": "{feature} broken — same as issue #{n}00",
            "body": "This is the same issue as #{n}00. {feature} still broken after supposed fix. Please reopen.",
            "author": "user_{n}@gmail.com",
            "has_stacktrace": False,
            "has_reproduction_steps": False,
            "repository": "{repo}",
        },
        {
            "title": "Bug with {module}: already reported",
            "body": "I know this was reported before but it is still happening in v{n}.0. The {module} crashes on startup.",
            "author": "reporter_{n}@email.com",
            "has_stacktrace": False,
            "has_reproduction_steps": False,
            "repository": "{repo}",
        },
    ],
    "vague": [
        {
            "title": "Something is broken",
            "body": "It does not work. Please fix.",
            "author": "angry_user_{n}@mail.com",
            "has_stacktrace": False,
            "has_reproduction_steps": False,
            "repository": "{repo}",
        },
        {
            "title": "{feature} issue",
            "body": "Having problems with {feature}. Not sure what is happening.",
            "author": "confused_{n}@outlook.com",
            "has_stacktrace": False,
            "has_reproduction_steps": False,
            "repository": "{repo}",
        },
    ],
}

FEATURES   = ["authentication", "dashboard", "payment gateway", "file upload",
               "search", "notifications", "API rate limiting", "dark mode"]
MODULES    = ["auth", "billing", "analytics", "storage", "cache", "scheduler",
              "webhook", "user_profile"]
OS_LIST    = ["Windows 11", "macOS Ventura", "Ubuntu 22.04", "Android 13"]
REPOS      = ["core-api", "frontend-app", "mobile-client", "data-pipeline"]
REPUTATIONS = ["trusted", "trusted", "new", "unknown"]   # weighted toward trusted


def generate_issue(category: str, issue_id: str, issue_number: int) -> dict:
    template = random.choice(ISSUE_TEMPLATES[category])
    n = random.randint(1, 99)
    fmt = dict(
        feature=random.choice(FEATURES),
        module=random.choice(MODULES),
        os=random.choice(OS_LIST),
        repo=random.choice(REPOS),
        n=n,
    )
    return {
        "id":                       issue_id,
        "number":                   issue_number,
        "title":                    template["title"].format(**fmt),
        "body":                     template["body"].format(**fmt),
        "author":                   template["author"].format(**fmt),
        "author_reputation":        random.choice(REPUTATIONS),
        "comments":                 random.randint(0, 12),
        "created_at":               "2024-03-15T10:00:00Z",
        "has_stacktrace":           template["has_stacktrace"],
        "has_reproduction_steps":   template["has_reproduction_steps"],
        "repository":               template["repository"].format(**fmt),
        "_category":                category,   # internal — stripped before Pydantic
    }


def generate_task_issues(
    categories: List[str],
) -> Tuple[List[dict], Dict[str, Any]]:
    issues, correct_answers = [], {}
    for i, cat in enumerate(categories):
        iid    = f"i{i+1}"
        number = 1000 + i
        issue  = generate_issue(cat, iid, number)
        issues.append(issue)

        # Derive correct answers from category
        if cat == "security":
            label, priority, team = "security", "critical", "security"
        elif cat == "bug":
            label    = "bug"
            priority = "high"
            team     = random.choice(["backend", "frontend"])
        elif cat == "feature":
            label, priority, team = "feature", "medium", "backend"
        elif cat == "question":
            label, priority, team = "question", "low", "docs"
        elif cat == "duplicate":
            label, priority, team = "duplicate", "low", None
        elif cat == "vague":
            label, priority, team = "question", "low", None
        else:
            label, priority, team = "bug", "medium", "backend"

        correct_answers[iid] = {
            "label":            label,
            "priority":         priority,
            "team":             team,
            "needs_close":      cat == "duplicate",
            "needs_info":       cat == "vague",
            "is_security":      cat == "security",
        }
    return issues, correct_answers


# ── Task definitions ──────────────────────────────────────────────────────────

def make_tasks() -> Dict[str, Any]:
    """Called on every reset() — fresh randomised issues each episode."""

    # Easy: 5 issues — clear signals, label only
    t1_cats   = ["bug", "feature", "question", "duplicate", "bug"]
    t1_issues, t1_answers = generate_task_issues(t1_cats)

    # Medium: 6 issues — label + priority + assign team
    t2_cats   = ["bug", "security", "feature", "question", "bug", "duplicate"]
    t2_issues, t2_answers = generate_task_issues(t2_cats)

    # Hard: 8 issues — full triage including vague + security + duplicates
    t3_cats   = ["security", "bug", "vague", "duplicate", "feature",
                 "bug", "security", "vague"]
    t3_issues, t3_answers = generate_task_issues(t3_cats)

    return {
        "task_1_easy": {
            "id":              "task_1_easy",
            "name":            "Basic Issue Labelling",
            "description":     (
                "Label 5 GitHub issues correctly as: bug, feature, question, "
                "duplicate, or security. Issues have clear signals in title and body."
            ),
            "difficulty":      "easy",
            "max_steps":       10,
            "issues":          t1_issues,
            "correct_answers": t1_answers,
        },
        "task_2_medium": {
            "id":              "task_2_medium",
            "name":            "Triage with Priority and Team Assignment",
            "description":     (
                "Label, set priority, and assign 6 issues to the correct team. "
                "Security issues must be identified and escalated immediately."
            ),
            "difficulty":      "medium",
            "max_steps":       20,
            "issues":          t2_issues,
            "correct_answers": t2_answers,
        },
        "task_3_hard": {
            "id":              "task_3_hard",
            "name":            "Full Bug Triage",
            "description":     (
                "Process 8 issues with full triage: label, prioritize, assign teams, "
                "close duplicates, request info for vague issues, and escalate security "
                "vulnerabilities. Vague issues have no reproduction steps — detect them."
            ),
            "difficulty":      "hard",
            "max_steps":       35,
            "issues":          t3_issues,
            "correct_answers": t3_answers,
        },
    }


# Module-level default used at import time
TASKS = make_tasks()


# ── Graders ───────────────────────────────────────────────────────────────────

def _clamp(score: float) -> float:
    """Ensure score is strictly within (0, 1) — never exactly 0.0 or 1.0."""
    return round(min(max(score, 0.001), 0.999), 3)


def grade_task_1(
    action_history: List[Dict[str, Any]],
    correct_answers: Dict = None
) -> float:
    correct = correct_answers or TASKS["task_1_easy"]["correct_answers"]
    scored  = {}
    for action in action_history:
        iid = action.get("issue_id")
        if iid and iid in correct:
            if action.get("label") == correct[iid]["label"]:
                scored[iid] = 1.0
            elif iid not in scored:
                scored[iid] = 0.0
    raw = (
        sum(scored.get(i, 0.0) for i in correct) / len(correct)
        if correct else 0.0
    )
    return _clamp(raw)


def grade_task_2(
    action_history: List[Dict[str, Any]],
    correct_answers: Dict = None
) -> float:
    correct     = correct_answers or TASKS["task_2_medium"]["correct_answers"]
    seen        = {}   # track best per issue

    for action in action_history:
        iid = action.get("issue_id")
        if not iid or iid not in correct:
            continue
        exp = correct[iid]
        if iid not in seen:
            seen[iid] = {"label": 0.0, "priority": 0.0, "team": 0.0}
        if action.get("label") == exp["label"]:
            seen[iid]["label"] = 1.0
        if action.get("priority") == exp["priority"]:
            seen[iid]["priority"] = 1.0
        if exp["team"] and action.get("team") == exp["team"]:
            seen[iid]["team"] = 1.0

    n = len(correct)
    label_score = pri_score = team_score = 0.0
    for iid in correct:
        s = seen.get(iid, {})
        label_score += s.get("label", 0.0)
        pri_score   += s.get("priority", 0.0)
        team_score  += s.get("team", 0.0)

    raw = (
        (label_score / n) * 0.40 +
        (pri_score   / n) * 0.35 +
        (team_score  / n) * 0.25
    )
    return _clamp(raw)


def grade_task_3(
    action_history: List[Dict[str, Any]],
    correct_answers: Dict = None
) -> float:
    correct      = correct_answers or TASKS["task_3_hard"]["correct_answers"]
    security_ids = [i for i, v in correct.items() if v["is_security"]]
    duplicate_ids= [i for i, v in correct.items() if v["needs_close"]]
    vague_ids    = [i for i, v in correct.items() if v["needs_info"]]

    seen       = {}
    closed     = set()
    info_asked = set()

    for action in action_history:
        iid = action.get("issue_id")
        if not iid or iid not in correct:
            continue
        exp = correct[iid]
        if iid not in seen:
            seen[iid] = {"label": 0.0, "priority": 0.0, "team": 0.0}
        if action.get("label") == exp["label"]:
            seen[iid]["label"] = 1.0
        if action.get("priority") == exp["priority"]:
            seen[iid]["priority"] = 1.0
        if exp["team"] and action.get("team") == exp["team"]:
            seen[iid]["team"] = 1.0
        if action.get("action_type") == "close" and iid in duplicate_ids:
            closed.add(iid)
        if action.get("action_type") == "request_info" and iid in vague_ids:
            txt = action.get("request_text", "")
            if len(txt) > 20:
                info_asked.add(iid)

    n = len(correct)
    label_score = sum(seen.get(i, {}).get("label", 0.0)    for i in correct) / n
    pri_score   = sum(seen.get(i, {}).get("priority", 0.0) for i in correct) / n
    team_score  = sum(seen.get(i, {}).get("team", 0.0)     for i in correct) / n
    close_score = (len(closed)     / len(duplicate_ids) if duplicate_ids else 1.0)
    info_score  = (len(info_asked) / len(vague_ids)     if vague_ids     else 1.0)

    raw = (
        label_score * 0.25 +
        pri_score   * 0.25 +
        team_score  * 0.20 +
        close_score * 0.15 +
        info_score  * 0.15
    )
    return _clamp(raw)


GRADERS = {
    "task_1_easy":   grade_task_1,
    "task_2_medium": grade_task_2,
    "task_3_hard":   grade_task_3,
}