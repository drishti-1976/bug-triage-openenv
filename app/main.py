from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Bug Triage OpenEnv</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e1e4e8; min-height: 100vh; }
  .header { background: #161b22; border-bottom: 1px solid #30363d; padding: 16px 32px; display: flex; align-items: center; gap: 12px; }
  .header h1 { font-size: 20px; font-weight: 600; color: #f0f6fc; }
  .badge { background: #1f6feb; color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 12px; font-weight: 500; }
  .badge2 { background: #3fb950; color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 12px; font-weight: 500; }
  .container { max-width: 1100px; margin: 0 auto; padding: 24px; }
  .tasks-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
  .task-card { background: #161b22; border: 2px solid #30363d; border-radius: 12px; padding: 20px; cursor: pointer; transition: all 0.2s; }
  .task-card:hover { border-color: #58a6ff; transform: translateY(-2px); }
  .task-card.active { border-color: #58a6ff; background: #1c2d3f; }
  .difficulty { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
  .easy { color: #3fb950; } .medium { color: #d29922; } .hard { color: #f85149; }
  .task-card h3 { font-size: 15px; font-weight: 600; color: #f0f6fc; margin-bottom: 6px; }
  .task-card p { font-size: 12px; color: #8b949e; line-height: 1.5; }
  .task-meta { display: flex; gap: 8px; margin-top: 12px; }
  .task-meta span { font-size: 11px; color: #58a6ff; background: #1f2d3d; padding: 2px 8px; border-radius: 6px; }
  .main-grid { display: grid; grid-template-columns: 1fr 360px; gap: 20px; }
  .panel { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
  .panel-title { font-size: 12px; font-weight: 600; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }
  .issue-number { color: #58a6ff; font-size: 13px; font-weight: 600; margin-right: 8px; }
  .issue-title { font-size: 17px; font-weight: 600; color: #f0f6fc; }
  .issue-body { color: #c9d1d9; font-size: 13px; line-height: 1.7; background: #0d1117; border-radius: 8px; padding: 14px; margin: 12px 0; white-space: pre-wrap; }
  .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
  .tag { font-size: 11px; padding: 3px 10px; border-radius: 12px; font-weight: 500; }
  .tag-blue { background: #1f3a5c; color: #79c0ff; }
  .tag-green { background: #1a3a2a; color: #56d364; }
  .tag-gray { background: #2a2a2a; color: #8b949e; }
  .tag-red { background: #3a1a1a; color: #ff7b72; }
  .actions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .field-box { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 12px; }
  .field-box label { font-size: 11px; color: #8b949e; display: block; margin-bottom: 6px; font-weight: 600; text-transform: uppercase; }
  .field-box select, .field-box textarea { width: 100%; background: #161b22; border: 1px solid #30363d; color: #c9d1d9; padding: 8px; border-radius: 6px; font-size: 13px; outline: none; }
  .field-box textarea { resize: none; height: 64px; }
  .btn-primary { grid-column: 1/-1; background: #1f6feb; color: #fff; border: none; padding: 13px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; width: 100%; }
  .btn-primary:hover { background: #388bfd; }
  .btn-primary:disabled { background: #30363d; color: #8b949e; cursor: not-allowed; }
  .btn-secondary { background: #21262d; border: 1px solid #30363d; color: #8b949e; padding: 10px; border-radius: 8px; font-size: 13px; cursor: pointer; width: 100%; margin-top: 8px; transition: all 0.2s; }
  .btn-secondary:hover { background: #30363d; color: #f0f6fc; }
  .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }
  .stat-box { background: #0d1117; border-radius: 8px; padding: 12px; text-align: center; }
  .stat-num { font-size: 26px; font-weight: 700; color: #f0f6fc; }
  .stat-lbl { font-size: 11px; color: #8b949e; margin-top: 2px; }
  .progress-bar { background: #21262d; border-radius: 8px; height: 8px; overflow: hidden; margin-bottom: 14px; }
  .progress-fill { background: #1f6feb; height: 100%; border-radius: 8px; transition: width 0.4s; }
  .score-box { text-align: center; padding: 16px; background: #0d1117; border-radius: 8px; margin-bottom: 14px; }
  .score-num { font-size: 44px; font-weight: 700; color: #58a6ff; line-height: 1; }
  .score-lbl { font-size: 12px; color: #8b949e; margin-top: 4px; }
  .feed { max-height: 220px; overflow-y: auto; }
  .feed-item { padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; font-size: 12px; border-left: 3px solid; }
  .feed-pos { background: #1a3a2a; border-color: #3fb950; color: #56d364; }
  .feed-neg { background: #3a1a1a; border-color: #f85149; color: #ff7b72; }
  .feed-neu { background: #1f2d3d; border-color: #58a6ff; color: #79c0ff; }
  .done-box { background: #1a3a2a; border: 1px solid #3fb950; border-radius: 10px; padding: 24px; text-align: center; }
  .done-box h3 { color: #56d364; font-size: 20px; margin-bottom: 8px; }
  .done-box p { color: #8b949e; font-size: 13px; }
  .empty-state { text-align: center; padding: 60px 20px; color: #8b949e; }
  .empty-state h3 { font-size: 18px; color: #f0f6fc; margin-bottom: 8px; }
  .spinner { display: inline-block; width: 22px; height: 22px; border: 3px solid #30363d; border-top-color: #58a6ff; border-radius: 50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="header">
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#58a6ff" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>
  <h1>Bug Triage OpenEnv</h1>
  <span class="badge">openenv</span>
  <span class="badge2">v1.0.0</span>
</div>

<div class="container">
  <div class="tasks-row">
    <div class="task-card" id="card_task_1_easy" onclick="selectTask('task_1_easy')">
      <div class="difficulty easy">Easy</div>
      <h3>Basic Issue Labelling</h3>
      <p>Label 5 GitHub issues. Clear signals in title and body.</p>
      <div class="task-meta"><span>5 issues</span><span>10 steps</span></div>
    </div>
    <div class="task-card" id="card_task_2_medium" onclick="selectTask('task_2_medium')">
      <div class="difficulty medium">Medium</div>
      <h3>Priority + Team Assignment</h3>
      <p>Label, prioritize and assign 6 issues to the right team.</p>
      <div class="task-meta"><span>6 issues</span><span>20 steps</span></div>
    </div>
    <div class="task-card" id="card_task_3_hard" onclick="selectTask('task_3_hard')">
      <div class="difficulty hard">Hard</div>
      <h3>Full Bug Triage</h3>
      <p>Full triage: label, prioritize, assign, close duplicates, escalate security.</p>
      <div class="task-meta"><span>8 issues</span><span>35 steps</span></div>
    </div>
  </div>

  <div id="emptyState" class="empty-state">
    <h3>Select a task above to begin</h3>
    <p>Choose Easy, Medium, or Hard to start triaging GitHub issues</p>
  </div>

  <div id="mainGrid" class="main-grid" style="display:none">
    <div>
      <div class="panel">
        <div class="panel-title">Current Issue</div>
        <div id="issueContent"><div style="text-align:center;padding:30px"><div class="spinner"></div></div></div>
      </div>
    </div>
    <div>
      <div class="panel">
        <div class="panel-title">Episode Stats</div>
        <div class="stats-grid">
          <div class="stat-box"><div class="stat-num" id="statStep">0</div><div class="stat-lbl">Steps</div></div>
          <div class="stat-box"><div class="stat-num" id="statLeft">—</div><div class="stat-lbl">Remaining</div></div>
          <div class="stat-box"><div class="stat-num" id="statBudget">—</div><div class="stat-lbl">Budget</div></div>
          <div class="stat-box"><div class="stat-num" id="statReward">0.00</div><div class="stat-lbl">Reward</div></div>
        </div>
        <div class="progress-bar"><div class="progress-fill" id="progFill" style="width:0%"></div></div>
        <div id="scoreBox" class="score-box" style="display:none">
          <div class="score-num" id="scoreNum">—</div>
          <div class="score-lbl">Final grader score</div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title">Reward Feed</div>
        <div class="feed" id="feed"><div style="color:#8b949e;font-size:12px;text-align:center;padding:16px">Actions will appear here</div></div>
      </div>
    </div>
  </div>
</div>

<script>
let task = null, obs = null, done = false, steps = 0, totalR = 0;

function selectTask(id) {
  task = id;
  ['task_1_easy','task_2_medium','task_3_hard'].forEach(t => {
    document.getElementById('card_'+t).classList.toggle('active', t===id);
  });
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('mainGrid').style.display = 'grid';
  startEpisode();
}

async function startEpisode() {
  done=false; steps=0; totalR=0;
  document.getElementById('feed').innerHTML = '<div style="color:#8b949e;font-size:12px;text-align:center;padding:16px">Actions will appear here</div>';
  document.getElementById('scoreBox').style.display = 'none';
  setStats(0,'—','—',0); setProgress(0,1);
  setIssue('<div style="text-align:center;padding:30px"><div class="spinner"></div><p style="color:#8b949e;margin-top:12px">Resetting...</p></div>');
  const r = await fetch('/reset?task_id='+task, {method:'POST'});
  obs = await r.json();
  renderIssue();
}

function renderIssue() {
  const issue = obs?.current_issue;
  const budget = obs?.step_budget_remaining ?? '—';
  const processed = obs?.issues_processed ?? 0;
  const total = obs?.inbox_size ?? 0;
  setStats(steps, total-processed, budget, totalR);
  setProgress(processed, total);
  if (done || !issue) { showDone(); return; }

  setIssue(`
    <div style="margin-bottom:12px">
      <span class="issue-number">#${issue.number}</span>
      <span class="issue-title">${esc(issue.title)}</span>
    </div>
    <div class="tags">
      <span class="tag tag-blue">${esc(issue.repository)}</span>
      <span class="tag ${repClass(issue.author_reputation)}">${esc(issue.author_reputation)}</span>
      ${issue.has_stacktrace?'<span class="tag tag-green">stacktrace</span>':'<span class="tag tag-gray">no stacktrace</span>'}
      ${issue.has_reproduction_steps?'<span class="tag tag-green">repro steps</span>':'<span class="tag tag-gray">no repro steps</span>'}
      <span class="tag tag-gray">${esc(issue.author)}</span>
    </div>
    <div class="issue-body">${esc(issue.body)}</div>
    <div class="actions-grid">
      <div class="field-box">
        <label>Label</label>
        <select id="selLabel">
          <option value="">— choose —</option>
          <option>bug</option><option>feature</option>
          <option>question</option><option>duplicate</option><option>security</option>
        </select>
      </div>
      <div class="field-box">
        <label>Priority</label>
        <select id="selPri">
          <option value="">— choose —</option>
          <option>critical</option><option>high</option><option>medium</option><option>low</option>
        </select>
      </div>
      <div class="field-box">
        <label>Assign team</label>
        <select id="selTeam">
          <option value="">— none —</option>
          <option>backend</option><option>frontend</option>
          <option>devops</option><option>security</option><option>docs</option>
        </select>
      </div>
      <div class="field-box">
        <label>Close reason</label>
        <select id="selClose">
          <option value="">— none —</option>
          <option>duplicate</option><option>invalid</option><option>wontfix</option>
        </select>
      </div>
      <div class="field-box" style="grid-column:1/-1">
        <label>Request info (optional)</label>
        <textarea id="txtReq" placeholder="Ask reporter for reproduction steps, env details..."></textarea>
      </div>
      <button class="btn-primary" id="submitBtn" onclick="submitAction('${issue.id}')">Submit Triage Action</button>
    </div>
    <button class="btn-secondary" onclick="skipAction('${issue.id}')">Skip this issue</button>
  `);
}

async function submitAction(issueId) {
  const label    = document.getElementById('selLabel')?.value;
  const priority = document.getElementById('selPri')?.value;
  const team     = document.getElementById('selTeam')?.value;
  const closeR   = document.getElementById('selClose')?.value;
  const reqText  = document.getElementById('txtReq')?.value?.trim();

  let actionType = 'label';
  if (closeR)   actionType = 'close';
  else if (reqText) actionType = 'request_info';
  else if (label)   actionType = 'label';
  else if (priority) actionType = 'prioritize';
  else if (team)    actionType = 'assign';

  const action = {action_type: actionType, issue_id: issueId};
  if (label)    action.label        = label;
  if (priority) action.priority     = priority;
  if (team)     action.team         = team;
  if (closeR)   action.close_reason = closeR;
  if (reqText)  action.request_text = reqText;

  document.getElementById('submitBtn').disabled = true;
  await doStep(action);
}

async function skipAction(issueId) {
  await doStep({action_type:'skip', issue_id: issueId});
}

async function doStep(action) {
  const r = await fetch('/step', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(action)
  });
  const result = await r.json();
  obs   = result.observation;
  done  = result.done;
  steps++;
  totalR += result.reward?.value || 0;
  addFeed(result.reward, action);
  if (done) { await loadGrade(); showDone(); }
  else renderIssue();
}

async function loadGrade() {
  const r = await fetch('/grader');
  const g = await r.json();
  document.getElementById('scoreNum').textContent = (g.grader_score||0).toFixed(3);
  document.getElementById('scoreBox').style.display = 'block';
}

function showDone() {
  const total = obs?.inbox_size || 0;
  setIssue(`
    <div class="done-box">
      <h3>Episode Complete</h3>
      <p>Processed ${total} issues in ${steps} steps</p>
      <p style="margin-top:8px">Total reward: ${totalR.toFixed(3)}</p>
    </div>
    <button class="btn-secondary" style="margin-top:12px" onclick="startEpisode()">Run Again</button>
    <button class="btn-secondary" style="margin-top:8px;color:#58a6ff" onclick="backToTasks()">Try Another Task</button>
  `);
  loadGrade();
}

function backToTasks() {
  document.getElementById('mainGrid').style.display = 'none';
  document.getElementById('emptyState').style.display = 'block';
  document.querySelectorAll('.task-card').forEach(c => c.classList.remove('active'));
}

function addFeed(reward, action) {
  const feed = document.getElementById('feed');
  if (feed.querySelector('[data-ph]')) feed.innerHTML = '';
  const val = reward?.value || 0;
  const cls = val > 0.1 ? 'feed-pos' : val < 0 ? 'feed-neg' : 'feed-neu';
  const sign = val >= 0 ? '+' : '';
  const d = document.createElement('div');
  d.className = 'feed-item ' + cls;
  d.innerHTML = `<strong>${sign}${val.toFixed(3)}</strong> — ${action.action_type}${action.label?': '+action.label:''}${action.priority?' / '+action.priority:''}`;
  feed.insertBefore(d, feed.firstChild);
}

function setIssue(html) { document.getElementById('issueContent').innerHTML = html; }
function setStats(s,l,b,r) {
  document.getElementById('statStep').textContent   = s;
  document.getElementById('statLeft').textContent   = l;
  document.getElementById('statBudget').textContent = b;
  document.getElementById('statReward').textContent = (r||0).toFixed(2);
}
function setProgress(done, total) {
  const pct = total > 0 ? Math.round((done/total)*100) : 0;
  document.getElementById('progFill').style.width = pct+'%';
}
function repClass(r) { return r==='trusted'?'tag-green':r==='new'?'tag-blue':'tag-gray'; }
function esc(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
</script>
</body>
</html>"""


@app.get("/")
def root():
    return HTMLResponse(content=HTML)

@app.get("/api")
def api_root():
    return {"status": "ok", "env": "bug-triage-openenv", "version": "1.0.0"}

@app.get("/web")
def web():
    return HTMLResponse(content=HTML)

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
            "id":          tid,
            "name":        task["name"],
            "description": task["description"],
            "difficulty":  task["difficulty"],
            "max_steps":   task["max_steps"],
            "num_issues":  len(task["issues"]),
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