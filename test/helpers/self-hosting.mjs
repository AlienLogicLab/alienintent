import { chmodSync, cpSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { generateKeyPairSync } from 'node:crypto';
import { join } from 'node:path';

// All authority responses below are deterministic local fixtures, never GitHub.
export function setupRehearsal(directory, source, port) {
  const git = (...args) => execFileSync('git', args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
  const store = join(directory, 'canonical');
  git('clone', '--no-hardlinks', '--no-local', source, store);
  git('-C', store, 'remote', 'set-url', 'origin', 'https://github.com/ExampleOrg/sample-project.git');
  // Commit candidate production bytes into the disposable canonical fixture so
  // uncommitted in-scope fixes are covered without changing the real repository.
  for (const path of ['bin', 'src', 'scripts', 'config']) {
    rmSync(join(store, path), { recursive: true, force: true });
    cpSync(join(source, path), join(store, path), { recursive: true });
  }
  git('-C', store, 'add', 'bin', 'src', 'scripts', 'config');
  git('-C', store, '-c', 'user.name=Synthetic Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--allow-empty', '-m', 'test: snapshot candidate production bytes');
  const baseline = git('-C', store, 'rev-parse', 'HEAD');
  git('-C', store, 'update-ref', 'refs/remotes/origin/main', baseline);
  const database = join(directory, 'github.json');
  writeFileSync(database, JSON.stringify({ status: 'REVIEW', comments: [], transitions: [] }));
  const common = `
import { readFileSync,writeFileSync,renameSync,appendFileSync,existsSync } from 'node:fs';
const database=${JSON.stringify(database)};
const read=()=>JSON.parse(readFileSync(database,'utf8'));
const save=value=>{const path=database+'.'+process.pid;writeFileSync(path,JSON.stringify(value));renameSync(path,database)};
const project={number:1,owner:{login:'ExampleOrg'}};
const membership={nodes:[{id:'PVTI_selfhost',databaseId:1,project}],pageInfo:{hasNextPage:false}};
const fields={pageInfo:{hasNextPage:false},nodes:[{id:'status-field',name:'Status',options:['IMPLEMENT','VERIFY','REVIEW','ACCEPT','DONE'].map(name=>({id:name,name}))}]};
`;
  const transport = join(directory, 'transport.mjs');
  writeFileSync(transport, common + `
import childProcess from 'node:child_process';
import {syncBuiltinESMExports} from 'node:module';
const real=childProcess.execFileSync;
const permissions={issues:'read',metadata:'read',organization_projects:'write'}, events=['issue_comment','projects_v2_item'];
childProcess.execFileSync=(command,args,options)=>{
 const respond=value=>JSON.stringify(value);
 if(command===${JSON.stringify(join(directory, 'curl'))}){
  const endpoint=new URL(args[args.indexOf('--url')+1]).pathname;
  if(endpoint==='/app')return respond({id:1,slug:'rehearsal',owner:{login:'ExampleOrg'},permissions,events});
  if(endpoint==='/app/installations/2')return respond({id:2,app_id:1,account:{login:'ExampleOrg'},target_type:'Organization',repository_selection:'selected',permissions,events});
  if(endpoint==='/app/installations/2/access_tokens')return respond({token:'synthetic-token',expires_at:new Date(Date.now()+3600000).toISOString(),permissions});
  throw Error('unexpected offline curl endpoint '+endpoint);
 }
 if(command!==${JSON.stringify(join(directory, 'gh'))})return real(command,args,options);
 if(args[1]==='/installation/repositories')return respond({total_count:1,repositories:[{full_name:'ExampleOrg/sample-project'}]});
 if(args[1]==='repos/ExampleOrg/sample-project/issues/1/comments')return respond(args.includes('--slurp')?[read().comments]:read().comments);
 const query=args.find(arg=>arg.startsWith('query='))??'';
 if(query.includes('viewerCanUpdate'))return respond({data:{viewer:{login:'rehearsal[bot]'},repository:{nameWithOwner:'ExampleOrg/sample-project',issues:{nodes:[]}},organization:{projectV2:{id:'project',viewerCanUpdate:true,fields}}}});
 if(query.includes('items(first:'))return respond({data:{organization:{projectV2:{items:{pageInfo:{hasNextPage:false},nodes:[{id:'PVTI_selfhost',content:{__typename:'Issue',number:1,repository:{nameWithOwner:'ExampleOrg/sample-project'}},fieldValues:{pageInfo:{hasNextPage:false},nodes:[{name:read().status,field:{name:'Status'}}]}}]}}}}});
 if(query.includes('fieldValueByName'))return respond({data:{node:{id:'PVTI_selfhost',project,content:{__typename:'Issue',number:1,repository:{nameWithOwner:'ExampleOrg/sample-project'}},fieldValueByName:{name:read().status}}}});
 if(query.includes('projectItems('))return query.includes('node(id:')?respond({data:{node:{number:1,repository:{nameWithOwner:'ExampleOrg/sample-project'},projectItems:membership}}}):respond({data:{repository:{issue:{projectItems:membership}}}});
 if(query.includes('updateProjectV2ItemFieldValue')){const value=read();value.status=args.find(arg=>arg.startsWith('optionId=')).slice(9);value.transitions.push(value.status);save(value);return respond({data:{updateProjectV2ItemFieldValue:{projectV2Item:{id:'PVTI_selfhost'}}}})}
 if(query.includes('fields(first:'))return respond({data:{organization:{projectV2:{id:'project',fields}}}});
 throw Error('unexpected offline gh request '+JSON.stringify(args));
};
syncBuiltinESMExports();
`);
  const gh = join(directory, 'gh');
  writeFileSync(gh, `#!${process.execPath}\nconst args=process.argv.slice(2).join(' ');const login=process.env.GH_CONFIG_DIR.endsWith('producer-gh')?'producer-bot':'verifier-bot';if(args.includes('api user'))console.log(login);else if(args.includes('repos/ExampleOrg/sample-project'))console.log('ExampleOrg/sample-project');else if(args.includes('viewerCanUpdate'))console.log('true');else if(args.includes('graphql'))console.log('WRITE');else process.exit(23);\n`);
  chmodSync(gh, 0o755);
  const provider = join(directory, 'provider.mjs');
  writeFileSync(provider, `#!${process.execPath}\n` + common + `
import {execFileSync} from 'node:child_process';
const prompt=process.argv.at(-1), invocationId=prompt.match(/Invocation ID: ([^ ]+)\\./)[1];
const role=invocationId.includes(':VERIFIER:')?'VERIFIER':'PRODUCER';
const phase=prompt.includes('post-ACCEPT closure')?'ACCEPT':role==='VERIFIER'?'VERIFY':'IMPLEMENT';
const git=(...args)=>execFileSync('/usr/bin/git',args,{encoding:'utf8'}).trim();
if(!existsSync('src/runtime/dispatcher.mjs'))throw Error('B-DISP source missing');
const evidence={invocationId,role,phase,cwd:process.cwd(),gitName:git('config','user.name'),gitEmail:git('config','user.email'),home:process.env.HOME,ghConfig:process.env.GH_CONFIG_DIR,tokenPresent:!!process.env.GH_TOKEN};
appendFileSync(${JSON.stringify(join(directory, 'launches.jsonl'))},JSON.stringify(evidence)+'\\n');
while(!existsSync(${JSON.stringify(directory)}+'/release-'+phase))await new Promise(resolve=>setTimeout(resolve,20));
let commit;
if(phase==='IMPLEMENT'){
 writeFileSync('self-hosting-rehearsal.txt','bounded synthetic B-DISP artifact\\n');git('add','self-hosting-rehearsal.txt');git('commit','-m','test: synthetic self-hosting artifact');commit=git('rev-parse','HEAD');
 writeFileSync(${JSON.stringify(join(directory, 'candidate.json'))},JSON.stringify({commit,invocationId}));
}else{
 const producer=read().comments.find(comment=>comment.user.login==='producer-bot'&&comment.body.includes(' RESULT=VERIFY -->'));
 commit=producer?.body.match(/Synthetic evidence commit ([a-f0-9]{40,64});/)?.[1];
 if(!commit)throw Error('durable producer evidence missing');
 if(phase==='ACCEPT'&&!read().comments.some(comment=>comment.user.login==='verifier-bot'&&comment.body.includes(' RESULT=ACCEPT -->')&&comment.body.includes(commit)))throw Error('durable verifier acceptance missing');
 if(git('show',commit+':self-hosting-rehearsal.txt')!=='bounded synthetic B-DISP artifact')throw Error('artifact verification failed');
 if(git('rev-parse','HEAD')===commit)throw Error('independent checkout was not isolated');
}
const result=phase==='IMPLEMENT'?'VERIFY':phase==='VERIFY'?'ACCEPT':'DONE';
const data=read();data.comments.push({id:data.comments.length+1,created_at:new Date().toISOString(),user:{login:role==='VERIFIER'?'verifier-bot':'producer-bot'},body:'Synthetic evidence commit '+commit+'; deployment/publication outside this offline rehearsal. <!-- B-DISP: INVOCATION='+invocationId+' RESULT='+result+' -->'});save(data);
console.log(JSON.stringify({synthetic:true,phase,commit,invocationId}));
while(!existsSync(${JSON.stringify(directory)}+'/exit-'+phase))await new Promise(resolve=>setTimeout(resolve,20));
`);
  chmodSync(provider, 0o755);
  const profile = JSON.parse(readFileSync(join(source, 'config/profile.example.json'), 'utf8'));
  profile.execution.enabled = true;
  profile.webhook.listenPort = port;
  profile.webhook.secretFile = join(directory, 'secret'); writeFileSync(profile.webhook.secretFile, 'synthetic-webhook-secret');
  profile.githubApp.privateKeyPath = join(directory, 'key.pem');
  writeFileSync(profile.githubApp.privateKeyPath, generateKeyPairSync('rsa', { modulusLength: 2048 }).privateKey.export({type:'pkcs8',format:'pem'}), {mode:0o600});
  profile.paths = {stateFile:join(directory,'state','state.json'),workerLogDirectory:join(directory,'logs'),repositoryStore:store,worktreeRoot:join(directory,'worktrees')};
  profile.executables = {node:process.execPath,githubCli:gh,curl:join(directory,'curl'),processInspector:'/usr/bin/ps',git:'/usr/bin/git',preflight:join(store,'scripts/worker-preflight')};
  profile.environment.executableSearchPath = '/usr/bin:/bin';
  for(const [role, worker] of Object.entries(profile.workers)) {
    const name=role.toLowerCase();
    worker.provider.adapter='codex';worker.provider.executablePath=provider;worker.provider.fundingProfile='provider-default';worker.provider.permissionMode='workspace-write';
    worker.provider.authenticationProfile.homeDirectory=join(directory,name+'-home');mkdirSync(worker.provider.authenticationProfile.homeDirectory);
    worker.githubAuthentication={configDirectory:join(directory,name+'-gh'),shimDirectory:join(directory,name+'-shim')};
  }
  const config=join(directory,'profile.json');writeFileSync(config,JSON.stringify(profile));
  return {config,transport,store,baseline,database,state:profile.paths.stateFile,launches:join(directory,'launches.jsonl')};
}
