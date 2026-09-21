#!/usr/bin/env python3
"""Fail-closed consistency checks for the retained Wave 1 closure evidence.

Checks evidence consistency, not product acceptance. No external mutation.
--negative-controls corrupts in-memory copies only and requires each to fail.
"""
import argparse
import copy
import datetime as dt
import json
from pathlib import Path
import re
import subprocess
import sys

import jsonschema

ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'docs/evidence'
EXPECTED={2:'PY-01',50:'PY-02',51:'PY-03',52:'PY-04',53:'PY-05',54:'PY-06',55:'PY-07',56:'PY-08',57:'PY-09',68:'PY-09B',58:'PY-10'}
MARKER=re.compile(r'<!-- B-DISP: INVOCATION=(AlienLogicLab/alienintent#(\d+):(PRODUCER|VERIFIER):[a-f0-9-]+) (RESULT|CONTROL)=([A-Z_]+) -->')
def read(path): return json.loads(path.read_text())
def load():
    manifest=read(E/'wave1-closure-manifest.json')
    return {'manifest':manifest,'source':read(E/'wave1-source-observations.json'),'repairs':read(E/'wave1-repair-cycles.json'),'quality':{b:read(E/f'quality/{b}-quality-evidence.json') for b in EXPECTED.values()},'trajectories':{b:[json.loads(s) for s in (E/f'execution-trajectories/{b}.jsonl').read_text().splitlines() if s] for b in EXPECTED.values()}}
def date(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
def git_ok(*args): return subprocess.run(['rtk','proxy','git',*args],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def check(data, ancestry=True):
    errors=[]; checked=[]
    def require(condition,label):
        checked.append(label)
        if not condition: errors.append(label)
    manifest=data['manifest']; source=data['source']; rows=manifest['bius']
    issues={x['number']:x for x in source['issues']}
    require({r['issue_number']:r['biu_id'] for r in rows}==EXPECTED,'exact population and Issue mapping')
    require(len(rows)==11,'eleven distinct manifest rows')
    require(manifest['terminal_sha']==source['terminal_sha']=='10cc81620511af56befbb6140504d1991bb02846','fixed terminal boundary')
    projects=source['project']['data']['organization']['projectV2']
    require(projects['id']=='PVT_kwDOEcrpC84Bj5i_' and not projects['items']['pageInfo']['hasNextPage'],'production Project identity and complete page')
    items={x['content']['number']:x for x in projects['items']['nodes'] if x.get('content') and 'number' in x['content']}
    require(not source['runtime']['active_wave1'],'no active Wave 1 lane at capture')
    require(not source['runtime']['recorded_worker_pids_still_present'],'no retained worker PID exists at capture')
    require(all(r['exitedAt'] for r in source['runtime']['resources']),'all captured Wave 1 resources exited')
    schemas={k:jsonschema.Draft202012Validator(read(E/f'schema/{k}-v1.schema.json'),format_checker=jsonschema.FormatChecker()) for k in ['execution-trajectory','quality-evidence']}
    for row in rows:
        b=row['biu_id']; n=row['issue_number']; issue=issues[n]; q=data['quality'][b]
        signals=[]
        for c in issue['comments']:
            for m in MARKER.finditer(c['body']):
                if int(m[2])==n: signals.append((c,m[1],m[3],m[4],m[5]))
        verdicts=[s for s in signals if s[2]=='VERIFIER' and s[4] in ['REJECT','ACCEPT']]
        rejections=[s for s in verdicts if s[4]=='REJECT']; accepted=[s for s in verdicts if s[4]=='ACCEPT']
        require(len(accepted)==1,b+' exactly one independent ACCEPT')
        require(len({s[1] for s in verdicts})==len(verdicts),b+' distinct verifier invocation identities')
        require(row['title']==issue['title'] and b in issue['title'],b+' Issue title mapping')
        require(row['native_blocked_by']==[EXPECTED[x['number']] for x in issue['dependencies']],b+' native dependency observation')
        require(all(d in EXPECTED.values() for d in row['dependencies']),b+' declared dependencies resolve')
        item=items[n]; state=next(x['name'] for x in item['fieldValues']['nodes'] if x.get('field',{}).get('name')=='Status')
        require(row['project_item']==item['id'] and row['final_lifecycle_state']==state=='DONE',b+' Project lifecycle fact')
        require(row['issue_state']==issue['state'].upper()=='CLOSED',b+' Issue closure fact')
        require(row['verifier_rejections']==q['verifier_rejections']==len(rejections),b+' rejection count reconciles to markers')
        require(row['verifier_verdicts']==q['verifier_cycles']==len(verdicts),b+' verdict count reconciles to markers')
        require(row['execution_cycles']==q['execution_cycles']==1+len(rejections),b+' cycle count excludes retries and exceptions')
        require(not [s for s in signals if s[3]=='CONTROL' and s[4]=='RETURN_TO_IMPLEMENT'],b+' no additional ACCEPT rework cycle')
        require(row['first_pass_accepted']==q['first_pass_accepted']==(len(rejections)==0),b+' first-pass matches full verdict history')
        require(q['repair_cycles']==q['return_to_implement_count']==len(rejections),b+' repair returns distinct from attempts')
        require(row['founder_exception_markers']==sum(s[4]=='FOUNDER_EXCEPTION' for s in signals),b+' exception marker count')
        require(row['accepted_candidate'] in accepted[0][0]['body'],b+' accepted SHA named by verifier')
        closure=next(x for x in source['runtime']['closures'] if x['item']['issue']==n and x['result']=='DONE')
        require(row['done_at']==q['done_at']==closure['completedAt'],b+' DONE uses dispatcher completedAt')
        require(row['done_signal_at']==q['done_signal_at']==closure['signalEvidence']['createdAt'],b+' worker signal distinct from lifecycle completion')
        require(row['issue_closed_at']==q['issue_closed_at']==issue['closed_at'],b+' Issue closure remains separate')
        require(date(row['accepted_at'])<=date(row['done_signal_at'])<=date(row['done_at'])<=date(row['issue_closed_at']),b+' acceptance/signal/DONE/closure chronology')
        require(q['elapsed_to_done_seconds']['value']==row['elapsed_to_done_seconds']==round((date(row['done_at'])-date(row['timing_origin'])).total_seconds(),3),b+' elapsed time reconciles')
        require(q['accepted_candidate']==row['accepted_candidate'] and q['merge_commit']==row['merge_commit'],b+' Quality Evidence identities')
        require(q['token_usage']==q['cost']==q['unique_findings']=='UNKNOWN',b+' UNKNOWN end-to-end telemetry never zero')
        require(q['extraction_status']['value']=='TERMINAL' and q['done'] and q['landed'] and q['final_verdict']=='ACCEPT',b+' terminal disposition')
        require(q['test_count_at_landing']==row['test_count_at_landing'],b+' final test observation')
        current=[e for e in data['trajectories'][b] if e.get('reconciliation')=='wave1-terminal']
        legacy=[e for e in data['trajectories'][b] if e.get('reconciliation')!='wave1-terminal']
        require(all(e.get('superseded_for_terminal_aggregation_by')=='wave1-terminal' for e in legacy),b+' historical records explicitly superseded')
        require(len([e for e in current if e['event_type']=='VERIFICATION_REJECTED'])==len(rejections),b+' trajectory rejections')
        require(len([e for e in current if e['event_type']=='VERIFICATION_ACCEPTED'])==1,b+' trajectory acceptance')
        require(next(e['terminal'] for e in current if e['event_type']=='TERMINAL_RECONCILIATION')==row,b+' trajectory terminal projection')
        require(len({e['event_id'] for e in data['trajectories'][b]})==len(data['trajectories'][b]),b+' event ids unique')
        for obj in data['trajectories'][b]:
            require(not list(schemas['execution-trajectory'].iter_errors(obj)),b+' v1 trajectory event '+obj['event_id'])
        require(not list(schemas['quality-evidence'].iter_errors(q)),b+' v1 Quality Evidence schema')
        cycle_rows=[c for c in data['repairs']['records'] if c['biu']==b]
        require(len(cycle_rows)==len(verdicts),b+' repair rows cover all verdicts')
        require([c['repair_finding_groups'] for c in cycle_rows]==q['repair_finding_groups_by_verdict'],b+' finding groups reconcile against Quality Evidence')
        for i,(cycle,v) in enumerate(zip(cycle_rows,verdicts),1):
            require(cycle['report_url']==v[0]['url'] and cycle['invocation_id']==v[1] and cycle['outcome']==v[4] and cycle['reported_at']==v[0]['created_at'],b+f' cycle {i} source verdict identity')
            require(cycle['cycle']==cycle['execution_cycle']==i,b+f' cycle {i} ordinal')
            require(cycle['unique_findings']==cycle['findings_total']=='UNKNOWN',b+f' cycle {i} UNKNOWN unique/all findings')
            if cycle['outcome']=='ACCEPT':
                require(cycle['acceptance_blockers']==0,b+' accepted blocking obligations discharged (not all findings zero)')
                require(cycle['tests_passed']==row['test_count_at_landing'] and re.search(r'\b'+str(cycle['tests_passed'])+r' passed\b',v[0]['body']) is not None,b+' final Python test count cited in independent report')
            match=next(e for e in current if e.get('invocation_id')==v[1] and e['event_type'].startswith('VERIFICATION_'))
            require(match['repair_finding_groups']==cycle['repair_finding_groups'],b+f' cycle {i} trajectory finding groups')
        if ancestry:
            require(git_ok('cat-file','-e',row['merge_commit']+'^{commit}'),b+' merge exists')
            require(git_ok('merge-base','--is-ancestor',row['accepted_candidate'],row['merge_commit']),b+' candidate reachable from stated merge')
            require(git_ok('merge-base','--is-ancestor',row['merge_commit'],manifest['terminal_sha']),b+' merge within terminal boundary')
            require(git_ok('merge-base','--is-ancestor',row['accepted_candidate'],'origin/main'),b+' candidate reachable from refreshed origin/main')
    missing_identity=next(c for c in data['repairs']['records'] if c['report_url'].endswith('5749643685'))
    require(missing_identity['candidate']=='UNKNOWN' and missing_identity['presumptive_reviewed_tree']=='f95199e6698dcb6b3858ae5e169a30a7fb130fd2','PY-04 presumptive tree is not identified candidate')
    py08=next(c for c in data['repairs']['records'] if c['report_url'].endswith('5753874359'))
    require(py08['explicitly_open_ids']==['Y2','Y4','Y7','Y8','Z1'] and py08['explicitly_open_count']==5 and py08['decisive_unmet_ac_groups']==2 and py08['directed_repair_ids']==['Y2','Y4','Z1'],'PY-08 corrected disjoint finding metrics')
    report=next(c['body'] for c in issues[56]['comments'] if c['id']==5753874359)
    require(all(re.search(r'\*\*'+s+r'\b',report) for s in py08['explicitly_open_ids']),'PY-08 all five IDs appear in verifier report')
    for n,prefixes in [(54,['F','G','H','J'])]:
        reports=[c for c in issues[n]['comments'] if 'RESULT=REJECT -->' in c['body'] and ':VERIFIER:' in c['body']]
        rows54=[c for c in data['repairs']['records'] if c['issue']==n and c['outcome']=='REJECT']
        for c,p,r in zip(reports,prefixes,rows54):
            actual=len(set(re.findall(r'^### ('+p+r'\d+)\b',c['body'],re.M)))
            require(r['repair_finding_groups']==actual,'PY-06 headed groups '+p+' reconcile to report headings')
    py09=[e for e in data['trajectories']['PY-09'] if e.get('reconciliation')=='wave1-terminal']
    for kind in ['INVOCATION_CAPACITY_FAILED','VERIFIER_NO_VERDICT','PROVIDER_FAILOVER_RECORDED']:
        matching=[e for e in py09 if e['event_type']==kind]
        require(len(matching)==1 and matching[0]['execution_cycle']==4,'PY-09 '+kind+' stays cycle 4')
    require(not any('e84d12a0' in c['invocation_id'] or 'f5ca7bab' in c['invocation_id'] for c in data['repairs']['records']),'no-result attempts absent from verifier verdict rows')
    for b,expected in [('PY-09B',['NEEDS_CLARIFICATION','NEEDS_CLARIFICATION','READY']),('PY-10',['BLOCKED','SPLIT_RECOMMENDED','READY'])]:
        require([e['result'] for e in data['trajectories'][b] if e.get('reconciliation')=='wave1-terminal' and e['event_type']=='READINESS_ASSESSMENT_RECORDED']==expected,b+' separate assessment history')
    preflight=[e for e in data['trajectories']['PY-09B'] if e.get('reconciliation')=='wave1-terminal' and e['event_type']=='PREFLIGHT_OBSERVED']
    require([e['result'] for e in preflight]==['PASS','FAIL','PASS'],'three-state permission preflight not flattened')
    sb=source['sandbox_project']['data']['organization']['projectV2']
    require(sb['id']=='PVT_kwDOEcrpC84BkIEX' and not sb['items']['pageInfo']['hasNextPage'],'sandbox Project identity and complete page')
    sbitems=[x for x in sb['items']['nodes'] if x.get('content',{}).get('title','').startswith('SB-')]
    require(len(sbitems)==6 and all(any(v.get('name')=='DONE' and v.get('field',{}).get('name')=='Status' for v in x['fieldValues']['nodes']) for x in sbitems),'six live sandbox BIUs DONE')
    remote=source['sandbox_remote']; candidates=[x for x in remote['branches'] if x['name'].startswith('candidate/')]
    require(len(candidates)==6 and len(remote['branches'])==7,'six candidates plus main, not seven candidates')
    proof=read(E/'py10/proof-run.json')
    require({x['sha'] for x in candidates}=={x['revision'] for x in proof['after']['candidates']},'live refs match retained run candidate identities')
    require(len(remote['comparisons'])==6 and all(x['ahead_by']==1 and x['behind_by']==0 and len(x['files'])==1 for x in remote['comparisons']),'live candidates one commit ahead, no duplicate published effects')
    require(sum(r['first_pass_accepted'] for r in rows)==2 and sum(r['verifier_rejections'] for r in rows)==33,'yield totals')
    return errors,checked

def negative_controls(data):
    mutants={
      'derived rejection count':lambda d:d['manifest']['bius'][0].update(verifier_rejections=0),
      'UNKNOWN to zero':lambda d:d['quality']['PY-10'].update(cost=0),
      'impossible chronology':lambda d:d['manifest']['bius'][-1].update(done_at='2020-01-01T00:00:00Z'),
      'Issue mismatch':lambda d:d['manifest']['bius'][-1].update(title='PY-09'),
      'false first-pass':lambda d:d['quality']['PY-09'].update(first_pass_accepted=True),
      'provider failure counted as repair':lambda d:d['quality']['PY-09'].update(repair_cycles=4),
      'retry increments cycle':lambda d:d['quality']['PY-09'].update(execution_cycles=5),
      'fabricated finding count':lambda d:d['repairs']['records'][-1].update(repair_finding_groups=99),
      'Issue closure conflated with DONE':lambda d:d['manifest']['bius'][-1].update(done_at=d['manifest']['bius'][-1]['issue_closed_at']),
      'seventh candidate':lambda d:d['source']['sandbox_remote']['branches'].append({'name':'candidate/extra','sha':'0'*40}),
      'nonexistent merge':lambda d:d['manifest']['bius'][-1].update(merge_commit='0'*40),
      'unreachable accepted candidate':lambda d:d['manifest']['bius'][-1].update(accepted_candidate='0'*40),
      'supersession removed':lambda d:d['trajectories']['PY-09'][0].pop('superseded_for_terminal_aggregation_by',None),
    }
    result=[]
    for name,mutate in mutants.items():
        damaged=copy.deepcopy(data); mutate(damaged)
        errors,_=check(damaged,ancestry=name in ['nonexistent merge','unreachable accepted candidate'])
        expected_git_failure={'nonexistent merge':'PY-10 merge exists','unreachable accepted candidate':'PY-10 candidate reachable from stated merge'}.get(name)
        killed=bool(errors) and (expected_git_failure is None or expected_git_failure in errors)
        result.append({'violation':name,'result':'KILLED' if killed else 'SURVIVED','failed_checks':errors})
    return result

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--negative-controls',action='store_true');parser.add_argument('--report',action='store_true');args=parser.parse_args()
    data=load(); errors,checks=check(data)
    negative=negative_controls(data) if args.negative_controls else []
    survived=[n for n in negative if n['result']!='KILLED']
    report={'ok':not errors and not survived,'checks':len(checks),'failures':errors,'negative_controls':negative,'scope':'Offline consistency against retained GitHub/runtime source capture and current Git objects/origin refs; not a fresh product verdict or re-execution of live proof.'}
    if args.report:
        (E/'wave1-consistency-report.json').write_text(json.dumps(report,indent=2)+'\n')
        (E/'wave1-consistency-report.md').write_text('# Wave 1 deterministic consistency report\n\n'+f"Result: **{'PASS' if report['ok'] else 'FAIL'}**. {len(checks)} checks; {len(errors)} failures. Negative controls: {len(negative)-len(survived)}/{len(negative)} killed.\n\nCommand: `rtk proxy python3 tools/evidence/check_wave1.py --negative-controls --report`.\n\n"+report['scope']+'\n\nCovers population/mapping, complete Project pages, source verdict counts, candidate/merge ancestry, timestamp semantics/order, cycle/attempt separation, first-pass status, UNKNOWN preservation, source/trajectory/quality reconciliation, historical supersession, v1 terminal schema validity, readiness/preflight history and sandbox remote custody.\n\nFinding-group semantics are a source-cited human classification; the checker validates their propagation and directly recounts PY-06 headed IDs. It does not claim to mechanically interpret arbitrary verifier prose. Historical schema/time ambiguities are disclosed in [reconciliation](wave1-evidence-reconciliation.md).\n\n'+ '\n'.join('- '+n['violation']+': '+n['result'] for n in negative)+'\n\nFull discriminating failure reasons: [JSON](wave1-consistency-report.json).\n')
    print(json.dumps({'ok':report['ok'],'checks':len(checks),'failures':errors,'negative_controls_killed':len(negative)-len(survived),'negative_controls_total':len(negative)},indent=2))
    return 0 if report['ok'] else 1
if __name__=='__main__': sys.exit(main())
