"""Event-driven offline factory coordinator for the PY-04 walking skeleton."""
from __future__ import annotations
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Iterable
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore, verify_in_fresh_process
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.domain.lifecycle import ExecutionState, LifecycleStage, transition
from alienintent.execution_coordination.domain.release import ReleaseRequest, ReleaseSource, admit_release
from alienintent.execution_coordination.domain.verdict import EvidenceDefinition, Observation, evaluate_verdict
from alienintent.execution_coordination.ports.operational_store import OperationalStore, ReservationRejected
from alienintent.execution_coordination.ports.work_management import ReadyWorkItem, WorkManagement
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerProvider

class StopReason(StrEnum):
    EXHAUSTED="eligible-backlog-exhausted"; BLOCKED="dependencies-or-authority-blocked"; CAPACITY_UNAVAILABLE="capacity-unavailable"; AWAITING_RELEASE="awaiting-explicit-release"; AUTHORITY_BLOCKED="authority-blocked"; FAILURE="worker-failure"
@dataclass(frozen=True)
class RunSummary: stop_reason: StopReason; dispatched: tuple[str, ...]

class FactoryCoordinator:
    def __init__(self, store: OperationalStore, work: WorkManagement, worker: WorkerProvider, artifacts: LocalArtifactStore, profile: str) -> None:
        self._store,self._work,self._worker,self._artifacts,self._profile=store,work,worker,artifacts,profile
        self._released:set[str]=set()
    def start(self, *, limit: int|None=None) -> RunSummary:
        items=self._work.import_ready_snapshot()
        if not self._recover(items): return RunSummary(StopReason.CAPACITY_UNAVAILABLE,())
        dispatched=[]
        while limit is None or len(dispatched)<limit:
            item=self._next_item(items)
            if item is None: return RunSummary(self._stop_reason(items),tuple(dispatched))
            result=self._run(item)
            if result is StopReason.AUTHORITY_BLOCKED:
                dispatched.append(item.identity)
                continue
            if result is not None: return RunSummary(result,tuple(dispatched))
            dispatched.append(item.identity)
        return RunSummary(StopReason.CAPACITY_UNAVAILABLE,tuple(dispatched))
    def release_and_start(self, identity:str)->RunSummary:
        version,existing=self._store.read_state(self._profile,self._release_aggregate(identity))
        if not existing: self._store.commit(self._profile,self._release_aggregate(identity),version,{"identity":identity,"source":ReleaseSource.EXPLICIT_HUMAN})
        self._released.add(identity); return self.start()
    def state(self, identity:str)->ExecutionState:
        _,raw=self._store.read_state(self._profile,self._aggregate(identity))
        if not raw: raise KeyError(identity)
        return self._decode(raw)
    def _next_item(self,items:Iterable[ReadyWorkItem])->ReadyWorkItem|None:
        candidates=[]
        for item in items:
            try: state=self.state(item.identity)
            except KeyError: state=ExecutionState.for_contract(item.contract)
            if state.stage is not LifecycleStage.DONE and not self._is_authority_blocked(item.identity) and all(self._is_done(d) for d in item.dependencies): candidates.append(item)
        eligible=[i for i in candidates if i.automatic_release or self._is_released(i.identity)]
        return min(eligible,key=lambda i:(i.priority is None,i.priority if i.priority is not None else 0,i.fifo),default=None)
    def _run(self,item:ReadyWorkItem)->StopReason|None:
        try:
            source=ReleaseSource.AUTOMATIC_POLICY if item.automatic_release else ReleaseSource.EXPLICIT_HUMAN
            admit_release({},ReleaseRequest(item.identity,item.contract,item.readiness_digest,frozenset(item.dependencies),frozenset({"python","filesystem","process-control"}),{d:1 for d in item.contract.budget_policy.required_dimensions},"offline-profile",source))
        except ValueError: return StopReason.AUTHORITY_BLOCKED
        self._work.propose_release(item)
        version,raw=self._store.read_state(self._profile,self._aggregate(item.identity))
        current=self._decode(raw) if raw else ExecutionState.for_contract(item.contract)
        current=replace(current,contract=item.contract)
        correlation=f"launch:{item.identity}:{version}"
        try: reservation=self._store.acquire(self._profile,"repository",item.repository,correlation)
        except ReservationRejected: return StopReason.CAPACITY_UNAVAILABLE
        read_back=False
        try:
            self._store.commit_with_effect(self._profile,self._aggregate(item.identity),version,self._encode(current),correlation,{"correlation":correlation,"work":item.identity})
            self._store.claim_effect(self._profile,correlation)
            outcome=self._worker.start(WorkerInvocation(item.identity,correlation),item.contract,frozenset(item.contract.required_capabilities),item.contract.budget_policy)
            self._store.confirm_effect(self._profile,correlation,f"outcome:{outcome.kind}")
            completed=self._completed_for_outcome(item,current,outcome)
            read_back=self._record_result(item,completed,correlation,outcome.kind)
            self._work.project_execution_state(item.identity,completed.stage)
            if outcome.kind=="authority-block": return StopReason.AUTHORITY_BLOCKED
            if outcome.kind not in {"success","rework"}: return StopReason.FAILURE
            return None
        finally:
            if read_back and not self._store.unresolved_effects(self._profile): self._store.release(self._profile,"repository",item.repository,correlation,reservation.fence)
    def _completed_for_outcome(self,item:ReadyWorkItem,current:ExecutionState,outcome:object)->ExecutionState:
        if getattr(outcome,"kind")!="success" or getattr(outcome,"candidate") is None: return current
        verified=verify_in_fresh_process(getattr(outcome,"candidate"))
        verified_state=transition(current,current.version,"verify",candidate=verified)
        reviewed=transition(verified_state,verified_state.version,"review")
        verdict=evaluate_verdict(EvidenceDefinition(frozenset(item.contract.required_evidence)),(Observation("artifact-verified",True,True),),worker_claimed_success=True)
        accepted=transition(reviewed,reviewed.version,"accept",verdict=verdict)
        return transition(accepted,accepted.version,"close",completed_closure_actions=frozenset(item.contract.required_closure_actions))
    def _record_result(self,item:ReadyWorkItem,state:ExecutionState,correlation:str,outcome:str)->bool:
        version,_=self._store.read_state(self._profile,self._aggregate(item.identity)); persisted=self._encode(state); persisted.update(correlation=correlation,outcome=outcome)
        self._store.commit(self._profile,self._aggregate(item.identity),version,persisted)
        _,read=self._store.read_state(self._profile,self._aggregate(item.identity)); return read.get("correlation")==correlation and read.get("outcome")==outcome
    def _recover(self,items:Iterable[ReadyWorkItem])->bool:
        by_identity={i.identity:i for i in items}
        for r in self._store.recovery_reservations(self._profile):
            if r.scope!="repository" or not r.owner.startswith("launch:"): return False
            try: _,identity,_=r.owner.rsplit(":",2)
            except ValueError: return False
            item=by_identity.get(identity)
            if not item: return False
            outcome=self._worker.read_back(WorkerInvocation(identity,r.owner))
            if outcome is None: return False
            try: self._store.confirm_effect(self._profile,r.owner,f"outcome:{outcome.kind}")
            except ReservationRejected: return False
            version,raw=self._store.read_state(self._profile,self._aggregate(identity)); current=self._decode(raw) if raw else ExecutionState.for_contract(item.contract); current=replace(current,contract=item.contract)
            completed=self._completed_for_outcome(item,current,outcome)
            if not self._record_result(item,completed,r.owner,outcome.kind): return False
            self._store.release(self._profile,r.scope,r.key,r.owner,r.fence); self._work.project_execution_state(identity,completed.stage)
        return True
    def _is_done(self,identity:str)->bool:
        try:return self.state(identity).stage is LifecycleStage.DONE
        except KeyError:return False
    def _stop_reason(self,items:Iterable[ReadyWorkItem])->StopReason:
        pending=[i for i in items if not self._is_done(i.identity)]
        if not pending:return StopReason.EXHAUSTED
        if any(not i.automatic_release and not self._is_released(i.identity) for i in pending):return StopReason.AWAITING_RELEASE
        if any(self._is_authority_blocked(i.identity) for i in pending): return StopReason.AUTHORITY_BLOCKED
        return StopReason.BLOCKED
    def _is_authority_blocked(self, identity: str) -> bool:
        _, raw = self._store.read_state(self._profile, self._aggregate(identity))
        return raw.get("outcome") == "authority-block"
    def _is_released(self,identity:str)->bool:
        if identity in self._released:return True
        _,raw=self._store.read_state(self._profile,self._release_aggregate(identity)); return raw.get("identity")==identity and raw.get("source")==ReleaseSource.EXPLICIT_HUMAN
    @staticmethod
    def _aggregate(identity:str)->str:return f"factory:{identity}"
    @staticmethod
    def _release_aggregate(identity:str)->str:return f"release:{identity}"
    @staticmethod
    def _encode(state:ExecutionState)->dict[str,object]:
        c=state.candidate; candidate=None if c is None else {"kind":c.kind,"identity":c.identity,"digest":c.content_digest,"locator":c.locator,"provenance":c.provenance,"read_back":c.independent_read_back_proven}
        return {"stage":state.stage,"version":state.version,"accepted":state.accepted,"closure":sorted(state.completed_closure_actions),"candidate":candidate}
    @staticmethod
    def _decode(raw:dict[str,object])->ExecutionState:
        c=raw.get("candidate"); candidate=None
        if isinstance(c,dict):candidate=CandidateRef(CandidateKind(str(c["kind"])),str(c["identity"]),str(c["digest"]),str(c["locator"]),str(c["provenance"]),bool(c["read_back"]))
        return ExecutionState(LifecycleStage(str(raw["stage"])),int(raw["version"]),candidate,bool(raw["accepted"]),frozenset(raw["closure"]),None)
