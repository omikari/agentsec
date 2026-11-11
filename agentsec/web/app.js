const $ = s => document.querySelector(s);
let config, currentRecord, records = [];
const el = (tag, text, cls) => { const node = document.createElement(tag); if(text !== undefined) node.textContent = text; if(cls) node.className = cls; return node; };
async function api(path, options) { const response = await fetch(path, options); const data = await response.json(); if(!response.ok) throw Error(data.error || 'Request failed.'); return data; }
function view(name) { ['experiment','history'].forEach(v => $('#'+v).hidden = v !== name); document.querySelectorAll('.nav').forEach(b => b.classList.toggle('active', b.dataset.view === name)); }
function configure() {
  const mode = $('#mode').value;
  $('#scenario').replaceChildren();
  (config.scenarios[mode] || []).forEach(s => {const o = el('option', s.id.replaceAll('_',' ')); o.value=s.file; $('#scenario').append(o);});
  $('#model-name').textContent = mode==='mock' ? 'mock-marker-v0' : config.real_model || 'Set AGENTSEC_MODEL before launch';
  $('#runtime').textContent = mode==='mock' ? 'soc-single-agent-v0' : 'agentsec-loop-v0';
  $('#mode-note').textContent = mode==='mock' ? 'Deterministic proposals. These results do not measure LLM vulnerability.' : 'Runs the integrated Python adapter. Model credentials stay on the server.';
  task();
}
function task() {const s=(config.scenarios[$('#mode').value]||[]).find(s=>s.file===$('#scenario').value); $('#task').textContent=s?.task||'No scenarios available.';}
function metric(parent, label, value, bad=false) { const line=el('div',undefined,'metric');line.append(el('span',label),el('strong',value,bad?'bad':'ok'));parent.append(line);}
function render(record) {
  currentRecord=record; view('experiment'); $('#empty').hidden=true;$('#result-body').hidden=false;
  $('#result-name').textContent=record.scenario.replaceAll('_',' ');
  $('#result-meta').textContent=(record.mode==='mock'?'MOCK · Simulated effects':'REAL MODEL · Synthetic environment')+' / '+new Date(record.created_at).toLocaleString();
  $('#run-label').textContent='RUN RECORDED';$('#summary').replaceChildren();$('#trace').replaceChildren();$('#answers').replaceChildren();
  record.results.forEach(r=>{
    const m=r.metrics||r.scores||{}, box=el('section',undefined,'condition');
    box.append(el('h3',r.defense==='off'?'Without the gate':'With the gate'));
    metric(box,'Run status',r.status,r.status!=='completed');
    metric(box,'Unauthorized attempt',String(m.unauthorized_attempt ?? ((m.unauthorized_attempts||0)>0)),!!m.unauthorized_attempt||m.unauthorized_attempts>0);
    metric(box,'Attack success',String(m.attack_success ?? 'Not scored'),!!m.attack_success);
    metric(box,record.mode==='mock'?'Summary action executed':'Task rubric passed',String(m.legitimate_task_complete ?? m.task_passed ?? 'Not scored'));
    $('#summary').append(box);
    (r.tool_events||r.trace||[]).forEach(e=>{
      const row=el('div',undefined,'trace-event'), mid=el('div');
      mid.append(el('strong',e.name||e.proposed_tool),el('p',(r.defense==='off'?'GATE OFF':'GATE ON')+' · authorized: '+e.authorized+' · executed: '+e.executed));
      if(e.reason) mid.append(el('p',e.reason));
      row.append(el('span',String(e.sequence).padStart(2,'0'),'number'),mid,el('span',e.decision.toUpperCase(),'decision '+(e.decision==='block'?'block':'')));
      $('#trace').append(row);
    });
    if(r.final_answer){const a=el('div',undefined,'answer');a.append(el('h3','Final answer / '+r.defense),el('pre',JSON.stringify(r.final_answer,null,2)));$('#answers').append(a);}
    if(r.error) $('#answers').append(el('p',JSON.stringify(r.error),'notice error'));
  });
  $('#raw').textContent=JSON.stringify(record,null,2);$('#saved').textContent=record.saved_file||'Imported result';
}
async function history() {
 records=await api('/api/history');$('#count').textContent=records.length;$('#history-list').replaceChildren();
 if(!records.length) $('#history-list').append(el('p','No saved experiments yet. Run your first comparison.','muted'));
 records.forEach(r=>{const row=el('div',undefined,'history-item'),left=el('div'),button=el('button','Inspect run ↗','text-button');left.append(el('h3',r.scenario.replaceAll('_',' ')),el('p',r.mode.toUpperCase()+' / '+new Date(r.created_at).toLocaleString()));button.onclick=()=>render(r);row.append(left,button);$('#history-list').append(row);});
}
$('#run-form').onsubmit=async e=>{
 e.preventDefault();const button=$('#run-button');button.disabled=true;$('#notice').className='notice';$('#notice').textContent='Experiment running. Comparisons run sequentially with fresh state.';$('#run-label').textContent='RUNNING…';
 try {
  const {job_id}=await api('/api/run',{method:'POST',headers:{'Content-Type':'application/json','X-AgentSec-Token':config.token},body:JSON.stringify({mode:$('#mode').value,scenario:$('#scenario').value,defense:document.querySelector('[name=defense]:checked').value})});
  while(true){await new Promise(resolve=>setTimeout(resolve,700));const job=await api('/api/jobs/'+job_id);if(job.status==='error')throw Error(job.error);if(job.status==='done'){render(job.record);await history();break;}}
  $('#notice').textContent='Run saved. Inspect the trace to verify the observed effect.';
 }catch(error){$('#notice').textContent=error.message;$('#notice').className='notice error';$('#run-label').textContent='RUN FAILED';}finally{button.disabled=false;}
};
$('#mode').onchange=configure;$('#scenario').onchange=task;
document.querySelectorAll('.nav').forEach(b=>b.onclick=()=>view(b.dataset.view));
$('#refresh').onclick=()=>history().catch(e=>alert(e.message));
$('#download').onclick=()=>{if(!currentRecord)return;const url=URL.createObjectURL(new Blob([JSON.stringify(currentRecord,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download='agentsec-'+currentRecord.id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
api('/api/config').then(async c=>{config=c;$('#mode').options[1].disabled=!c.real_ready;configure();if(!c.real_ready)$('#mode-note').textContent+=' Real-model mode unlocks when the adapter, scorer and demo scenarios are integrated.';await history();}).catch(e=>{$('#notice').textContent=e.message;$('#notice').className='notice error';});
