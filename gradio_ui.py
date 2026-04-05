import gradio as gr
import httpx
import json

BASE = "http://localhost:7860"


def do_reset(task_id):
    try:
        r = httpx.post(f"{BASE}/reset", params={"task_id": task_id}, timeout=30)
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return f"Error: {e}"


def do_step(action_json):
    try:
        action = json.loads(action_json)
        r = httpx.post(f"{BASE}/step", json=action, timeout=30)
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return f"Error: {e}"


def do_state():
    try:
        r = httpx.get(f"{BASE}/state", timeout=30)
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return f"Error: {e}"


def do_grader():
    try:
        r = httpx.get(f"{BASE}/grader", timeout=30)
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return f"Error: {e}"


def do_baseline():
    try:
        r = httpx.get(f"{BASE}/baseline", timeout=60)
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return f"Error: {e}"


CONNECT_CODE = '''from openai import OpenAI
import httpx

# Connect directly to the running server
BASE_URL = "https://drishti1976-bug-triage-env.hf.space"

# Reset environment
obs = httpx.post(f"{BASE_URL}/reset", params={"task_id": "task_1_easy"}).json()

# Take a step
result = httpx.post(f"{BASE_URL}/step", json={
    "action_type": "label",
    "label": "bug",
    "issue_id": obs["current_issue"]["id"]
}).json()

print(result["reward"])'''

STEP_EXAMPLE = '''{
  "action_type": "label",
  "label": "bug",
  "issue_id": "i1"
}'''


def build_ui():
    with gr.Blocks(
        title="Bug Triage OpenEnv",
        theme=gr.themes.Base(
            primary_hue="green",
            neutral_hue="slate",
        ),
        css="""
        .header-text { font-size: 24px !important; font-weight: 700 !important; }
        .tab-selected { border-bottom: 2px solid #22c55e !important; }
        .code-block { font-family: monospace; font-size: 12px; }
        footer { display: none !important; }
        """
    ) as demo:

        gr.Markdown("# OpenEnv Agentic Environment: bug_triage_env")

        with gr.Tabs():

            # ── Playground Tab ────────────────────────────────────────────
            with gr.Tab("Playground"):
                gr.Markdown("### Click Reset to start a new episode.")

                with gr.Row():

                    # Left column — connect info
                    with gr.Column(scale=1):
                        gr.Markdown("### Quick Start")
                        gr.Markdown("**Connect to this environment**")
                        gr.Markdown("Connect directly to a running server:")
                        gr.Code(
                            value=CONNECT_CODE,
                            language="python",
                            label="Python client",
                        )
                        gr.Markdown("**Available tasks:**")
                        gr.Markdown(
                            "- `task_1_easy` — Label 5 issues (Easy)\n"
                            "- `task_2_medium` — Label + Priority + Team (Medium)\n"
                            "- `task_3_hard` — Full triage (Hard)"
                        )
                        gr.Markdown("**Action types:**")
                        gr.Markdown(
                            "`label` · `prioritize` · `assign` · `close` · `request_info` · `skip`"
                        )

                    # Right column — interactive playground
                    with gr.Column(scale=2):
                        gr.Markdown("### Playground")

                        task_selector = gr.Dropdown(
                            choices=["task_1_easy", "task_2_medium", "task_3_hard"],
                            value="task_1_easy",
                            label="Select Task",
                        )

                        action_input = gr.Textbox(
                            label="Action JSON",
                            value=STEP_EXAMPLE,
                            lines=6,
                            placeholder='{"action_type": "label", "label": "bug", "issue_id": "i1"}',
                        )

                        with gr.Row():
                            btn_step  = gr.Button("Step",      variant="primary")
                            btn_reset = gr.Button("Reset",     variant="secondary")
                            btn_state = gr.Button("Get state", variant="secondary")

                        status_box = gr.Textbox(
                            label="Status",
                            lines=1,
                            value="Click Reset to start",
                            interactive=False,
                        )

                        output_box = gr.Code(
                            label="Raw JSON response",
                            language="json",
                            lines=18,
                        )

                        # Wire buttons
                        btn_reset.click(
                            fn=lambda t: (do_reset(t), "Episode reset — ready to step"),
                            inputs=[task_selector],
                            outputs=[output_box, status_box],
                        )
                        btn_step.click(
                            fn=lambda a: (do_step(a), "Step executed"),
                            inputs=[action_input],
                            outputs=[output_box, status_box],
                        )
                        btn_state.click(
                            fn=lambda: (do_state(), "State fetched"),
                            outputs=[output_box, status_box],
                        )

            # ── Grader Tab ────────────────────────────────────────────────
            with gr.Tab("Grader"):
                gr.Markdown("### Get grader score for current episode")
                btn_grade = gr.Button("Get Grader Score", variant="primary")
                grade_out = gr.Code(label="Grader response", language="json", lines=10)
                btn_grade.click(fn=lambda: do_grader(), outputs=[grade_out])

            # ── Baseline Tab ──────────────────────────────────────────────
            with gr.Tab("Baseline"):
                gr.Markdown("### Run the rule-based baseline agent on all 3 tasks")
                btn_base = gr.Button("Run Baseline", variant="primary")
                base_out = gr.Code(label="Baseline scores", language="json", lines=15)
                btn_base.click(fn=lambda: do_baseline(), outputs=[base_out])

            # ── README Tab ────────────────────────────────────────────────
            with gr.Tab("README"):
                gr.Markdown("""
## Bug Triage OpenEnv

A real-world OpenEnv environment where AI agents triage GitHub issues —
labelling, prioritising, assigning to teams, closing duplicates, and
escalating security vulnerabilities.

## Observation Space
| Field | Type | Description |
|-------|------|-------------|
| current_issue | GitHubIssue | The issue to process |
| inbox_size | int | Total issues in queue |
| issues_processed | int | How many completed |
| step_budget_remaining | int | Steps left |
| reporter_history | dict | Author reputation map |

## Action Space
| Field | Type | Values |
|-------|------|--------|
| action_type | str | label / prioritize / assign / close / request_info / skip |
| label | str | bug / feature / question / duplicate / security |
| priority | str | critical / high / medium / low |
| team | str | backend / frontend / devops / security / docs |

## Tasks
| Task | Difficulty | Issues | Max Steps |
|------|-----------|--------|-----------|
| task_1_easy | Easy | 5 | 10 |
| task_2_medium | Medium | 6 | 20 |
| task_3_hard | Hard | 8 | 35 |

## Baseline Scores
| Task | Score |
|------|-------|
| task_1_easy | 0.74 |
| task_2_medium | 0.61 |
| task_3_hard | 0.43 |
                """)

    return demo