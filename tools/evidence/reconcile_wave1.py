#!/usr/bin/env python3
"""Rebuild the Wave 1 terminal evidence projection from retained observations.

This is offline evidence tooling, not execution/lifecycle authority. No GitHub
write, provider invocation, or runtime mutation is performed. The source bundle
contains published Issue observations and an allowlisted runtime evidence export.
"""
import argparse
import collections
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
E = ROOT / 'docs/evidence'
SOURCE = E / 'wave1-source-observations.json'
TERMINAL = '10cc81620511af56befbb6140504d1991bb02846'
IDS = dict(zip([2,50,51,52,53,54,55,56,57,68,58],
              ['PY-01','PY-02','PY-03','PY-04','PY-05','PY-06','PY-07','PY-08','PY-09','PY-09B','PY-10']))
MERGES = ['ab08449','ab4efe5','d8f80e1','0170af0','5b617a3','896c0fe','946e3cc','2c179e5','85b6060','93dd8b1','10cc816']
TESTS = [6,23,40,65,87,110,129,158,209,308,344]
MARKER = re.compile(r'<!-- B-DISP: INVOCATION=(AlienLogicLab/alienintent#(\d+):(PRODUCER|VERIFIER):[a-f0-9-]+) (RESULT|CONTROL)=([A-Z_]+) -->')
# Report-local directed report finding groups. Not distinct defects
# across time; subpoints stay grouped. Non-blocking observations are excluded.
GROUPS = {
 'PY-01':[3,2,0], 'PY-02':[3,0], 'PY-03':[4,0],
 'PY-04':[5,5,10,3,2,1,1,1,2,0], 'PY-05':[6,1,0],
 'PY-06':[9,6,5,2,0], 'PY-07':[4,2,3,3,1,0],
 'PY-08':[12,14,11,10,8,3,0], 'PY-09':[5,2,5,0],
 'PY-09B':[0], 'PY-10':[0],
}
COUNT_NOTES = {
 'PY-04':'Numbered unresolved contract groups; cycle 4 secondary observation excluded; cycle 8 is one blocking mutation-class group with five surviving mutations, not five unique findings.',
 'PY-07':'Main acceptance/scope groups only, excluding residual/minor observations; cycle 1 groups several smaller obligations under heading 4; cycles 2/3 exclude restated residuals.',
 'PY-08':'Cycle 6 has three directed repair groups Y2/Y4/Z1 (Z1 non-decisive), five explicitly open IDs including Y7/Y8, and two decisive unmet AC groups Y2/Y4. Legacy result-row 7 is this sixth verdict, not execution cycle 7. Zero at ACCEPT means no blocking repair, not zero residual observations.',
 'PY-09':'Cycle 1: two blocking heading groups plus three reproduced correctness groups; cycle 3 five blocking headings. Counts do not expand every AC/subpoint or additional non-blocking observation.',
}

def read(path): return json.loads(Path(path).read_text())
def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')
def git(*args):
    return subprocess.check_output(['rtk','proxy','git',*args],cwd=ROOT,text=True).strip()
def instant(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
def status(item):
    return next((x['name'] for x in item['fieldValues']['nodes'] if x.get('field',{}).get('name')=='Status'),'UNKNOWN')
def markers(issue):
    found=[]
    for c in issue['comments']:
        for m in MARKER.finditer(c['body']):
            if int(m[2]) != issue['number']: continue
            found.append(dict(c,invocation_id=m[1],role=m[3],signal_type=m[4],result=m[5]))
    return found
def event(biu,n,kind,at,refs,**fields):
    return dict(schema_version='1.0',event_id=f'wave1-terminal-{biu}-{n}',project='AlienIntent',repository='AlienLogicLab/alienintent',biu_id=biu,event_type=kind,actor_role=fields.pop('actor_role','RECORDER'),evidence_refs=refs,recorded_at=at,reconciliation='wave1-terminal',observation_type=fields.pop('observation_type','state-record observation'),**fields)

def enrich(biu, source, add):
    histories={'PY-09B':['d35928d','d01bc38','d3f54eb'],'PY-10':['c32830b','1f16b81','693fef9']}
    for ref in histories.get(biu,[]):
        path=f'docs/work-units/python/{biu}.assessment.json'
        revision=git('rev-parse',ref); text=git('show',f'{ref}:{path}'); assessment=json.loads(text)
        add('READINESS_ASSESSMENT_RECORDED',[f'https://github.com/AlienLogicLab/alienintent/blob/{revision}/{path}'],started_at=git('show','-s','--format=%cI',ref),result=assessment['disposition'],assessment_sha256=hashlib.sha256(text.encode()).hexdigest(),expected_rework_locality=assessment.get('expected_rework_locality','UNKNOWN'),description='Separate immutable assessment at its repository revision; timestamp is commit retention time, not inferred assessment execution time.')
    if biu=='PY-09':
        resources={x['invocationId']:x for x in source['runtime']['resources']}
        for x in source['runtime']['log_excerpts']:
            r=resources[x['invocation_id']]; capacity=x['terminal_record']['type']=='turn.failed'
            add('INVOCATION_CAPACITY_FAILED' if capacity else 'VERIFIER_NO_VERDICT',['docs/evidence/wave1-source-observations.json#runtime/log_excerpts','docs/evidence/2026-09-21-py09-provider-capacity-interruption.md'],started_at=r['createdAt'],ended_at=r['exitedAt'],invocation_id=x['invocation_id'],actor_role=r['role'],execution_cycle=4,provider='codex' if capacity else 'claude',result='DURABLE_RESULT_MISSING',resource_id=r['resourceId'],provider_terminal_observation=x['terminal_record'],description='No durable work result; does not add a verifier rejection or execution cycle. Provider invocation success is not a work verdict.')
        for x in source['runtime']['observations']['coordinator-liveness.jsonl']:
            if x.get('issue')==57 and x.get('event')=='LIVENESS_SUPPRESSED':
                add('LIVENESS_SUPPRESSED',['docs/evidence/wave1-source-observations.json#runtime/observations'],started_at=x['at'],execution_cycle=4,description='IMPLEMENT without actor, age 441s > 300s grace; unresolved DURABLE_RESULT_MISSING attention suppresses re-emission.',observed=x)
        add('PROVIDER_FAILOVER_RECORDED',['https://github.com/AlienLogicLab/alienintent/issues/57#issuecomment-5754575853','docs/evidence/2026-09-21-py09-provider-capacity-interruption.md'],execution_cycle=4,invocation_id='AlienLogicLab/alienintent#57:PRODUCER:9979bdcc-adaf-4b5a-9847-265e6556645e',provider='claude',actor_role='PRODUCER',started_at='2026-09-21T02:21:37.058Z',description='Continuation of cycle 4 after Codex quota exhaustion. Preserved resource 63097907 holds uncommitted partial work. Recovery authorization comment was posted at 02:21:38Z, after resource allocation by 0.942s; pre-launch ordering of the comment is not supported. Founder authorization is reported, its exact instant UNKNOWN.')
    if biu=='PY-09B':
        add('BIU_DECOMPOSITION_RECORDED',['docs/decisions/2026-09-21-py10-transport-split.md','docs/decisions/2026-09-21-sandbox-isolation-standard.md'],description='SWF-33 inserted PY-09B after PY-10 SPLIT_RECOMMENDED. SWF-34 resolved impossible token-level Project isolation: repository permission boundary, deterministic Project targeting, PY-10 AC16 compensating proof.')
        for suffix,description in [('pre-contents-grant','Passing check against wrong expected permission contract'),('negative-control','Correct expected contract, real missing contents:write grant: 2 failed of 17'),('post-contents-grant','Corrected installation and expected contract: 17/17 passing')]:
            p=f'docs/evidence/py10-preflight-2026-09-21-{suffix}.json'; d=read(ROOT/p)
            add('PREFLIGHT_OBSERVED',[p],check_passed=sum(c['ok'] for c in d['checks']),check_count=len(d['checks']),result='PASS' if d['ok'] else 'FAIL',description=description+'. Discriminating check correctness does not imply specification correctness.')
        add('LIVE_TRANSPORT_VERIFIED',['docs/evidence/PY-09B-live-transport.md','https://github.com/AlienLogicLab/alienintent/issues/68#issuecomment-5759003341'],observation_type='independent verification',description='Verifier independently reproduced 35/35 live checks, 13/13 proven-red guards, 308 Python tests, fitness PASS and Node 310+18+2. Includes live clone/push/fresh-clone read-back, exact permissions, fenced projection, signed ingress/replay and foreign-Project refusal; probe resources removed by that historical run.')
    if biu=='PY-10':
        d=read(E/'py10/proof-run.json')
        add('LIVE_PROOF_RETAINED',['docs/evidence/py10/proof-run.json','docs/evidence/py10/run-timeline.jsonl','docs/evidence/execution-trajectories/PY-10-sandbox-run.jsonl','https://github.com/AlienLogicLab/alienintent/issues/58#issuecomment-5760269849'],started_at=d['started_at'],ended_at=d['finished_at'],sandbox_repository=d['repository'],sandbox_project=d['project'],seeded_bius=6,done_bius=6,candidate_branches=6,description='Integrated run: priority/FIFO, dependency, WIP 1 across 34 samples plus exclusion probe; two durable decisions; SIGKILL restart parks unknown effect, independent work continues; no duplicate published effects. 13 successful operator commands plus killed run; no manual IMPLEMENT command evidenced. AC16 before/after digests producer-retained; independent verifier could not re-read production Project. AC17 independently audited; no fresh live execution here.')
        add('REMOTE_CUSTODY_READ_BACK',['docs/evidence/wave1-source-observations.json#sandbox_remote','docs/evidence/wave1-source-observations.json#sandbox_project'],description='Fresh read-only GitHub capture: exactly six candidate refs with recorded SHAs, each one commit ahead of sandbox main touching its own note; all six sandbox items DONE and two decision items retained. Seven total refs includes main, not a seventh candidate or repair cycle.')

def derive(source):
    project=source['project']['data']['organization']['projectV2']
    items={x['content']['number']:x for x in project['items']['nodes'] if x.get('content') and 'number' in x['content']}
    rows=[]; cycles=[]; trajectories={}
    for index,issue in enumerate(source['issues']):
        number=issue['number']; biu=IDS[number]; signals=markers(issue)
        verdicts=[c for c in signals if c['role']=='VERIFIER' and c['result'] in ['REJECT','ACCEPT']]
        assert len(verdicts)==len(GROUPS[biu]), (biu,len(verdicts))
        accepted=[c for c in verdicts if c['result']=='ACCEPT']; assert len(accepted)==1
        accept=accepted[0]
        candidate=re.search(r'\b[a-f0-9]{40}\b',accept['body'])[0]
        merge=git('rev-parse',MERGES[index])
        closure=next(x for x in source['runtime']['closures'] if x['item']['issue']==number and x['result']=='DONE')
        resources=[x for x in source['runtime']['resources'] if x['issue']==number]
        contract=(ROOT/f'docs/work-units/python/{biu}.md').read_text()
        requirement_lines=[s for s in contract.splitlines() if s.startswith('| SF-REQ-')]
        requirements=[{'id':re.search(r'SF-REQ-\d+',s)[0],'extent':s.split('|')[-2].strip()} for s in requirement_lines]
        predecessor=next((s for s in contract.splitlines() if s.startswith(('**Predecessor:','**Predecessors:'))),'None declared')
        deps=list(dict.fromkeys(re.findall(r'PY-\d\dB?',predecessor.split('**Baseline:')[0])))
        assessment=read(ROOT/f'docs/work-units/python/{biu}.assessment.json')
        release=next((c for c in issue['comments'] if c['author']=='sanookdu' and ('release authorization' in c['body'] or 'TASKS → READY → IMPLEMENT' in c['body'])),None)
        start=release['created_at'] if release else min(x['createdAt'] for x in resources)
        release_baseline=(re.search(r'\b[a-f0-9]{40}\b',release['body'])[0] if release and re.search(r'\b[a-f0-9]{40}\b',release['body']) else 'UNKNOWN')
        rejects=sum(c['result']=='REJECT' for c in verdicts)
        row=dict(biu_id=biu,issue_number=number,issue_url=issue['url'],title=issue['title'],requirements=requirements or 'UNKNOWN',requirement_note='PY-01 is governed by architecture authority; no SF-REQ mapping declared in its contract.' if not requirements else 'Extent is the contract contribution, not a declaration that the entire Product Requirement is DONE.',dependencies=deps,native_blocked_by=[IDS[d['number']] for d in issue['dependencies']],project_item=items[number]['id'],final_lifecycle_state=status(items[number]),issue_state=issue['state'].upper(),accepted_candidate=candidate,merge_commit=merge,agent_ready={'disposition':assessment['disposition'],'expected_rework_locality':assessment.get('expected_rework_locality','UNKNOWN')},verifier_rejections=rejects,verifier_verdicts=len(verdicts),execution_cycles=rejects+1,execution_cycle_definition='Initial admitted IMPLEMENT plus each verifier-returned repair; same-phase authority recovery/re-emission, capacity failover and no-verdict retry excluded. No ACCEPT-to-IMPLEMENT control marker exists in captured Wave 1 records.',first_pass_accepted=rejects==0,founder_exception_markers=sum(c['result']=='FOUNDER_EXCEPTION' for c in signals),done_signal_at=closure['signalEvidence']['createdAt'],done_at=closure['completedAt'],issue_closed_at=issue['closed_at'],accepted_at=accept['created_at'],release_record_at=release['created_at'] if release else 'UNKNOWN',timing_origin=start,timing_origin_definition='release authorization comment' if release else 'first retained producer allocation; release timestamp UNKNOWN',release_baseline=release_baseline,elapsed_to_done_seconds=round((instant(closure['completedAt'])-instant(start)).total_seconds(),3),test_count_at_landing=TESTS[index],token_usage='UNKNOWN',cost='UNKNOWN',evidence_refs=[issue['url'],accept['url'],f"{issue['url']}#issuecomment-{closure['signalEvidence']['commentId']}",f'docs/work-units/python/{biu}.md','docs/evidence/wave1-source-observations.json'])
        events=[]; now=source['capture']['captured_at']
        def add(kind,refs,**fields): events.append(event(biu,len(events)+1,kind,now,refs,issue_number=number,**fields))
        if release: add('BIU_RELEASED',[release['url']],started_at=start,release_baseline=release_baseline,description='Release authorization record; exact Project-transition timestamp not inferred from comment time.',execution_cycle=1)
        for i,c in enumerate(verdicts,1):
            count=GROUPS[biu][i-1]
            cr=dict(biu=biu,issue=number,cycle=i,execution_cycle=i,outcome=c['result'],invocation_id=c['invocation_id'],reported_at=c['created_at'],report_url=c['url'],findings_total='UNKNOWN',repair_finding_groups=count,findings_count_definition=COUNT_NOTES.get(biu,'Outstanding acceptance/scope report groups; grouped subpoints not expanded. ACCEPT means zero blocking groups only, not zero non-blocking observations.'),unique_findings='UNKNOWN',tests_passed='UNKNOWN',unknown_metrics=['unique_findings','findings_total','tests_passed'])
            # Candidate evidence can be absent, as in PY-04's publication rejection.
            shas=re.findall(r'\b[a-f0-9]{40}\b',c['body'])
            cr['candidate']=shas[0] if shas else 'UNKNOWN'
            if c['url'].endswith('5749643685'):
                cr['candidate']='UNKNOWN'
                cr['presumptive_reviewed_tree']='f95199e6698dcb6b3858ae5e169a30a7fb130fd2'
                cr['candidate_identity_note']='Verifier explicitly rejected timestamp correlation as candidate identification; this presumptive tree is not custody proof.'
            if c['result']=='ACCEPT':
                cr['tests_passed']=TESTS[index]
                cr['acceptance_blockers']=0
                cr['unknown_metrics'].remove('tests_passed')
            else: cr['acceptance_blockers']='UNKNOWN'
            if biu=='PY-08' and i==6:
                cr.update(explicitly_open_ids=['Y2','Y4','Y7','Y8','Z1'],explicitly_open_count=5,decisive_unmet_ac_groups=2,directed_repair_ids=['Y2','Y4','Z1'])
            if biu=='PY-06': cr['findings_count_definition']='Report-headed F/G/H/J groups only; excludes carried non-blocking observations. Zero at ACCEPT means no blocking repair, not no open observations.'
            cycles.append(cr)
            add('VERIFICATION_ACCEPTED' if c['result']=='ACCEPT' else 'VERIFICATION_REJECTED',[c['url']],started_at=c['created_at'],actor_role='VERIFIER',worker_identity=c['author'],invocation_id=c['invocation_id'],result=c['result'],execution_cycle=i,repair_finding_groups=count,description=cr['findings_count_definition'],observation_type='independent verification')
        closure_ids={x['invocationId'] for x in source['runtime']['closures']}
        for r in resources:
            cyc=1+sum(instant(c['created_at'])<instant(r['createdAt']) for c in verdicts if c['result']=='REJECT')
            add('INVOCATION_OBSERVED',['docs/evidence/wave1-source-observations.json#runtime/resources'],started_at=r['createdAt'],ended_at=r['exitedAt'],actor_role=r['role'],invocation_id=r['invocationId'],execution_cycle=cyc,phase='ACCEPT' if r['invocationId'] in closure_ids else ('VERIFY' if r['role']=='VERIFIER' else 'IMPLEMENT'),resource_id=r['resourceId'],branch=r['branch'],allocation_baseline=r['baselineCommit'],provider='UNKNOWN',description='Resource allocation and exit observation. Retained lifecycle RUNNING labels are cleanup metadata, not evidence of a live process.')
        for c in signals:
            if c['result']=='FOUNDER_EXCEPTION': add('HUMAN_DECISION_REQUIRED',[c['url']],started_at=c['created_at'],invocation_id=c['invocation_id'],actor_role=c['role'],result='FOUNDER_EXCEPTION',description='Protocol marker, not automatically a genuine missing-authority decision or verifier rejection.')
        add('CANDIDATE_LANDED',[row['evidence_refs'][2],'commit:'+merge],started_at=git('show','-s','--format=%cI',merge),commit_sha=merge,candidate_ref=candidate,observation_type='Git observation')
        add('BIU_DONE',['docs/evidence/wave1-source-observations.json#runtime/closures'],started_at=row['done_at'],result='DONE',execution_cycle=row['execution_cycles'],description='Dispatcher closure completedAt; distinct from worker result comment and Issue closure.')
        add('ISSUE_CLOSED',[issue['url']],started_at=issue['closed_at'],description='GitHub bookkeeping projection, not the DONE transition.')
        enrich(biu,source,add)
        add('TERMINAL_RECONCILIATION',row['evidence_refs'],terminal=row,description='Supersedes earlier aggregate measurements at the terminal boundary; historical events remain provenance, never added again to this projection.')
        rows.append(row); trajectories[biu]=events
    return rows,cycles,trajectories

def generate(source):
    rows,cycles,trajectories=derive(source)
    write(E/'wave1-closure-manifest.json',{'schema_version':'1.0','terminal_sha':TERMINAL,'captured_at':source['capture']['captured_at'],'bius':rows,'count_definitions':'Combined verifier verdicts: Wave 1 does not distinguish VERIFY failures from REVIEW discoveries. Cycles exclude same-phase retries. No unique-defect total is derived.'})
    old=read(E/'wave1-repair-cycles.json')
    legacy=old.get('superseded_records',old.get('records',[]))
    write(E/'wave1-repair-cycles.json',{'status':'TERMINAL','terminal_sha':TERMINAL,'records':cycles,'superseded_records':legacy,'superseded_records_definition':'Historical result-marker rows; cycle included FOUNDER_EXCEPTION and was not a lifecycle cycle. Retained for correction provenance; excluded from aggregates.','count_definition':'repair_finding_groups counts report-local outstanding acceptance/scope groups, not unique defects or all observations. findings_total remains UNKNOWN when non-blocking prose has no complete count.'})
    for row in rows:
        biu=row['biu_id']; path=E/f'execution-trajectories/{biu}.jsonl'
        prior=[json.loads(s) for s in path.read_text().splitlines() if s] if path.exists() else []
        prior=[s for s in prior if s.get('reconciliation')!='wave1-terminal']
        # Explicit supersession prevents the historical recorder's counts being summed twice.
        for x in prior:
            x['superseded_for_terminal_aggregation_by']='wave1-terminal'
            # Optional v1 timestamps cannot be JSON null. Preserve the old null
            # as provenance without inventing a previously unknown end instant.
            for field in ['started_at','ended_at','parent_candidate']:
                if field in x and x[field] is None:
                    x.pop(field)
                    x.setdefault('historical_schema_corrections',{})[field]='Original null omitted: optional v1 string; UNKNOWN at historical capture, no value inferred.'
        path.write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in prior+trajectories[biu]))
        qp=E/f'quality/{biu}-quality-evidence.json'; oldq=read(qp) if qp.exists() else {}
        historical=oldq.get('superseded_measurement',oldq)
        q=dict(schema_version='1.0',biu_id=biu,derived_from=f'docs/evidence/execution-trajectories/{biu}.jsonl',derivation_scope='reconciliation == wave1-terminal; historical events are explicitly superseded for aggregation',source_schema_version='1.0',evidence_refs=row['evidence_refs'],extraction_status={'value':'TERMINAL','captured_at':source['capture']['captured_at']},first_pass_accepted=row['first_pass_accepted'],verifier_cycles=row['verifier_verdicts'],verifier_rejections=row['verifier_rejections'],repair_cycles=row['verifier_rejections'],execution_cycles=row['execution_cycles'],return_to_implement_count=row['verifier_rejections'],repair_finding_groups_by_verdict=GROUPS[biu],repair_finding_groups_definition='Report-local outstanding acceptance/scope groups; not all observations or unique defects. See per-report definitions in repair dataset.',unique_findings='UNKNOWN',accepted_candidate=row['accepted_candidate'],merge_commit=row['merge_commit'],agent_ready=row['agent_ready'],final_verdict='ACCEPT',landed=True,done=True,done_at=row['done_at'],done_signal_at=row['done_signal_at'],issue_closed_at=row['issue_closed_at'],elapsed_to_done_seconds={'value':row['elapsed_to_done_seconds'],'definition':row['timing_origin_definition']+' to dispatcher DONE completedAt'},test_count_at_landing=row['test_count_at_landing'],token_usage='UNKNOWN',cost='UNKNOWN',founder_exception_markers=row['founder_exception_markers'],unknown_metrics=['end-to-end tokens','end-to-end cost','unique defects across reports','mechanical VERIFY versus qualitative REVIEW attribution','complete per-invocation model attribution'],superseded_measurement=historical)
        if biu=='PY-04': q['formal_independent_verifier_cycles']=10
        if biu=='PY-09': q['provider_capacity_failures']=1; q['verifier_no_verdict_invocations']=1; q['provider_failovers']=1
        write(qp,q)
        summary=f'# {biu} — terminal execution trajectory\n\nSupersedes the pre-closure summary at `{TERMINAL}` (if present). Historical JSONL events remain explicitly superseded for terminal aggregation. This summary uses the `wave1-terminal` projection only.\n\n'
        summary+=f"Issue [#{row['issue_number']}]({row['issue_url']}): **{row['final_lifecycle_state']}**, Issue **{row['issue_state']}**. Agent-Ready **{row['agent_ready']['disposition']}**. {row['verifier_rejections']} combined verifier rejections; {row['verifier_verdicts']} verdicts; {row['execution_cycles']} execution cycles; first-pass accepted: **{str(row['first_pass_accepted']).lower()}**.\n\n"
        summary+=f"Accepted `{row['accepted_candidate']}`; landed `{row['merge_commit']}`. Final Python test observation: **{row['test_count_at_landing']}**. Worker DONE signal `{row['done_signal_at']}`; dispatcher DONE `{row['done_at']}`; Issue closure `{row['issue_closed_at']}`. These are three distinct observations.\n\n"
        summary+='| Verdict sequence | Outcome | Directed report groups | Source |\n|---|---|---|---|\n'
        for c in [c for c in cycles if c['biu']==biu]: summary+=f"| {c['cycle']} | {c['outcome']} | {c['repair_finding_groups']} | [report]({c['report_url']}) |\n"
        summary+='\nCounts are report-local groups, not unique defects; ACCEPT closes blocking obligations, not every non-blocking observation. Detailed incidents, corrections and proof limitations: [closure reconciliation](../wave1-evidence-reconciliation.md).\n'
        (E/f'execution-trajectories/{biu}-summary.md').write_text(summary)
        (E/f'quality/{biu}-quality-evidence.md').write_text(summary.replace('terminal execution trajectory','terminal Quality Evidence').replace('../wave1-evidence-reconciliation.md','../wave1-evidence-reconciliation.md')+f'\nMachine-readable measurement: [{biu}-quality-evidence.json]({biu}-quality-evidence.json). Prior measurements are retained in `superseded_measurement`, excluded from current aggregates.\n')
    table='| BIU / Issue | Final state | Rejections | Verdicts / cycles | First-pass | Tests |\n|---|---|---:|---:|---|---:|\n'
    for r in rows: table+=f"| [{r['biu_id']} #{r['issue_number']}]({r['issue_url']}) | {r['final_lifecycle_state']} / {r['issue_state']} | {r['verifier_rejections']} | {r['verifier_verdicts']} / {r['execution_cycles']} | {r['first_pass_accepted']} | {r['test_count_at_landing']} |\n"
    manifest=f'# Wave 1 Closure Manifest\n\nAuthority: the Founder-directed Phase 0 + Phase 1 evidence reconciliation; governing lifecycle remains Project Status under SWF-31. This manifest freezes the observed terminal boundary; it issues no new work verdict.\n\n**Wave 1 terminal SHA: `{TERMINAL}`.** This is PY-10 landing, not the later evidence-publication commit. All eleven accepted candidates are retained ancestors. Final dispatcher DONE: `{rows[-1]["done_at"]}`; final Issue closure: `{rows[-1]["issue_closed_at"]}`. Capture: `{source["capture"]["captured_at"]}`.\n\n'+table
    manifest+='\n## Boundary and totals\n\n11 executed BIUs; **2 first-pass accepted (PY-09B and PY-10)**; **33 combined verifier rejections**; 44 formal verdicts / reconstructed execution cycles. PY-01 through PY-08: **0/8** first-pass; PY-01 through PY-09: **0/9**. No causal conclusion is made.\n\nAll eleven Project items are DONE and Issues CLOSED. No remaining member is release-eligible. Runtime active map is empty for this population; all recorded resource entries have exitedAt and none of their PIDs exists at capture. A retained worktree resource label RUNNING is not a running invocation. Runtime-managed branches/worktrees remain governed by SWF-30, not this evidence task.\n\nKnown capacity interruptions: 2 execution incidents (PY-03 closure, PY-09 producer); Agent-Ready provider failover is separately recorded. FOUNDER_EXCEPTION totals below count protocol markers, not a claim that each required new authority. Control-plane incidents and inserted/replanned work: see [reconciliation](wave1-evidence-reconciliation.md). PY-09B is the sole inserted Wave 1 BIU, authorized by SWF-33; PY-10 was replanned before release.\n\n## Per-BIU authority, identity and timestamps\n\n'
    for r in rows:
        manifest+=f"### {r['biu_id']} — {r['title'].split(' — ',1)[-1]}\n\n"
        manifest+=f"- Issue: [{r['issue_number']}]({r['issue_url']}); Project item `{r['project_item']}`; final **{r['final_lifecycle_state']} / {r['issue_state']}**.\n- Requirements (contract extent): {json.dumps(r['requirements'],ensure_ascii=False)}. {r['requirement_note']}\n- Declared predecessors: {', '.join(r['dependencies']) or 'none'}. Native blocked-by read-back: {', '.join(r['native_blocked_by']) or 'empty'}.\n- Agent-Ready: **{r['agent_ready']['disposition']}**, rework locality {r['agent_ready']['expected_rework_locality']}.\n- Accepted candidate: `{r['accepted_candidate']}`; merge: `{r['merge_commit']}`.\n- Combined verifier rejections: {r['verifier_rejections']}; FOUNDER_EXCEPTION markers: {r['founder_exception_markers']}.\n- ACCEPT marker: `{r['accepted_at']}`; DONE marker: `{r['done_signal_at']}`; dispatcher DONE: `{r['done_at']}`; Issue closure: `{r['issue_closed_at']}`.\n- Evidence: [ACCEPT]({r['evidence_refs'][1]}), [closure]({r['evidence_refs'][2]}), [trajectory](execution-trajectories/{r['biu_id']}.jsonl), [Quality Evidence](quality/{r['biu_id']}-quality-evidence.json).\n\n"
    manifest+='## Verification and limitations\n\n[Machine-readable manifest](wave1-closure-manifest.json), [retained source observations](wave1-source-observations.json), [consistency report](wave1-consistency-report.md), [yield snapshot](wave1-yield-snapshot.md). Requirements retain their scoped contribution: this is not full Product Requirement completion or Python Sovereignty. UNKNOWN telemetry is not zero. No Wave 2 design, learning consolidation or implementation is authorized by this record.\n'
    manifest+='\nAuthority qualification: PY-09B/PY-10 Claude producer use is corroborated, but an extension of the PY-09-only recovery authorization is UNKNOWN. See [late-arriving evidence](wave1-evidence-reconciliation.md#late-arriving-participant-evidence-and-provider-authority-qualification). This manifest does not ratify operational authority.\n'
    (E/'wave1-closure-manifest.md').write_text(manifest)
    distribution=dict(sorted(collections.Counter(r['verifier_rejections'] for r in rows).items()))
    yielddoc='# Wave 1 final yield snapshot\n\nFACTS only; no causal attribution or learning consolidation. Supersedes interim yield tables at the terminal boundary.\n\n'+table
    yielddoc+=f"\n- Executed: 11; first-pass accepted: 2/11 (18.18%). **PY-09B first-pass accepted; PY-10 first-pass accepted.**\n- Earlier eight (PY-01…PY-08): 0/8; earlier nine including PY-09: 0/9.\n- Combined verifier rejections: 33; distribution (rejections: BIU count): `{distribution}`.\n- Repair-return distribution is the same; execution cycles = 1 + repair returns: `{dict(sorted(collections.Counter(r['execution_cycles'] for r in rows).items()))}`. Same-phase retries and provider failover excluded.\n- Python suite growth at accepted milestones: {' → '.join(str(r['test_count_at_landing']) for r in rows)}; net +338 from PY-01. These are historical verifier/closure observations, not fresh reruns of eleven revisions.\n- FOUNDER_EXCEPTION protocol markers: {sum(r['founder_exception_markers'] for r in rows)}; not equivalent to genuine authority gaps.\n- Known execution provider-capacity interruptions: 2 (PY-03 closure, PY-09 IMPLEMENT); Agent-Ready quota/failover episode separately scoped. Complete provider interruption telemetry: UNKNOWN.\n- Known regressions: PY-04 lost proof; PY-08 behavioral/proof regressions reported in its trajectory. A globally deduplicated defect/regression total is UNKNOWN.\n- Inserted/split BIUs: PY-09B inserted from PY-10 by SWF-33; 1 inserted, no renumbering.\n- Control-plane incidents: dropped delivery/liveness gap (PY-06); attention activation and release admission (PY-06/07/08); stale Issue projection (PY-06/07); PY-09 no-verdict, duplicate attention identity and false recovery alarm. Incident taxonomy/deduplicated global total UNKNOWN.\n- UNKNOWN: end-to-end tokens/cost, per-invocation model attribution, unique defects across carried findings, escaped defects, REVIEW-versus-VERIFY attribution, complete historical transition timestamps.\n\nSources and limitations: [manifest](wave1-closure-manifest.md), [reconciliation](wave1-evidence-reconciliation.md), [repair records](wave1-repair-cycles.json).\n"
    yielddoc+='\nAuthority qualification: the two first-pass BIUs used Claude after the PY-09-only recovery; a durable extension of that authorization is UNKNOWN. This does not change their observed verdict histories. See the reconciliation.\n'
    (E/'wave1-yield-snapshot.md').write_text(yielddoc)
    comparison='# Wave 1 cross-BIU comparison — terminal\n\nFACT: terminal identity/state and counts below derive from the source-backed trajectory. INFERENCE: no cross-BIU causal relation is asserted. HYPOTHESIS: none tested in this phase. Historical interpretations remain explicitly superseded for terminal aggregation.\n\n'+table
    comparison+='\n| BIU | Purpose | Agent-Ready / locality | Directed report groups by verdict | Time to DONE (s) |\n|---|---|---|---|---:|\n'
    for r in rows: comparison+=f"| {r['biu_id']} | {r['title'].split(' — ',1)[-1]} | {r['agent_ready']['disposition']} / {r['agent_ready']['expected_rework_locality']} | {' → '.join(map(str,GROUPS[r['biu_id']]))} | {r['elapsed_to_done_seconds']} |\n"
    comparison+='\nTime starts at the release authorization comment, except PY-01, PY-02 and PY-03 where first retained producer allocation is the available lower-bound origin. These are not comparable full release-to-DONE windows. Exact lifecycle release times not supplied by sources remain UNKNOWN. Groups are per-report occurrences; do not sum them as unique findings. Candidate/merge identities, Founder markers and timestamps are in the manifest. Detailed behavioral/proof classifications and regressions remain in historical trajectories with their source references; their globally deduplicated totals are UNKNOWN. Durable recorded observations, not new lessons: [reconciliation](../wave1-evidence-reconciliation.md).\n'
    (E/'quality/wave1-cross-biu-comparison.md').write_text(comparison)
    (E/'wave1-repair-cycles.md').write_text('# Wave 1 repair-cycle data — terminal\n\nSupersedes the interim PY-02…PY-09 extraction at `'+TERMINAL+'`. The previous records remain in `superseded_records` in [JSON](wave1-repair-cycles.json); they are not execution cycles.\n\n'+table+'\nThe current 44 records are independent verifier verdicts: 33 REJECT + 11 ACCEPT. `cycle` is the reconstructed verification/execution pass; FOUNDER_EXCEPTION, provider interruptions and same-phase retries are not verdict records.\n\n`repair_finding_groups` counts directed report finding groups, retaining grouping rather than counting mentions or expanding subpoints. `findings_total` and unique findings are UNKNOWN when no complete source count exists. ACCEPT supports zero blocking groups under the verifier contract, not zero open non-blocking observations. Carried groups count as per-cycle occurrences only.\n\nCorrections and source-specific definitions: [reconciliation](wave1-evidence-reconciliation.md). Regenerate offline with `rtk proxy python3 tools/evidence/reconcile_wave1.py --write`; verify with `rtk proxy python3 tools/evidence/check_wave1.py`.\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--write',action='store_true'); args=parser.parse_args()
    if args.write: generate(read(SOURCE)); print('Generated Wave 1 terminal evidence for 11 BIUs')
    else: print('Use --write to regenerate terminal evidence from retained source observations.')
