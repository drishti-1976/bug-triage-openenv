from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from app.environment import BugTriageEnv
from app.models import Action
from app.tasks import TASKS, GRADERS, make_tasks

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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#060910;color:#e2e8f0;min-height:100vh;overflow-x:hidden}
.bg-grid{position:fixed;inset:0;background-image:linear-gradient(rgba(99,102,241,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(99,102,241,.03) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0}
.wrap{position:relative;z-index:1}
.header{padding:20px 32px;display:flex;align-items:center;gap:14px;border-bottom:1px solid rgba(255,255,255,.06);background:rgba(6,9,16,.8);backdrop-filter:blur(20px);position:sticky;top:0;z-index:100}
.logo{width:36px;height:36px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:10px;display:flex;align-items:center;justify-content:center}
.logo svg{width:20px;height:20px}
.header-title{font-size:18px;font-weight:700;background:linear-gradient(90deg,#e2e8f0,#94a3b8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.pill{font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;letter-spacing:.5px}
.pill-purple{background:rgba(99,102,241,.15);color:#818cf8;border:1px solid rgba(99,102,241,.3)}
.pill-green{background:rgba(16,185,129,.1);color:#34d399;border:1px solid rgba(16,185,129,.25)}
.pill-live{background:rgba(16,185,129,.1);color:#34d399;border:1px solid rgba(16,185,129,.25);display:flex;align-items:center;gap:5px}
.dot{width:6px;height:6px;border-radius:50%;background:#10b981;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
.container{max-width:1200px;margin:0 auto;padding:28px 24px}
.hero{text-align:center;padding:48px 20px 36px;margin-bottom:8px}
.hero h2{font-size:32px;font-weight:700;background:linear-gradient(135deg,#e2e8f0 0%,#94a3b8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:12px}
.hero p{font-size:15px;color:#64748b;max-width:520px;margin:0 auto;line-height:1.7}
.tasks-row{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px}
.task-card{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:22px;cursor:pointer;transition:all .25s;position:relative;overflow:hidden}
.task-card::before{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(99,102,241,.05),transparent);opacity:0;transition:opacity .25s}
.task-card:hover{border-color:rgba(99,102,241,.4);transform:translateY(-3px);background:rgba(99,102,241,.05)}
.task-card:hover::before{opacity:1}
.task-card.active{border-color:#6366f1;background:rgba(99,102,241,.1);box-shadow:0 0 0 1px rgba(99,102,241,.3),0 8px 32px rgba(99,102,241,.15)}
.task-card.active::before{opacity:1}
.diff-badge{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}
.diff-easy{color:#34d399}.diff-medium{color:#f59e0b}.diff-hard{color:#f87171}
.diff-dot{width:7px;height:7px;border-radius:50%}
.dot-easy{background:#10b981}.dot-medium{background:#f59e0b}.dot-hard{background:#ef4444}
.task-card h3{font-size:15px;font-weight:600;color:#e2e8f0;margin-bottom:8px;line-height:1.4}
.task-card p{font-size:12px;color:#64748b;line-height:1.6;margin-bottom:14px}
.task-pills{display:flex;gap:6px;flex-wrap:wrap}
.task-pill{font-size:11px;color:#6366f1;background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.2);padding:2px 8px;border-radius:6px;font-weight:500}
.main-grid{display:grid;grid-template-columns:1fr 340px;gap:20px}
.panel{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:20px}
.panel-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
.panel-title{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#475569}
.issue-meta-bar{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.tag{font-size:11px;font-weight:500;padding:3px 10px;border-radius:6px}
.tag-repo{background:rgba(99,102,241,.1);color:#818cf8;border:1px solid rgba(99,102,241,.2)}
.tag-trust{background:rgba(16,185,129,.1);color:#34d399;border:1px solid rgba(16,185,129,.2)}
.tag-new{background:rgba(59,130,246,.1);color:#60a5fa;border:1px solid rgba(59,130,246,.2)}
.tag-unk{background:rgba(100,116,139,.1);color:#94a3b8;border:1px solid rgba(100,116,139,.2)}
.tag-yes{background:rgba(16,185,129,.08);color:#34d399;border:1px solid rgba(16,185,129,.15)}
.tag-no{background:rgba(100,116,139,.08);color:#64748b;border:1px solid rgba(100,116,139,.15)}
.issue-num{font-size:13px;font-weight:700;color:#6366f1;font-family:'JetBrains Mono',monospace;margin-right:8px}
.issue-title{font-size:18px;font-weight:600;color:#e2e8f0;line-height:1.4;margin-bottom:12px}
.issue-body{font-size:13px;color:#94a3b8;line-height:1.8;background:rgba(0,0,0,.25);border-radius:10px;padding:14px;margin-bottom:16px;font-family:'JetBrains Mono',monospace;white-space:pre-wrap;border:1px solid rgba(255,255,255,.05)}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.field{background:rgba(0,0,0,.2);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:12px}
.field label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#475569;display:block;margin-bottom:7px}
.field select,.field textarea{width:100%;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);color:#e2e8f0;padding:8px 10px;border-radius:7px;font-size:13px;outline:none;transition:border-color .2s;font-family:'Inter',sans-serif}
.field select:focus,.field textarea:focus{border-color:rgba(99,102,241,.5)}
.field textarea{resize:none;height:62px}
.field-full{grid-column:1/-1}
.btn-submit{width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;padding:14px;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;transition:all .2s;letter-spacing:.3px;margin-bottom:8px;font-family:'Inter',sans-serif}
.btn-submit:hover{opacity:.9;transform:translateY(-1px)}
.btn-submit:disabled{opacity:.4;cursor:not-allowed;transform:none}
.btn-skip{width:100%;background:transparent;border:1px solid rgba(255,255,255,.1);color:#64748b;padding:10px;border-radius:10px;font-size:13px;cursor:pointer;transition:all .2s;font-family:'Inter',sans-serif}
.btn-skip:hover{border-color:rgba(255,255,255,.2);color:#94a3b8}
.stats-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px}
.stat{background:rgba(0,0,0,.2);border-radius:10px;padding:14px;text-align:center;border:1px solid rgba(255,255,255,.05)}
.stat-n{font-size:28px;font-weight:700;color:#e2e8f0;line-height:1;font-variant-numeric:tabular-nums}
.stat-l{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#475569;margin-top:5px}
.prog-wrap{margin-bottom:16px}
.prog-label{display:flex;justify-content:space-between;margin-bottom:6px}
.prog-label span{font-size:11px;color:#475569;font-weight:500}
.prog-track{background:rgba(255,255,255,.06);border-radius:8px;height:6px;overflow:hidden}
.prog-fill{height:100%;border-radius:8px;background:linear-gradient(90deg,#6366f1,#8b5cf6);transition:width .5s cubic-bezier(.4,0,.2,1)}
.score-panel{background:linear-gradient(135deg,rgba(99,102,241,.1),rgba(139,92,246,.1));border:1px solid rgba(99,102,241,.25);border-radius:12px;padding:18px;text-align:center;margin-bottom:16px}
.score-n{font-size:46px;font-weight:700;background:linear-gradient(135deg,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1;font-variant-numeric:tabular-nums}
.score-l{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;color:#6366f1;margin-top:6px}
.feed{max-height:200px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:rgba(99,102,241,.3) transparent}
.feed-item{padding:8px 12px;border-radius:8px;margin-bottom:6px;font-size:12px;display:flex;align-items:center;gap:8px;font-family:'JetBrains Mono',monospace}
.feed-pos{background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);color:#34d399}
.feed-neg{background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.15);color:#f87171}
.feed-neu{background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.15);color:#818cf8}
.feed-val{font-weight:700;min-width:52px}
.feed-txt{color:#94a3b8;font-size:11px}
.done-box{background:linear-gradient(135deg,rgba(16,185,129,.08),rgba(16,185,129,.04));border:1px solid rgba(16,185,129,.25);border-radius:14px;padding:28px;text-align:center}
.done-box h3{font-size:22px;font-weight:700;color:#34d399;margin-bottom:8px}
.done-box p{font-size:13px;color:#64748b;margin-bottom:4px}
.btn-again{display:block;width:100%;margin-top:16px;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);color:#34d399;padding:11px;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;font-family:'Inter',sans-serif}
.btn-again:hover{background:rgba(16,185,129,.2)}
.btn-back{display:block;width:100%;margin-top:8px;background:transparent;border:1px solid rgba(255,255,255,.1);color:#6366f1;padding:11px;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;font-family:'Inter',sans-serif}
.btn-back:hover{border-color:rgba(99,102,241,.4);background:rgba(99,102,241,.05)}
.empty{text-align:center;padding:60px 20px}
.empty-icon{width:64px;height:64px;background:rgba(99,102,241,.1);border-radius:16px;margin:0 auto 20px;display:flex;align-items:center;justify-content:center}
.empty h3{font-size:20px;font-weight:600;color:#e2e8f0;margin-bottom:8px}
.empty p{font-size:14px;color:#64748b}
.spin{display:inline-block;width:20px;height:20px;border:2px solid rgba(99,102,241,.2);border-top-color:#6366f1;border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.fade-in{animation:fadein .3s ease}
@keyframes fadein{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.action-type-badge{font-size:11px;font-weight:600;padding:2px 8px;border-radius:6px;font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.5px}
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="wrap">
<div class="header">
  <div class="logo"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg></div>
  <span class="header-title">Bug Triage OpenEnv</span>
  <span class="pill pill-purple">openenv</span>
  <span class="pill pill-green">v1.0.0</span>
  <span class="pill pill-live" style="margin-left:auto"><span class="dot"></span>Live</span>
</div>

<div class="container">
  <div class="hero">
    <h2>GitHub Issue Triage Environment</h2>
    <p>Train and evaluate AI agents on real-world engineering workflows. Label, prioritize, assign, and escalate issues across three difficulty levels.</p>
  </div>

  <div class="tasks-row" id="taskRow">
    <div class="task-card" id="card_task_1_easy" onclick="selectTask('task_1_easy')">
      <div class="diff-badge diff-easy"><span class="diff-dot dot-easy"></span>Easy</div>
      <h3>Basic Issue Labelling</h3>
      <p>Classify 5 GitHub issues. Signals are clear in title and body — perfect for warming up.</p>
      <div class="task-pills"><span class="task-pill">5 issues</span><span class="task-pill">10 steps</span><span class="task-pill">label only</span></div>
    </div>
    <div class="task-card" id="card_task_2_medium" onclick="selectTask('task_2_medium')">
      <div class="diff-badge diff-medium"><span class="diff-dot dot-medium"></span>Medium</div>
      <h3>Priority + Team Assignment</h3>
      <p>Label, set priority and assign 6 issues to the right engineering team. Security issues must be escalated.</p>
      <div class="task-pills"><span class="task-pill">6 issues</span><span class="task-pill">20 steps</span><span class="task-pill">multi-action</span></div>
    </div>
    <div class="task-card" id="card_task_3_hard" onclick="selectTask('task_3_hard')">
      <div class="diff-badge diff-hard"><span class="diff-dot dot-hard"></span>Hard</div>
      <h3>Full Bug Triage</h3>
      <p>Complete triage: label, prioritize, assign teams, close duplicates, request info for vague issues, escalate security vulnerabilities.</p>
      <div class="task-pills"><span class="task-pill">8 issues</span><span class="task-pill">35 steps</span><span class="task-pill">all actions</span></div>
    </div>
  </div>

  <div id="emptyState" class="empty">
    <div class="empty-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg></div>
    <h3>Select a task to begin</h3>
    <p>Choose Easy, Medium, or Hard above to start an episode</p>
  </div>

  <div id="mainGrid" class="main-grid" style="display:none">
    <div>
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Current Issue</span>
          <div id="issueIndicator"></div>
        </div>
        <div id="issueContent"><div style="text-align:center;padding:40px"><div class="spin"></div></div></div>
      </div>
    </div>

    <div>
      <div class="panel" style="margin-bottom:16px">
        <div class="panel-header"><span class="panel-title">Episode Stats</span></div>
        <div class="stats-grid">
          <div class="stat"><div class="stat-n" id="sStep">0</div><div class="stat-l">Steps</div></div>
          <div class="stat"><div class="stat-n" id="sLeft">—</div><div class="stat-l">Remaining</div></div>
          <div class="stat"><div class="stat-n" id="sBudget">—</div><div class="stat-l">Budget</div></div>
          <div class="stat"><div class="stat-n" id="sReward">0.00</div><div class="stat-l">Reward</div></div>
        </div>
        <div class="prog-wrap">
          <div class="prog-label"><span>Progress</span><span id="progPct">0%</span></div>
          <div class="prog-track"><div class="prog-fill" id="progFill" style="width:0%"></div></div>
        </div>
        <div id="scoreBox" class="score-panel" style="display:none">
          <div class="score-n" id="scoreNum">—</div>
          <div class="score-l">Grader Score</div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header"><span class="panel-title">Reward Feed</span></div>
        <div class="feed" id="feed">
          <div style="color:#475569;font-size:12px;text-align:center;padding:20px">Actions appear here</div>
        </div>
      </div>
    </div>
  </div>
</div>
</div>

<script>
let task=null,obs=null,done=false,steps=0,totalR=0;

function selectTask(id){
  task=id;
  ['task_1_easy','task_2_medium','task_3_hard'].forEach(t=>{
    document.getElementById('card_'+t).classList.toggle('active',t===id)
  });
  document.getElementById('emptyState').style.display='none';
  document.getElementById('mainGrid').style.display='grid';
  startEpisode();
}

async function startEpisode(){
  done=false;steps=0;totalR=0;
  document.getElementById('feed').innerHTML='<div style="color:#475569;font-size:12px;text-align:center;padding:20px">Actions appear here</div>';
  document.getElementById('scoreBox').style.display='none';
  setStats(0,'—','—',0);setProgress(0,1);
  setIssue('<div style="text-align:center;padding:40px"><div class="spin"></div><p style="color:#475569;margin-top:14px;font-size:13px">Loading episode...</p></div>');
  const r=await fetch('/reset?task_id='+task,{method:'POST'});
  obs=await r.json();
  renderIssue();
}

function renderIssue(){
  const issue=obs?.current_issue;
  const budget=obs?.step_budget_remaining??'—';
  const processed=obs?.issues_processed??0;
  const total=obs?.inbox_size??0;
  setStats(steps,total-processed,budget,totalR);
  setProgress(processed,total);
  if(done||!issue){showDone();return}
  const repCls=issue.author_reputation==='trusted'?'tag-trust':issue.author_reputation==='new'?'tag-new':'tag-unk';
  setIssue(`
    <div class="fade-in">
      <div style="margin-bottom:10px">
        <span class="issue-num">#${issue.number}</span>
        <span class="issue-title">${esc(issue.title)}</span>
      </div>
      <div class="issue-meta-bar">
        <span class="tag tag-repo">${esc(issue.repository)}</span>
        <span class="tag ${repCls}">${esc(issue.author_reputation)}</span>
        <span class="tag ${issue.has_stacktrace?'tag-yes':'tag-no'}">${issue.has_stacktrace?'stacktrace':'no stacktrace'}</span>
        <span class="tag ${issue.has_reproduction_steps?'tag-yes':'tag-no'}">${issue.has_reproduction_steps?'repro steps':'no repro'}</span>
        <span class="tag tag-unk">${esc(issue.author)}</span>
      </div>
      <div class="issue-body">${esc(issue.body)}</div>
      <div class="form-grid">
        <div class="field">
          <label>Label</label>
          <select id="selLabel">
            <option value="">— choose —</option>
            <option>bug</option><option>feature</option>
            <option>question</option><option>duplicate</option><option>security</option>
          </select>
        </div>
        <div class="field">
          <label>Priority</label>
          <select id="selPri">
            <option value="">— choose —</option>
            <option>critical</option><option>high</option><option>medium</option><option>low</option>
          </select>
        </div>
        <div class="field">
          <label>Assign team</label>
          <select id="selTeam">
            <option value="">— none —</option>
            <option>backend</option><option>frontend</option>
            <option>devops</option><option>security</option><option>docs</option>
          </select>
        </div>
        <div class="field">
          <label>Close reason</label>
          <select id="selClose">
            <option value="">— none —</option>
            <option>duplicate</option><option>invalid</option><option>wontfix</option>
          </select>
        </div>
        <div class="field field-full">
          <label>Request info (optional)</label>
          <textarea id="txtReq" placeholder="Ask reporter for reproduction steps, environment details..."></textarea>
        </div>
      </div>
      <button class="btn-submit" id="submitBtn" onclick="submitAction('${issue.id}')">Submit Triage Action</button>
      <button class="btn-skip" onclick="skipAction('${issue.id}')">Skip this issue</button>
    </div>
  `);
}

async function submitAction(issueId){
  const label=document.getElementById('selLabel')?.value;
  const priority=document.getElementById('selPri')?.value;
  const team=document.getElementById('selTeam')?.value;
  const closeR=document.getElementById('selClose')?.value;
  const reqText=document.getElementById('txtReq')?.value?.trim();
  let actionType='label';
  if(closeR)actionType='close';
  else if(reqText)actionType='request_info';
  else if(label)actionType='label';
  else if(priority)actionType='prioritize';
  else if(team)actionType='assign';
  const action={action_type:actionType,issue_id:issueId};
  if(label)action.label=label;
  if(priority)action.priority=priority;
  if(team)action.team=team;
  if(closeR)action.close_reason=closeR;
  if(reqText)action.request_text=reqText;
  const btn=document.getElementById('submitBtn');
  if(btn){btn.disabled=true;btn.textContent='Submitting...';}
  await doStep(action);
}

async function skipAction(issueId){
  await doStep({action_type:'skip',issue_id:issueId});
}

async function doStep(action){
  const r=await fetch('/step',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(action)});
  const result=await r.json();
  obs=result.observation;done=result.done;
  steps++;totalR+=result.reward?.value||0;
  addFeed(result.reward,action);
  if(done){await loadGrade();showDone();}
  else renderIssue();
}

async function loadGrade(){
  const r=await fetch('/grader');
  const g=await r.json();
  document.getElementById('scoreNum').textContent=(g.grader_score||0).toFixed(3);
  document.getElementById('scoreBox').style.display='block';
}

function showDone(){
  const total=obs?.inbox_size||0;
  setIssue(`
    <div class="fade-in done-box">
      <h3>Episode Complete</h3>
      <p>Processed ${total} issues in ${steps} steps</p>
      <p style="margin-top:4px">Total reward accumulated: <strong style="color:#e2e8f0">${totalR.toFixed(3)}</strong></p>
      <button class="btn-again" onclick="startEpisode()">Run Again</button>
      <button class="btn-back" onclick="backToTasks()">Try Another Task</button>
    </div>
  `);
  loadGrade();
}

function backToTasks(){
  document.getElementById('mainGrid').style.display='none';
  document.getElementById('emptyState').style.display='block';
  document.querySelectorAll('.task-card').forEach(c=>c.classList.remove('active'));
}

function addFeed(reward,action){
  const feed=document.getElementById('feed');
  if(feed.children[0]?.style.textAlign==='center')feed.innerHTML='';
  const val=reward?.value||0;
  const cls=val>0.1?'feed-pos':val<0?'feed-neg':'feed-neu';
  const sign=val>=0?'+':'';
  const d=document.createElement('div');
  d.className='feed-item '+cls+' fade-in';
  d.innerHTML=`<span class="feed-val">${sign}${val.toFixed(3)}</span><span class="feed-txt">${action.action_type}${action.label?' / '+action.label:''}${action.priority?' / '+action.priority:''}</span>`;
  feed.insertBefore(d,feed.firstChild);
}

function setIssue(html){document.getElementById('issueContent').innerHTML=html}
function setStats(s,l,b,r){
  document.getElementById('sStep').textContent=s;
  document.getElementById('sLeft').textContent=l;
  document.getElementById('sBudget').textContent=b;
  document.getElementById('sReward').textContent=(r||0).toFixed(2);
}
function setProgress(done,total){
  const pct=total>0?Math.round((done/total)*100):0;
  document.getElementById('progFill').style.width=pct+'%';
  document.getElementById('progPct').textContent=pct+'%';
}
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
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
