from app.environment import BugTriageEnv
from app.models import Action


def test_reset():
    env = BugTriageEnv()
    obs = env.reset("task_1_easy")
    assert obs.current_issue is not None,    "Issue should exist after reset"
    assert obs.inbox_size == 5,              "Task 1 has 5 issues"
    assert obs.issues_processed == 0,        "Nothing processed at start"
    assert obs.step_budget_remaining == 10,  "Full budget at start"
    print("✓ reset() works")


def test_step():
    env = BugTriageEnv()
    obs = env.reset("task_1_easy")
    iid = obs.current_issue.id

    result = env.step(Action(action_type="label", label="bug", issue_id=iid))
    assert 0.0 <= result.reward.value <= 1.0, "Reward must be 0.0–1.0"
    assert result.observation is not None,    "Observation must exist"
    assert result.done is False,              "Not done after 1 step"
    print("✓ step() works")


def test_state():
    env = BugTriageEnv()
    env.reset("task_1_easy")
    iid = env.issues[0]["id"]

    env.step(Action(action_type="label", label="bug", issue_id=iid))
    state = env.state()
    assert state.episode_step == 1,       "Should be step 1"
    assert state.issues_processed == 1,   "One issue processed"
    assert len(state.action_history) == 1,"One action recorded"
    print("✓ state() works")


def test_full_episode():
    env  = BugTriageEnv()
    obs  = env.reset("task_1_easy")
    done = False

    while not done:
        iid = obs.current_issue.id if obs.current_issue else None
        if not iid:
            break
        result = env.step(Action(action_type="label", label="bug", issue_id=iid))
        obs    = result.observation
        done   = result.done

    assert env.done is True, "Episode should be done"
    score = env.grade()
    assert 0.0 <= score <= 1.0, f"Grade must be 0.0–1.0, got {score}"
    print(f"✓ full episode works — grade: {score:.3f}")


def test_all_tasks():
    for task_id in ["task_1_easy", "task_2_medium", "task_3_hard"]:
        env = BugTriageEnv()
        obs = env.reset(task_id)
        assert obs.current_issue is not None,  f"{task_id} should have issues"
        assert obs.current_task_id == task_id, f"task_id mismatch"
        print(f"✓ {task_id} resets correctly")


def test_repeat_penalty():
    env = BugTriageEnv()
    obs = env.reset("task_1_easy")
    iid = obs.current_issue.id

    # prioritize is non-terminal — stays on same issue
    r1 = env.step(Action(action_type="prioritize", priority="high", issue_id=iid))
    r2 = env.step(Action(action_type="prioritize", priority="high", issue_id=iid))
    assert r2.reward.value <= r1.reward.value, "Repeat action should be penalised"
    print("✓ repeat penalty works")


def test_security_bonus():
    """Security issues marked critical should get bonus reward."""
    from app.tasks import generate_issue
    from app.rewards import compute_reward

    issue = generate_issue("security", "sec1", 9999)
    correct = {
        "sec1": {
            "label": "security", "priority": "critical",
            "team": "security", "needs_close": False,
            "needs_info": False, "is_security": True,
        }
    }
    action = Action(action_type="prioritize", priority="critical", issue_id="sec1")
    reward = compute_reward(action, issue, correct, step=1, max_steps=20)
    assert reward.partial_credits.get("security_critical_bonus", 0) > 0, \
        "Security critical bonus should fire"
    print("✓ security bonus works")


def test_reporter_history():
    env = BugTriageEnv()
    obs = env.reset("task_2_medium")
    iid = obs.current_issue.id

    env.step(Action(action_type="label", label="bug", issue_id=iid))
    state = env.state()
    assert len(env.reporter_history) > 0, "Reporter history should be populated"
    print("✓ reporter history works")


if __name__ == "__main__":
    print("\nRunning tests...\n")
    test_reset()
    test_step()
    test_state()
    test_full_episode()
    test_all_tasks()
    test_repeat_penalty()
    test_security_bonus()
    test_reporter_history()
    print("\n✅ All tests passed")