import test from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { createServer } from 'node:net';
import { once } from 'node:events';
import { spawn, execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setupRehearsal } from './helpers/self-hosting.mjs';

const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(check, detail) {
  const deadline=Date.now()+15000;
  while(Date.now()<deadline){const value=await check();if(value)return value;await pause(25)}
  throw Error('Rehearsal timed out: '+detail());
}
async function unusedPort(){const server=createServer();server.listen(0,'127.0.0.1');await once(server,'listening');const port=server.address().port;await new Promise(resolve=>server.close(resolve));return port}

test('OFFLINE synthetic self-hosting rehearsal composes CLI, signed events, isolated Git workers, closure and restart', {timeout:60000}, async () => {
  const directory=mkdtempSync(join(tmpdir(),'b-disp-self-hosting-'));
  let child, output='';
  const children=[];
  try {
    const source=fileURLToPath(new URL('..',import.meta.url));
    const port=await unusedPort();
    const fixture=setupRehearsal(directory,source,port);
    const read=path=>JSON.parse(readFileSync(path,'utf8'));
    const launches=()=>existsSync(fixture.launches)?readFileSync(fixture.launches,'utf8').trim().split('\n').filter(Boolean).map(JSON.parse):[];
    const diagnostic=()=>output+'\n'+(existsSync(fixture.state)?readFileSync(fixture.state,'utf8'):'no state');
    const start=()=>{
      child=spawn(process.execPath,['--import',fixture.transport,join(fixture.store,'bin/b-disp.mjs'),'--config',fixture.config], {env:{PATH:'/usr/bin:/bin',HOME:directory,LANG:'C.UTF-8'},stdio:['ignore','pipe','pipe']});
      children.push(child);
      child.stdout.on('data',data=>{output+=data});child.stderr.on('data',data=>{output+=data});
    };
    const stop=async()=>{const exited=once(child,'exit');child.kill('SIGTERM');await exited};
    let delivery=0;
    const post=async(event,payload,valid=true,id='rehearsal-'+(++delivery))=>{
      const body=JSON.stringify(payload);
      const signature=valid?'sha256='+createHmac('sha256','synthetic-webhook-secret').update(body).digest('hex'):'sha256=invalid';
      return fetch(`http://127.0.0.1:${port}`,{method:'POST',body,headers:{'x-github-event':event,'x-github-delivery':id,'x-hub-signature-256':signature}});
    };
    const statusEvent=status=>({action:'edited',organization:{login:'ExampleOrg'},sender:{type:'User',login:'project-operator'},projects_v2_item:{id:1,node_id:'PVTI_selfhost',content_node_id:'I_selfhost',updated_at:new Date().toISOString()},changes:{field_value:{field_name:'Status',to:status}}});
    const commentEvent=comment=>({action:'created',repository:{full_name:'ExampleOrg/sample-project'},issue:{number:1},comment});
    start();
    await until(async()=>{try{return (await post('ping',{},false)).status===401}catch{return false}},diagnostic);
    assert.equal(launches().length,0);
    // A rejected signed-body check must not admit work or record a delivery.
    assert.equal((await post('projects_v2_item',statusEvent('IMPLEMENT'),false,'bad-signature')).status,401);
    assert.equal(launches().length,0);
    const initial=read(fixture.database);initial.status='IMPLEMENT';writeFileSync(fixture.database,JSON.stringify(initial));
    const implement=statusEvent('IMPLEMENT');
    assert.equal((await post('projects_v2_item',implement,true,'implement-delivery')).status,202);
    await until(()=>launches().length===1,diagnostic);
    const producer=launches()[0];
    assert.equal(producer.phase,'IMPLEMENT');
    const wrong={id:900,created_at:new Date().toISOString(),user:{login:'producer-bot'},body:'<!-- B-DISP: INVOCATION=not-the-active-invocation RESULT=VERIFY -->'};
    assert.equal((await post('issue_comment',commentEvent(wrong))).status,202);
    assert.equal(read(fixture.database).status,'IMPLEMENT');
    assert.ok(existsSync(producer.cwd));
    assert.equal(Object.values(read(fixture.state).resources)[0].lifecycle,'RUNNING');

    for(const [index,phase,target] of [[0,'IMPLEMENT','VERIFY'],[1,'VERIFY','ACCEPT'],[2,'ACCEPT','DONE']]){
      await until(()=>launches().length===index+1,diagnostic);
      const invocation=launches()[index];assert.equal(invocation.phase,phase);
      writeFileSync(join(directory,'release-'+phase),'release');
      await until(()=>read(fixture.database).comments.length===index+1,diagnostic);
      const comment=read(fixture.database).comments[index];
      assert.ok(comment.body.includes('INVOCATION='+invocation.invocationId+' RESULT='+target));
      // The signed comment routes the durable result while its process still owns cwd.
      assert.equal((await post('issue_comment',commentEvent(comment),true,'result-'+index)).status,202);
      await until(()=>read(fixture.database).status===target,diagnostic);
      assert.ok(existsSync(invocation.cwd));
      assert.equal(read(fixture.state).resources[invocation.invocationId].lifecycle,'RUNNING');
      writeFileSync(join(directory,'exit-'+phase),'exit');
      await until(()=>Object.values(read(fixture.state).resources).filter(resource=>resource.lifecycle==='REMOVED').length===index+1,diagnostic);
      if(target!=='DONE')assert.equal((await post('projects_v2_item',statusEvent(target))).status,202);
    }
    const all=launches(), state=read(fixture.state), github=read(fixture.database);
    assert.equal(all.length,3);
    assert.equal(new Set(all.map(worker=>worker.cwd)).size,3);
    assert.deepEqual(all.map(worker=>worker.role),['PRODUCER','VERIFIER','PRODUCER']);
    assert.deepEqual(github.transitions,['VERIFY','ACCEPT','DONE']);
    assert.deepEqual(state.active,{});
    assert.equal(state.deliveries['bad-signature'],undefined);
    assert.equal(Object.values(state.closures).length,1);
    assert.equal(Object.values(state.closures)[0].result,'DONE');
    for(const worker of all){
      assert.equal(worker.tokenPresent,false);
      assert.notEqual(worker.cwd,fixture.store);
      assert.equal(existsSync(worker.cwd),false);
      const resource=state.resources[worker.invocationId];
      assert.equal(resource.lifecycle,'REMOVED');
      const log=readFileSync(resource.logPath,'utf8');assert.match(log,/"synthetic":true/);assert.ok(log.includes(worker.invocationId));
      assert.equal(resource.baselineCommit,fixture.baseline);
    }
    assert.notEqual(all[0].gitName,all[1].gitName);
    assert.notEqual(all[0].gitEmail,all[1].gitEmail);
    assert.notEqual(all[0].home,all[1].home);
    assert.notEqual(all[0].ghConfig,all[1].ghConfig);
    const candidate=read(join(directory,'candidate.json'));
    assert.equal(execFileSync('git',['-C',fixture.store,'show',candidate.commit+':self-hosting-rehearsal.txt'],{encoding:'utf8'}),'bounded synthetic B-DISP artifact\n');
    const retained=execFileSync('git',['-C',fixture.store,'worktree','list','--porcelain'],{encoding:'utf8'});
    assert.equal((retained.match(/^worktree /gm)??[]).length,1);
    await stop();
    start();
    await until(async()=>{try{return (await post('ping',{},false)).status===401}catch{return false}},diagnostic);
    assert.equal((await post('projects_v2_item',implement,true,'implement-delivery')).status,202);
    assert.equal((await post('issue_comment',commentEvent(github.comments[0]),true,'result-0')).status,202);
    assert.equal(launches().length,3);
    assert.equal(read(fixture.database).status,'DONE');
    assert.deepEqual(read(fixture.database).transitions,['VERIFY','ACCEPT','DONE']);
    assert.deepEqual(read(fixture.state).resources,state.resources);
    await stop();
    assert.doesNotMatch(output,/PREFLIGHT_FAILED|WORKER_TECHNICAL_FAILURE|WORKTREE_CLEANUP_FAILED/);
  } finally {
    // Release fixture waits and stop owned CLI processes before deleting fixture state.
    for(const phase of ['IMPLEMENT','VERIFY','ACCEPT'])for(const prefix of ['release-','exit-'])writeFileSync(join(directory,prefix+phase),'cleanup');
    await pause(100);
    const statePath=join(directory,'state','state.json');
    const resources=existsSync(statePath)?Object.values(JSON.parse(readFileSync(statePath,'utf8')).resources??{}):[];
    const ownsFixture=pid=>{try{return readFileSync(`/proc/${pid}/cmdline`,'utf8').split('\0').includes(join(directory,'provider.mjs'))}catch{return false}};
    for(const resource of resources)if(Number.isInteger(resource.pid)&&ownsFixture(resource.pid)){
      process.kill(resource.pid,'SIGKILL');
      await until(()=>!ownsFixture(resource.pid),()=>`fixture provider ${resource.pid} did not exit`);
    }
    for(const owned of children)if(owned.exitCode===null&&owned.signalCode===null){const exited=once(owned,'exit');owned.kill('SIGKILL');await exited;}
    rmSync(directory,{recursive:true,force:true});
  }
});
