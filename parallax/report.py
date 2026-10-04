"""Self-contained, offline HTML walkthrough (D)."""
import html
import json


def build_report(run):
    data = json.dumps(run).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return TEMPLATE.replace('__TOTALS__', summary_tables(run.get('summary', {}))).replace('__RUN_DATA__', data)


def table(headers, rows):
    """Escape every saved value, including exclusion reasons and case IDs."""
    def cell(value):
        return html.escape('Unavailable' if value is None else str(value), quote=True)
    head = ''.join('<th>' + cell(h) + '</th>' for h in headers)
    body = ''.join('<tr>' + ''.join('<td>' + cell(v) + '</td>' for v in row) + '</tr>' for row in rows)
    return '<div style="overflow:auto"><table><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table></div>'


def summary_tables(summary):
    rows = []
    for label in ('harmful', 'benign'):
        counts = summary.get('classes', {}).get(label, {})
        directions = summary.get(label + '_directions', {})
        rows.append([label, counts.get('planned'), counts.get('eligible'),
                     counts.get('excluded_by_checks'), counts.get('incomplete_primary'),
                     directions.get('more_forgiving', {}).get('count'),
                     directions.get('more_forgiving', {}).get('rate'),
                     directions.get('stricter', {}).get('count'),
                     directions.get('stricter', {}).get('rate')])
    output = table(['Class', 'Planned', 'Eligible', 'Excluded', 'Incomplete',
                    'More forgiving', 'Rate', 'Stricter', 'Rate'], rows)
    output += '<h3>Why reviews abstained</h3>' + table(
        ['Cause', 'Count', 'Processed review denominator'],
        [[cause, count, summary.get('scheduled_judgments_denominator')]
         for cause, count in summary.get('call_abstention_causes', {}).items()])
    output += '<h3>Human-review requests</h3>' + table(
        ['Class', 'Escalated', 'Cases submitted to gate'],
        [[label, record.get('escalated'), record.get('cases')]
         for label, record in summary.get('escalation_by_class', {}).items()])
    excluded = summary.get('excluded_cases', [])
    output += '<h3>Excluded primary cases</h3>'
    output += table(['Case', 'Class', 'Stage', 'Reason'],
                    [[e.get(k) for k in ('case_id', 'ground_truth', 'stage', 'reason')] for e in excluded]) if excluded else '<p>No primary-case exclusions recorded.</p>'
    return output


TEMPLATE = '''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Parallax-R — follow one case</title>
<style>
:root{font-family:system-ui,sans-serif;color:#172c3a;background:#f2f5f7;line-height:1.55}body{max-width:1180px;margin:auto;padding:28px}h1{font-size:36px;margin-bottom:8px}h2{font-size:22px}h3{margin-top:0}.kicker{color:#456373;font-weight:700;letter-spacing:.1em}.notice{position:sticky;top:0;z-index:10;background:#fff0c9;border-left:5px solid #ca8500;padding:16px;border-radius:8px}section,.card{background:white;padding:22px;border-radius:12px;margin:18px 0;border:1px solid #d5e1e8}select,button{font:inherit;padding:10px;border-radius:8px;border:1px solid #91a9b9;background:white}select{max-width:100%}button{cursor:pointer}button.active{background:#154f66;color:white}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.card{margin:0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f0f4f7;padding:12px;font-size:13px;max-height:420px;overflow:auto}small,.muted{color:#526876}.tag{display:inline-block;padding:5px 10px;border-radius:7px;background:#e4eef3;font-weight:700}.alert{background:#ffe3d9;color:#8b2b12}.good{background:#def0e5;color:#205433}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px;border-bottom:1px solid #d8e2e8}.steps{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}summary{cursor:pointer;font-weight:600}#raw{font-size:12px}a{color:#095775}@media(max-width:700px){.grid{grid-template-columns:1fr}body{padding:14px}h1{font-size:28px}table{font-size:13px}}
</style>
<header><div class="kicker">PARALLAX-R · WORKING PROTOTYPE</div><h1>Same action. Different review?</h1>
<p>Follow one recorded action from the original instruction to the final review decision.</p></header>
<div id="notice" class="notice"></div>
<section><label for="case"><b>Choose a case</b></label><br><select id="case"></select>
<p class="muted">All included cases are fictional. No files were emailed and no actor was executed.</p>
<div class="steps" id="steps"></div></section>
<main id="main"></main><nav class="steps" aria-label="Walkthrough navigation"><button id="back">Previous step</button><button id="next">Next step</button></nav>
<section><h2>Run totals</h2><div id="totals"></div>__TOTALS__<details><summary>Full machine-readable summary</summary><pre id="summary"></pre></details></section>
<section><h2>Who does what next?</h2><p><b>A — You:</b> check the rules, labels, and whether both stories keep the same important facts.</p>
<p><b>B:</b> connect a real reviewer, run the experiment, and save responses.</p><p><b>C:</b> improve the different presentations and calculate comparisons.</p><p><b>D:</b> challenge the evidence checks, improve this display, and prepare the demo.</p>
<p>Read <b>README.md</b> for commands and <b>docs/HACKATHON-REPORT.md</b> for architecture, metrics, and limitations. This page displays saved output; selecting a case does not call an AI or spend API credits.</p></section>
<script>
const run=__RUN_DATA__;
const esc=s=>String(s??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pretty=x=>esc(JSON.stringify(x,null,2));
const names=['1. What happened','2. Check records','3. Make versions','4. Ask reviewer','5. Compare','6. Decide'];
const labels={full:'Full: explanation included',action_only:'Action-only: explanation removed',masked:'Masked: actor name replaced',ledger:'Ledger: evidence listing'};
let current=0,step=0;
document.getElementById('notice').textContent=run.mode==='demo'?'OFFLINE TEACHING DEMO — Reviewer answers are scripted to show how the program works. These are not real AI results or research findings.':'REAL API RUN — Answers came from the configured AI model on fictional cases. This exploratory run is not evidence of general reliability.';
const sel=document.getElementById('case');run.results.forEach((r,i)=>{let o=document.createElement('option');o.value=i;o.textContent=r.case.case_id+' · '+(r.case.condition||r.case.ground_truth);sel.append(o)});sel.onchange=()=>{current=Number(sel.value);draw()};
document.getElementById('back').onclick=()=>{step=Math.max(0,step-1);draw()};
document.getElementById('next').onclick=()=>{step=Math.min(5,step+1);draw()};
names.forEach((n,i)=>{let b=document.createElement('button');b.textContent=n;b.onclick=()=>{step=i;draw()};document.getElementById('steps').append(b)});
const box=(title,text)=>`<div class="card"><h3>${esc(title)}</h3>${text}</div>`;
function draw(){document.getElementById('back').disabled=step===0;document.getElementById('next').disabled=step===5;document.querySelectorAll('#steps button').forEach((b,i)=>b.className=i===step?'active':'');if(!run.results.length){document.getElementById('main').innerHTML='<section><p>No cases reached review. See exclusions in Run totals.</p></section>';return;}let r=run.results[current],c=r.case,m=r.metrics,out='';
if(step===0)out=`<h2>1. Read the rule and the recorded action</h2><div class="grid">${box('Instruction',`<p>${esc(c.task)}</p><p><b>${esc(c.policy)}</b></p>`)}${box('Recorded action',c.events.length?c.events.map(e=>`<p>${esc(e.actor)}: ${esc(e.operation)} ${esc(e.resource)}</p><p>${esc(e.output)}</p>`).join(''):'<p>The transcript contains no action. Check the receipts in step 2.</p>')}</div><p><b>Actor’s explanation:</b> ${esc(c.narrative)}</p><p><b>Teaching answer key:</b> ${esc(c.ground_truth)}. The program does not show this label to the reviewer.</p><p>This actor is a fictional entry in a JSON file, not an AI we are running.</p>`;
if(step===1)out=`<h2>2. Compare the transcript with separate records</h2><p>A receipt records an operation. Here we generated fictional receipts so we can deliberately test missing or inconsistent records.</p><table><tr><th>Event</th><th>Check result</th><th>Receipt</th></tr>${r.reconciliation.findings.map(f=>`<tr><td>${esc(f.event_id)}</td><td>${esc(f.status)}</td><td>${esc(f.receipt_ids.join(', '))}</td></tr>`).join('')}</table><p>Record completeness: <b>${esc(c.coverage)}</b>.</p><p>SUPPORTED = operation fields match; it does not override a CHAIN_BREAK finding. PHANTOM = no receipt found. HIDDEN = a receipt exists for an action omitted from the transcript. MISMATCH = records disagree. CHAIN_BREAK = a digest or chain link failed validation. A missing receipt does not prove non-occurrence; a chain gap does not by itself prove tampering. These checks do not prove intent.</p><details><summary>Inspect receipts</summary><pre>${pretty(c.receipts)}</pre></details>`;
if(step===2)out=`<h2>3. Prepare different versions of the same evidence</h2><p>The instruction, operation, output, and receipt status remain present. We remove the explanation in action-only and ledger views. Identity masking changes display names only.</p><p class="tag ${Object.keys(m.view_validation_failures||{}).length?'alert':'good'}">${Object.keys(m.view_validation_failures||{}).length?'A version failed validation; see the saved failure below.':'Automated evidence checks passed'}</p><p>Human review is still needed to check that removing text did not change its meaning.</p><div class="grid">${r.views.map(v=>box(labels[v.name]||v.name,`<p>${v.payload.explanation?'Explanation included':'Explanation removed'}</p><p>${esc(m.view_validation_failures?.[v.name]||'')}</p><details><summary>Exact input sent to reviewer</summary><pre>${pretty(v.payload)}</pre></details>`)).join('')}</div>`;
if(step===3)out=`<h2>4. Review each version independently</h2><p>${run.mode==='demo'?'The offline reviewer is deliberately programmed to accept the excuse. This demonstrates a failure; it does not discover one.':'Each uncached request uses a fresh API conversation with the same rubric.'}</p><div class="grid">${Object.entries(m.groups).map(([name,g])=>box(labels[name]||name,`<p><b>${esc(g.verdict)}</b> · mean risk ${g.risk===null?'unavailable':g.risk.toFixed(2)}</p>${r.rows.filter(x=>x.view===name).map(x=>`<p>Review ${x.repeat}: ${esc(x.verdict)}${x.cache_hit?' (saved response)':''}</p><small>${esc(x.judgment?.rationale||x.error)}</small>`).join('')}`)).join('')}</div>`;
if(step===4)out=`<h2>5. Compare the answers</h2><p>Action-only mean score minus full-story mean score: <b>${m.delta===null?'unavailable':m.delta.toFixed(2)}</b>.</p><p>A positive number means the full story looked less risky to this reviewer.</p><p><b>Direction:</b> ${esc(m.direction)} · <b>Expected verdict:</b> ${esc(m.expected_verdict)}</p><table><tr><th>Version</th><th>Mean risk</th><th>Majority verdict</th><th>Repeat variation</th><th>Complete</th><th>Matches expected</th></tr>${Object.entries(m.groups).map(([n,g])=>`<tr><td>${esc(n)}</td><td>${esc(g.risk)}</td><td>${esc(g.verdict)}</td><td>${esc(g.repeat_sd)}</td><td>${esc(m.view_results?.[n]?.complete)}</td><td>${m.view_results?.[n]?.matches_expected==null?'Not applicable':esc(m.view_results[n].matches_expected)}</td></tr>`).join('')}</table><p>D (spread across three views): ${esc(m.D)} · F (any verdict disagreement): ${esc(m.F)} · U (unresolved citations): ${esc(m.U)}</p><p>U only checks whether cited IDs exist. It does not prove that the cited evidence supports the conclusion.</p>`;
if(step===5)out=`<h2>6. Decide whether a person should check</h2><p class="tag ${m.decision.action==='ESCALATE'?'alert':'good'}">${esc(m.decision.action)}</p><p>${m.decision.action==='ESCALATE'?'Ask a person to examine this case. This does not automatically mean the actor was malicious.':'The implemented checks passed and reviewer verdicts agree: '+esc(m.decision.accepted_verdict)+'. This is not a guarantee of safety.'}</p><p>Reasons: <b>${esc(m.decision.reason_codes.join(', ')||'No implemented check triggered')}</b></p><p>VIEW_FRAGILITY means versions produced different verdicts. EVIDENCE_CONFLICT means records disagree or an action lacks a matching record. INCOMPLETE_RECORD means completeness is unknown. UNSUPPORTED_CLAIM means a decisive claim lacks resolvable evidence references. FLAG describes the behavior assessment; ESCALATE requests review and does not remove an eligible comparison from the measurements. MONITOR_ABSTENTION means a review could not be used.</p><details><summary>Decision and evidence IDs</summary><pre>${pretty(m.decision)}</pre></details>`;
document.getElementById('main').innerHTML='<section>'+out+'</section>';
}
document.getElementById('totals').textContent=`${run.summary.cases} cases · ${run.summary.scheduled_judgments} processed review records · ${run.summary.abstentions} abstentions · ${run.summary.escalation_count} cases marked for human review (no notification sent). Pilot status: ${run.summary.pilot_status}.`;
document.getElementById('summary').textContent=JSON.stringify(run.summary,null,2);draw();
</script></html>'''
