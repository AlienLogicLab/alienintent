from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tests.context_assembly.test_design_admission import DesignAdmissionTests, contract, review, KEY, PROJECT, PROFILE
from alienintent.context_assembly.application.design_admission_service import DesignAdmission, DesignReadiness
from alienintent.context_assembly.domain.design_admission import ReviewAdmitted, ReviewRefused, Stale
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
f=DesignAdmissionTests();f.setUp()
try:
 p=f.profile();a=p.design;r=a.inspect(contract(),0);old=review(r)
 assert isinstance(a.record_review(KEY,old,1),ReviewAdmitted)
 assert isinstance(a.check(KEY,{**deepcopy(r.vector),'requirements':{KEY:'sha256:'+'b'*64}}),Stale)
 path=f.state/'state'
 b=DesignAdmission(LocalEvidenceRepository(path/'evidence',PROJECT,PROFILE),SQLiteOperationalStore(path/'operational.sqlite'),a.project,a.profile,a.definition_ref,'JC-reopened-process',a.access_scope,a.architecture,a.premises,a.authority,a.reviewers)
 assert isinstance(b.check(KEY,r.vector),Stale)
 again=b.inspect(contract(),3)
 altered=deepcopy(old);altered['authority']='same authorized role, different serialization'
 refusal=b.record_review(KEY,altered,4)
 assert isinstance(refusal,ReviewRefused) and refusal.reason_code=='REVIEW_NOT_FRESH',refusal
 assert not DesignReadiness(b).admit(KEY,again.vector).admitted
 assert isinstance(b.record_review(KEY,review(again,reviewer=('JC','fresh-after-reopen')),5),ReviewAdmitted)
 assert DesignReadiness(b).admit(KEY,again.vector).admitted
 assert b.retained(b.history(KEY)[1][1])['review']==old
 print('PASS: reopened store retains invalidation, altered historical review is refused, fresh review admits, prior verdict retained')
finally:f.doCleanups()
