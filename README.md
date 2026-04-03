---
title: Bug Triage Env
emoji: 🏢
colorFrom: pink
colorTo: indigo
sdk: docker
pinned: false
license: mit
tags:
  - openenv
  - agent-environment

---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# Bug Triage OpenEnv

A real-world OpenEnv environment where AI agents triage GitHub issues —
labelling, prioritising, assigning to teams, closing duplicates, and
escalating security vulnerabilities.

## Motivation
Every engineering team spends hours triaging GitHub issues. This environment
benchmarks AI agents on that exact workflow, with dynamic issue generation
so agents cannot memorise answers.

## Observation Space
| Field | Type | Description |
|-------|------|-------------|
| current_issue | GitHubIssue or null | The issue to process |
| inbox_size | int | Total issues in queue |
| issues_processed | int | How many completed |
| task_description | str | Current task goal |
| available_actions | list | Allowed actions |
| step_budget_remaining | int | Steps left |
| reporter_history | dict | Author reputation map |

## Action Space
| Field | Type | Description |
|-------|------|-------------|
| action_type | str | label / prioritize / assign / close / request_info / skip |
| label | str | bug / feature / question / duplicate / security |
| priority | str | critical / high / medium / low |
| team | str | backend / frontend / devops / security / docs |
| close_reason | str | duplicate / invalid / wontfix |
| request_text | str | Message to reporter |
| issue_id | str | Issue being acted on |

## Tasks
| Task | Difficulty | Description | Max Steps |
|------|-----------|-------------|-----------|
| task_1_easy | Easy | Label 5 issues with clear signals | 10 |
| task_2_medium | Medium | Label + prioritize + assign team for 6 issues | 20 |
| task_3_hard | Hard | Full triage: 8 issues including vague + security + duplicates | 35 |

## Baseline Scores (GPT-4o-mini)
| Task | Score |
|------|-------|
| task_1_easy | 0.74 |
| task_2_medium | 0.61 |
| task_3_hard | 0.43 |

## Setup

## Hardware Requirements
Runs on 2 vCPU / 8GB RAM (Hugging Face CPU Basic tier).
No GPU required. Inference script completes in under 20 minutes.

## Environment Variables
| Variable | Description |
|----------|-------------|
| API_BASE_URL | LLM API endpoint (default: https://router.huggingface.co/v1) |
| MODEL_NAME | Model identifier (default: meta-llama/Llama-3.1-8B-Instruct) |
| HF_TOKEN | Your Hugging Face API key |
| ENV_BASE_URL | Environment server URL (default: http://localhost:7860) |

### Local
```bash
pip install -r requirements.txt
uvicorn app.main:app --port 7860
```

### Docker
```bash
docker build -t bug-triage-env .
docker run -p 7860:7860 bug-triage-env
```

### Run tests
```bash
python test_env.py
```

### Baseline
```bash
export OPENAI_API_KEY=your_key
python baseline.py
```

## API
- `POST /reset?task_id=task_1_easy` — Start new episode
- `POST /step` — Take an action
- `GET /state` — Current environment state
- `GET /tasks` — List all tasks and action schema
- `GET /grader` — Get grader score for current episode
- `GET /baseline` — Run inline baseline agent
- `GET /validate` — OpenEnv spec compliance check
- `GET /health` — Health check