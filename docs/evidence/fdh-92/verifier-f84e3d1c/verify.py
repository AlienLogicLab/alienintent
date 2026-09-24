import pathlib, subprocess, tempfile, shutil, json
root=pathlib.Path.cwd()
ev=root/'docs/evidence/fdh-92/verifier-f84e3d1c'
ev.mkdir(exist_ok=True)
results=[]
def run(name,cmd,cwd=root):
    with (ev/(name+'.txt')).open('w') as f:
        f.write('COMMAND: '+cmd+'\n'); f.flush()
        r=subprocess.run(cmd,shell=True,cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
        f.write('\nEXIT: '+str(r.returncode)+'\n')
    results.append(dict(name=name,command=cmd,exit=r.returncode))
    (ev/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(name, r.returncode, flush=True)
with tempfile.TemporaryDirectory(prefix='fdh92-jc-') as tmp:
    tmp=pathlib.Path(tmp)
    for name,ref in [('baseline','0eda915'),('eq','93e4e7e'),('suppress','93e4e7e')]:
        dest=tmp/name;dest.mkdir()
        archive=subprocess.run(['rtk','proxy','git','archive',ref],stdout=subprocess.PIPE,check=True).stdout
        subprocess.run(['rtk','proxy','tar','-x','-C',str(dest)],input=archive,check=True)
    t='tools/orchestration/'
    for f in ['test_factory_director_inputs.py','test_factory_director_host.py']:
        shutil.copyfile(root/t/f,tmp/'baseline'/t/f)
    for name,file,old,new in [('eq','factory_director_inputs.py','wip_intentionally_full=runtime.claims >= wip_limit,','wip_intentionally_full=runtime.claims == wip_limit,'),('suppress','factory_director_host.py','if values.wip_intentionally_full and not values.director_only_control():','if values.wip_intentionally_full:')]:
        p=tmp/name/t/file;s=p.read_text();assert s.count(old)==1;p.write_text(s.replace(old,new))
        diff=subprocess.run(['rtk','proxy','diff','-u',str(root/t/file),str(p)],capture_output=True,text=True)
        (ev/(name+'-variant.diff')).write_text(diff.stdout)
    ac12=' '.join(t+x for x in ['test_factory_director_inputs.py::test_wip_intentionally_full','test_factory_director_inputs.py::test_overlap_with_only_worker_work_pending_idles_wip_intentionally_full','test_factory_director_inputs.py::test_overlap_with_no_control_required_idles_wip_intentionally_full','test_factory_director_host.py::test_claims_above_the_wip_limit_idle_as_wip_intentionally_full'])
    ac3=' '.join(t+x for x in ['test_factory_director_inputs.py::test_overlap_never_suppresses_director_only_control','test_factory_director_host.py::test_claims_above_the_wip_limit_never_suppress_director_only_control'])
    pytest='rtk proxy python3 -m pytest -q -p no:cacheprovider -rfE '
    for name,variant,tests in [('baseline-ac12','baseline',ac12),('baseline-ac3','baseline',ac3),('eq-ac12','eq',ac12),('suppress-ac3','suppress',ac3)]:run(name,pytest+tests,tmp/variant)
    run('candidate-targeted',pytest+ac12+' '+ac3)
    run('candidate-fdh-suites',pytest+' '.join(t+f for f in ['test_factory_director_inputs.py','test_factory_director_host.py','test_factory_director_docs.py']))
    run('candidate-check-all','rtk proxy node scripts/check.mjs all')
    run('candidate-pytest-tools',pytest+'tools')
    # Restore baseline tests before comparing the full unmodified baseline suite.
    for f in ['test_factory_director_inputs.py','test_factory_director_host.py']:
        (tmp/'baseline'/t/f).write_bytes(subprocess.run(['rtk','proxy','git','show','0eda915:'+t+f],capture_output=True,check=True).stdout)
    baseline_git=tmp/'baseline-git'
    subprocess.run(['rtk','proxy','git','worktree','add','--detach',str(baseline_git),'0eda915'],check=True)
    try:
        run('baseline-pytest-tools',pytest+'tools',baseline_git)
    finally:
        subprocess.run(['rtk','proxy','git','worktree','remove',str(baseline_git)],check=True)
