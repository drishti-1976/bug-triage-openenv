from app.models import Action, Reward
from typing import Dict, Any, List, Optional


PRIORITY_MAP = {"critical": 3, "high": 2, "medium": 1, "low": 0}


def compute_reward(
    action: Action,
    issue: Dict[str, Any],
    correct_answers: Dict[str, Any],
    step: int,
    max_steps: int,
    action_history: Optional[List[Dict[str, Any]]] = None,
) -> Reward:
    partial: Dict[str, float] = {}
    total   = 0.0
    iid     = issue["id"]
    exp     = correct_answers.get(iid, {})

    # ── Label reward ──────────────────────────────────────────────────────────
    if action.action_type == "label":
        if action.label == exp.get("label"):
            partial["label_correct"] = 0.50
            total += 0.50
        else:
            partial["label_correct"] = 0.0
            # partial credit: at least identifying bug vs non-bug
            is_bug_family = action.label in ("bug", "security")
            exp_bug_family = exp.get("label") in ("bug", "security")
            if is_bug_family == exp_bug_family:
                partial["label_partial"] = 0.10
                total += 0.10

    # ── Priority reward ───────────────────────────────────────────────────────
    if action.action_type == "prioritize":
        exp_p  = exp.get("priority", "medium")
        act_p  = action.priority or "medium"
        dist   = abs(PRIORITY_MAP.get(exp_p, 1) - PRIORITY_MAP.get(act_p, 1))
        reward = max(0.0, 0.30 - dist * 0.10)
        partial["priority_score"] = round(reward, 2)
        total += reward

        # Bonus: security issues marked critical
        if exp.get("is_security") and act_p == "critical":
            partial["security_critical_bonus"] = 0.10
            total += 0.10

    # ── Team assignment reward ────────────────────────────────────────────────
    if action.action_type == "assign":
        expected_team = exp.get("team")
        if expected_team is None:
            # issue shouldn't be assigned (duplicate/vague)
            partial["unnecessary_assign"] = -0.10
            total -= 0.10
        elif action.team == expected_team:
            partial["team_correct"] = 0.30
            total += 0.30
        else:
            partial["team_wrong"] = 0.0

    # ── Close reward / penalty ────────────────────────────────────────────────
    if action.action_type == "close":
        if exp.get("needs_close"):
            partial["correct_close"] = 0.30
            total += 0.30
        else:
            partial["wrong_close"] = -0.30
            total -= 0.30

    # ── Request info reward ───────────────────────────────────────────────────
    if action.action_type == "request_info":
        if exp.get("needs_info"):
            text   = action.request_text or ""
            quality = min(len(text) / 80, 1.0) * 0.25
            partial["info_request_quality"] = round(quality, 2)
            total += quality
        else:
            partial["unnecessary_info_request"] = -0.10
            total -= 0.10

    # ── Repeat action penalty ─────────────────────────────────────────────────
    if action_history:
        repeat_count = sum(
            1 for h in action_history
            if h.get("issue_id") == iid
            and h.get("action_type") == action.action_type
        )
        if repeat_count > 0:
            penalty = round(min(0.40, 0.20 * repeat_count), 2)
            partial["repeat_penalty"] = -penalty
            total -= penalty

    # ── Efficiency bonus ──────────────────────────────────────────────────────
    efficiency = (max_steps - step) / max_steps
    partial["efficiency_bonus"] = round(efficiency * 0.05, 3)
    total += efficiency * 0.05

    total  = round(max(0.0, min(1.0, total)), 3)
    reason = (
        f"Action '{action.action_type}' on issue '{iid}'. "
        + ", ".join(f"{k}={v}" for k, v in partial.items())
    )

    return Reward(value=total, reason=reason, partial_credits=partial)