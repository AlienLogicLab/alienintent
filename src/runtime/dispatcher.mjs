import { existsSync, readFileSync, writeFileSync, renameSync, rmSync } from "node:fs";
import crypto from "node:crypto";
import { inspectWorker, workerLogPath } from "./worker-runner.mjs";
import { isAbsolute } from "node:path";
import { allowedSignals, parseInvocationSignal } from "../github/authority.mjs";
const defaultRoleNames = { PRODUCER: "PRODUCER", VERIFIER: "VERIFIER" };

const routedSignal = claim => claim?.control ?? claim?.result;
const recoverable = outcome => ["COMPLETION_ERROR", "DURABLE_RESULT_MISSING", "WORKER_IDENTITY_MISMATCH"].includes(outcome);
function workerBootstrap(role, item, invocationId, status, roleNames, workerDisplayNames = {}) {
  const displayName = workerDisplayNames[role] ?? (role === roleNames.PRODUCER ? "PRODUCER" : "VERIFIER");
  const verifierName = workerDisplayNames[roleNames.VERIFIER] ?? "VERIFIER";
  const context = `Read AGENTS.md. Repository: ${item.repository}. GitHub Issue #${item.issue}. Invocation ID: ${invocationId}. Worker: ${displayName}.`;
  if (role === roleNames.PRODUCER && status === "ACCEPT") return `${context} Handle post-ACCEPT closure using the accepted result and durable assignment authority. Leave the Project item in ACCEPT during execution and any authority block; only the dispatcher updates its status. Account for landing/merge, deployment/publication, live operational verification and every remaining required action. Perform authorized actions and document evidence for any action that is unnecessary. Signal DONE only when all required actions are completed or shown unnecessary, with no known remaining work. Mechanical closure needs no additional ${verifierName} review. Publish one terminal Issue comment with supporting evidence and either <!-- B-DISP: INVOCATION=${invocationId} RESULT=DONE --> or <!-- B-DISP: INVOCATION=${invocationId} RESULT=FOUNDER_EXCEPTION -->. Explain the specific authority needed for FOUNDER_EXCEPTION; ACCEPT remains unchanged. A material implementation change invalidates the old acceptance: preserve its evidence, publish <!-- B-DISP: INVOCATION=${invocationId} CONTROL=RETURN_TO_IMPLEMENT --> without a terminal RESULT, and stop. Do not implement the change under the prior acceptance. The dispatcher returns the work to IMPLEMENT, followed by VERIFY and independent review. stdout and chat cannot supply a workflow result.`;
  const allowed = role === roleNames.PRODUCER ? ["VERIFY", "FOUNDER_EXCEPTION"] : ["ACCEPT", "REJECT", "FOUNDER_EXCEPTION"];
  const review = role === roleNames.VERIFIER ? "Independently reconstruct the review context" : "Reconstruct the task context";
  const markers = allowed.map((result) => `<!-- B-DISP: INVOCATION=${invocationId} RESULT=${result} -->`).join(" or ");
  return `${context} ${review} from durable Issue and repository evidence, then complete the bounded assignment. Use that durable assignment as the source of execution authority. Carry out repository and GitHub changes that it authorizes. Changes to another repository require explicit authorization in the durable task. Only the exact invocation marker communicates a workflow RESULT; it does not narrow the execution authority of the assignment. Finish by publishing exactly one GitHub Issue comment containing ${markers}. stdout and chat cannot supply a workflow result.`;
}
export function verifyWebhookSignature(secret, rawBody, signature) { if (!secret || !signature?.startsWith("sha256=")) return false; const expected = Buffer.from(`sha256=${crypto.createHmac("sha256", secret).update(rawBody).digest("hex")}`); const received = Buffer.from(signature); return expected.length === received.length && crypto.timingSafeEqual(expected, received); }
export class EventRelay {
  constructor(options) { this.options = options; this.roleNames = options.roleNames ?? defaultRoleNames; this.roles = { IMPLEMENT: this.roleNames.PRODUCER, VERIFY: this.roleNames.VERIFIER, ACCEPT: this.roleNames.PRODUCER }; this.active = new Map(); this.started = false; this.stopped = false; this.routing = new Map(); this.metrics = { projectLists: 0 }; this._events = []; }
  isClosure(claim) { return claim?.role === this.roleNames.PRODUCER && claim.status === "ACCEPT"; }
  configuredWorkerLogin(role) { return this.options.workerLogins?.[role] ?? this.options.authority.workerLogins?.[role]; }
  assertActiveConfiguration() {
    if (this.options.requireExecutionControls && !this.options.executionControls) throw new Error("EXECUTION_CONFORMANCE_REQUIRED");
    this.assertResourcePaths();
    const roles = new Set(Object.values(this.roleNames));
    for (const [lane, claim] of Object.entries(this.state().active ?? {})) {
      // Unrelated malformed legacy records have no recoverable role identity.
      if (!/#[1-9][0-9]*:[^:]+$/.test(lane) && claim.role === undefined) continue;
      const laneRole = lane.slice(lane.lastIndexOf(":") + 1);
      if (!roles.has(laneRole) || (claim.role !== undefined && claim.role !== laneRole)) throw new Error("ACTIVE_ROLE_CONFIGURATION_MISMATCH");
      if (claim.workerLogin !== undefined && claim.workerLogin !== this.configuredWorkerLogin(laneRole)) throw new Error("ACTIVE_WORKER_IDENTITY_CONFIGURATION_MISMATCH");
    }
  }
  assertResourcePaths() {
    const seen = new Set();
    for (const resource of Object.values(this.state().resources ?? {})) {
      if (!isAbsolute(resource.path ?? "") || seen.has(resource.path)) throw new Error("WORKTREE_PATH_COLLISION_OR_INVALID");
      seen.add(resource.path);
    }
  }
  allocateResource(active) {
    const manager = this.options.worktreeManager;
    if (!manager) return;
    const worker = this.options.workers?.[active.role];
    const record = manager.plan({ invocationId: active.invocationId, item: active.item, role: active.role });
    const state = this.state();
    if (record.invocationId !== active.invocationId || record.repository !== active.item.repository
        || record.issue !== active.item.issue || record.role !== active.role || !isAbsolute(record.path ?? "")
        || Object.values(state.resources ?? {}).some(other => other.path === record.path)) throw new Error("WORKTREE_PATH_COLLISION_OR_INVALID");
    state.resources ??= {};
    state.resources[active.invocationId] = { ...record, logPath: workerLogPath(active.invocationId, worker.logDirectory) };
    state.active[active.lane].worktree = record.path;
    active.worktree = record.path;
    this.save(state); // Allocation intent survives a crash in Git.
    const allocated = manager.allocate(record, worker);
    if (allocated.path !== record.path || allocated.invocationId !== record.invocationId) throw new Error("WORKTREE_OWNERSHIP_CHANGED");
    const updated = this.state();
    updated.resources[active.invocationId] = { ...updated.resources[active.invocationId], ...allocated };
    this.save(updated);
  }
  updateResource(invocationId, changes) {
    const state = this.state();
    if (!state.resources?.[invocationId]) return;
    Object.assign(state.resources[invocationId], changes); this.save(state);
  }
  ownedWorkAlive(claim) {
    const resource = this.state().resources?.[claim.invocationId];
    if (!resource?.supervision) return this.processAlive(claim.pid);
    try {
      if (!this.options.launch.observe) throw new Error("SUPERVISION_OBSERVER_REQUIRED");
      const observation = this.options.launch.observe(resource, supervision => this.updateResource(claim.invocationId, { supervision }));
      if (observation.terminal) this.updateResource(claim.invocationId, { exitedAt: resource.exitedAt ?? new Date(this.now()).toISOString() });
      return !observation.terminal;
    } catch (error) {
      this.updateResource(claim.invocationId, { supervisionDiagnostic: error.message });
      this.emit({ invocationId: claim.invocationId, outcome: "SUPERVISION_HOLD", error: error.message });
      return true;
    }
  }
  reconcileResources() {
    if (!this.options.worktreeManager) return;
    this.assertResourcePaths();
    for (const invocationId of Object.keys(this.state().resources ?? {})) {
      const state = this.state(), resource = state.resources[invocationId];
      if (resource.lifecycle === "REMOVED" || this.active.has(invocationId)
          || Object.values(state.active).some(claim => claim.invocationId === invocationId)) continue;
      if (resource.supervision && this.ownedWorkAlive(resource)) continue;
      // PID reuse can cause conservative retention; permission errors are unknown.
      // A crash between spawn and PID persistence must never authorize deletion.
      if (!resource.supervision && !resource.exitedAt && !["ALLOCATING", "READY"].includes(resource.lifecycle)) {
        if (!Number.isInteger(resource.pid) || resource.pid <= 0) continue;
        if (this.options.isProcessAlive) { if (this.options.isProcessAlive(resource.pid)) continue; }
        else { try { process.kill(resource.pid, 0); continue; } catch (error) { if (error.code !== "ESRCH") continue; } }
      }
      const diagnostic = Object.values(state.diagnostics ?? {}).find(claim => claim.invocationId === invocationId);
      if (diagnostic && ["COMPLETION_ERROR", "DURABLE_RESULT_MISSING", "WORKER_IDENTITY_MISMATCH", "WORKER_TECHNICAL_FAILURE"].includes(diagnostic.outcome)
          && !resource.admissionFailed) continue;
      try {
        const cleaned = this.options.worktreeManager.cleanup(resource);
        this.updateResource(invocationId, { ...cleaned, cleanupDiagnostic: null });
        this.emit({ invocationId, outcome: "WORKTREE_REMOVED" });
      } catch (error) {
        this.updateResource(invocationId, { cleanupDiagnostic: error.message });
        this.emit({ invocationId, outcome: "WORKTREE_CLEANUP_FAILED", error: error.message });
      }
    }
  }
  state() { return existsSync(this.options.statePath) ? JSON.parse(readFileSync(this.options.statePath, "utf8")) : { deliveries: {}, active: {} }; }
  save(state) {
    const temporary = `${this.options.statePath}.${process.pid}.${crypto.randomUUID()}.tmp`;
    try {
      writeFileSync(temporary, `${JSON.stringify(state, null, 2)}\n`, { mode: 0o600 });
      renameSync(temporary, this.options.statePath);
    } finally { rmSync(temporary, { force: true }); }
  }
  get events() { return this._events; } emit(event) { const record = { at: new Date().toISOString(), ...event }; this._events.push(record); this.options.onEvent?.(record); }
  lane(item, role) { return `${item.repository}#${item.issue}:${role}`; } invocation(item, role) { return `${this.lane(item, role)}:${crypto.randomUUID()}`; }
  budgetKey(item) { return `${item.repository}#${item.issue}`; }
  reservePhaseAttempt(item, role, status) { const c = this.options.executionControls; if (!c || status === "ACCEPT") return true; const state = this.state(); state.executionBudgets ??= {}; const budget = state.executionBudgets[this.budgetKey(item)] ??= { cycle: 1, phases: {} }; const phase = `${budget.cycle}:${status}:${role}`, launches = budget.phases[phase] ?? 0; if (launches && launches - 1 >= c.replacements.value) return false; budget.phases[phase] = launches + 1; this.save(state); return true; }
  reserveNextCycle(item, state) { const c = this.options.executionControls; if (!c) return true; state.executionBudgets ??= {}; const budget = state.executionBudgets[this.budgetKey(item)] ??= { cycle: 1, phases: {} }; if (budget.cycle >= c.attempts.value) return false; budget.cycle += 1; return true; }
  biuKey(item) { return `${item.repository}#${item.issue}`; }
  limitFor(item) {
    const limit = this.options.biuLimits?.[this.biuKey(item)];
    if (!limit) return null;
    if (!Number.isSafeInteger(limit.maxCycles) || limit.maxCycles < 1
        || !Number.isSafeInteger(limit.maxReplacementsPerPhase) || limit.maxReplacementsPerPhase < 0) throw new Error("BIU_LIMIT_CONFIGURATION_INVALID");
    return limit;
  }
  limitState(state, item, phase) {
    const key = this.biuKey(item);
    state.executionLimits ??= {};
    state.executionLimits[key] ??= { cycle: 1, phase, phaseInvocations: [] };
    return state.executionLimits[key];
  }
  limitHold(state, item, outcome, details) {
    const key = this.biuKey(item);
    state.limitEscalations ??= {};
    const previous = state.limitEscalations[key];
    if (!previous || (outcome === "EXECUTION_CYCLE_LIMIT" && previous.outcome !== outcome)) {
      state.limitEscalations[key] = { outcome, biu: key, ...details, at: new Date(this.now()).toISOString(), ...(previous ? { prior: previous } : {}) };
    }
    this.save(state);
    this.emit({ issue: item.issue, outcome, biu: key, ...details });
  }
  target(role, result) { if (role === this.roleNames.PRODUCER && result === "VERIFY") return "VERIFY"; if (role === this.roleNames.VERIFIER && result === "REJECT") return "IMPLEMENT"; if (role === this.roleNames.VERIFIER && result === "ACCEPT") return "ACCEPT"; return null; }
  processAlive(pid) { if (!Number.isInteger(pid) || pid <= 0) return false; if (this.options.isProcessAlive) return this.options.isProcessAlive(pid); try { process.kill(pid, 0); return true; } catch { return false; } }
  authorizedOperator(sender) {
    if (sender?.type !== "User" || typeof sender.login !== "string") return false;
    const login = sender.login.toLowerCase();
    return !login.endsWith("[bot]") && login !== this.options.appIdentity?.toLowerCase()
      && !Object.values(this.roleNames).some(role => this.configuredWorkerLogin(role)?.toLowerCase() === login)
      && (this.options.authorizedOperatorLogins ?? []).some(value => value.toLowerCase() === login);
  }
  eventStatus(payload) { const change = payload?.changes?.field_value; if (payload?.action !== "edited" || change?.field_name !== "Status") return null; const value = typeof change.to === "string" ? change.to : change.to?.name; return typeof value === "string" ? value.toUpperCase() : null; }
  async acceptEvent({ headers, payload }) {
    this.assertActiveConfiguration();
    if (!headers["x-github-delivery"]) return { accepted: false, reason: "UNSUPPORTED_EVENT" };
    if (headers["x-github-event"] === "issue_comment") return this.acceptResultComment(headers["x-github-delivery"], payload);
    if (headers["x-github-event"] !== "projects_v2_item") return { accepted: false, reason: "UNSUPPORTED_EVENT" };
    if (payload?.organization?.login && this.options.projectOwner && payload.organization.login !== this.options.projectOwner) return { accepted: false, reason: "WRONG_ORGANIZATION" };
    const status = this.eventStatus(payload), role = this.roles[status]; if (!role || !payload?.projects_v2_item?.content_node_id || !payload.projects_v2_item.id) return { accepted: false, reason: "IRRELEVANT" };
    const state = this.state(), delivery = headers["x-github-delivery"]; if (state.deliveries[delivery]) return { accepted: true, duplicate: true }; state.deliveries[delivery] = { state: "PROCESSING", at: new Date().toISOString() }; this.save(state);
    try { const identity = await this.options.authority.enrichContentNode(payload.projects_v2_item.content_node_id, payload.projects_v2_item.node_id ?? payload.projects_v2_item.id); if (!identity?.repository || !Number.isInteger(identity.issue) || !identity.itemId) { this.emit({ outcome: "CONTENT_ENRICHMENT_FAILED" }); } else await this.start(identity, role, status, undefined, payload); const processed = this.state(); processed.deliveries[delivery] = { state: "PROCESSED", at: new Date().toISOString() }; this.save(processed); return { accepted: true }; }
    catch (error) { const retryable = this.state(); delete retryable.deliveries[delivery]; this.save(retryable); throw error; }
  }
  async acceptResultComment(delivery, payload) {
    if (payload?.action !== "created") return { accepted: false, reason: "UNSUPPORTED_ACTION" };
    const state = this.state(); if (state.deliveries[delivery]) return { accepted: true, duplicate: true }; state.deliveries[delivery] = { state: "PROCESSING", at: new Date().toISOString() }; this.save(state);
    try {
      const repository = payload?.repository?.full_name, issue = payload?.issue?.number, body = payload?.comment?.body, author = payload?.comment?.user?.login;
      const snapshot = this.state();
      const claims = Object.entries(snapshot.active).map(([lane, claim]) => ({ lane, ...claim }));
      // A delayed created webhook may finish the latest failed invocation, but
      // never an older invocation after a successor has taken the lane.
      for (const [lane, diagnostic] of Object.entries(snapshot.diagnostics ?? {})) {
        if (!snapshot.active[lane] && ["DURABLE_RESULT_MISSING", "COMPLETION_ERROR", "WORKER_IDENTITY_MISMATCH"].includes(diagnostic.outcome)) claims.push({ ...diagnostic, lane, recovered: true });
      }
      const claim = claims.find(candidate => candidate.item?.repository === repository && candidate.item.issue === issue && parseInvocationSignal(body, candidate, this.roleNames));
      const signal = claim && parseInvocationSignal(body, claim, this.roleNames);
      const timestampValid = !payload?.comment?.created_at || Math.floor(Date.parse(payload.comment.created_at) / 1000) >= Math.floor(Date.parse(claim?.startedAt) / 1000);
      const expectedLogin = this.options.workerLogins?.[claim?.role] ?? this.options.authority.workerLogins?.[claim?.role];
      if (claim?.workerLogin !== undefined && claim.workerLogin !== expectedLogin) throw new Error("ACTIVE_WORKER_IDENTITY_CONFIGURATION_MISMATCH");
      if (claim && (typeof expectedLogin !== "string" || !expectedLogin.trim() || author !== expectedLogin)) this.diagnostic(claim, "WORKER_IDENTITY_MISMATCH", { evidence: { commentId: payload.comment.id, author: author ?? null, expectedLogin: expectedLogin ?? null } });
      if (!repository || repository !== this.options.repository || !Number.isInteger(issue) || !claim || !signal || !timestampValid || typeof expectedLogin !== "string" || !expectedLogin.trim() || author !== expectedLogin) { this.emit({ issue, outcome: "INVALID_RESULT_COMMENT" }); }
      else {
        claim.signalEvidence = { commentId: payload.comment.id, createdAt: payload.comment.created_at, author };
        if (claim.recovered) {
          const current = this.state();
          current.active[claim.lane] = { ...claim };
          this.active.set(claim.invocationId, claim);
          this.save(current);
          try { await this.routeResult(claim, signal); }
          catch (error) { this.diagnostic(claim, "COMPLETION_ERROR", { error: error.message }); throw error; }
          finally {
            const completed = this.state().active[claim.lane];
            this.release(claim); this.active.delete(claim.invocationId);
            this.reconcileResources();
            if (completed && routedSignal(completed)) await this.resumeAfterClosure(completed);
          }
        } else await this.routeResult(claim, signal);
      }
      const processed = this.state(); processed.deliveries[delivery] = { state: "PROCESSED", at: new Date().toISOString() }; this.save(processed); return { accepted: true };
    } catch (error) { const retryable = this.state(); delete retryable.deliveries[delivery]; this.save(retryable); throw error; }
  }
  now() { return (this.options.now ?? Date.now)(); }
  diagnostic(claim, outcome, evidence = {}, pendingState) {
    const state = pendingState ?? this.state();
    const current = state.active[claim.lane] ?? state.diagnostics?.[claim.lane];
    if (current?.invocationId !== claim.invocationId) return;
    state.diagnostics ??= {};
    const previous = state.diagnostics[claim.lane];
    const consumed = previous?.invocationId === claim.invocationId && ["FOUNDER_EXCEPTION", "VERIFY_TO_VERIFY", "ACCEPT_TO_ACCEPT", "REJECT_TO_IMPLEMENT", "DONE_TO_DONE", "RETURN_TO_IMPLEMENT_TO_IMPLEMENT", "EXECUTION_CYCLE_LIMIT"].includes(previous.outcome);
    state.diagnostics[claim.lane] = { invocationId: claim.invocationId, item: claim.item, role: claim.role, status: claim.status, ...(current.workerLogin !== undefined ? { workerLogin: current.workerLogin } : {}), signalEvidence: current.signalEvidence ?? claim.signalEvidence, pendingSignal: current.pendingSignal, pendingStatus: current.pendingStatus, pendingOperatorEvent: current.pendingOperatorEvent, result: current.result, control: current.control, startedAt: claim.startedAt, at: new Date(this.now()).toISOString(), outcome: consumed ? previous.outcome : outcome, ...evidence };
    this.save(state);
    this.emit({ issue: claim.item.issue, role: claim.role, invocationId: claim.invocationId, outcome, ...evidence });
  }
  release(claim) {
    const state = this.state();
    if (state.active[claim.lane]?.invocationId === claim.invocationId) { delete state.active[claim.lane]; this.save(state); }
  }
  async routeResult(claim, result) {
    if (!allowedSignals(claim, this.roleNames).has(result)) return false;
    if (this.routing.has(claim.invocationId)) return this.routing.get(claim.invocationId);
    const pending = (async () => {
      const snapshot = this.state();
      if (snapshot.limitEscalations?.[this.biuKey(claim.item)]?.outcome === "EXECUTION_CYCLE_LIMIT") return false;
      const current = snapshot.active[claim.lane];
      if (current?.invocationId !== claim.invocationId || routedSignal(current)) return false;
      const item = await this.options.authority.resolveItem(claim.item);
      const resolved = this.state();
      if (resolved.active[claim.lane]?.invocationId !== claim.invocationId || routedSignal(resolved.active[claim.lane])) return false;
      claim.item = item;
      const target = this.isClosure(claim)
        ? (result === "DONE" ? "DONE" : result === "RETURN_TO_IMPLEMENT" ? "IMPLEMENT" : null)
        : this.target(claim.role, result);
      // Legacy non-closure markers imply a unique phase; do not write that
      // inference into historical records. Closure markers still require ACCEPT.
      const expectedStatus = claim.status ?? (claim.role === this.roleNames.VERIFIER ? "VERIFY" : "IMPLEMENT");
      const status = target ? await this.options.authority.currentStatus(item) : expectedStatus;
      // Only an already persisted intent can reconcile an interrupted mutation.
      // A fresh result at its target status is stale, not proof we moved it.
      const latest = this.state();
      const owned = latest.active[claim.lane];
      if (owned?.invocationId !== claim.invocationId || routedSignal(owned)) return false;
      if (owned.limitHold) return false;
      const intent = owned.pendingSignal;
      if (intent && (intent.value !== result || intent.target !== target)) return false;
      const confirmed = target && intent?.value === result && intent.target === target && status === target;
      owned.item = item;
      if (claim.signalEvidence) owned.signalEvidence = claim.signalEvidence;
      if (status !== expectedStatus && !confirmed) {
        this.diagnostic(claim, "STALE_RESULT", { rejectedSignal: result, expectedStatus, observedStatus: status }, latest);
        return false;
      }
      const limit = this.limitFor(item);
      if (limit && target) {
        const account = this.limitState(latest, item, expectedStatus);
        if (account.transitionInvocationId !== claim.invocationId && account.phase !== expectedStatus) throw new Error("BIU_LIMIT_PHASE_MISMATCH");
        if (account.transitionInvocationId !== claim.invocationId) {
          const nextCycle = target === "IMPLEMENT" && expectedStatus !== "IMPLEMENT" ? account.cycle + 1 : account.cycle;
          if (nextCycle > limit.maxCycles) {
            owned.limitHold = "EXECUTION_CYCLE_LIMIT";
            this.limitHold(latest, item, "EXECUTION_CYCLE_LIMIT", { cycle: account.cycle, maxCycles: limit.maxCycles, invocationId: claim.invocationId, rejectedSignal: result, phase: expectedStatus });
            this.diagnostic(claim, "EXECUTION_CYCLE_LIMIT", { rejectedSignal: result, cycle: account.cycle, maxCycles: limit.maxCycles });
            return false;
          }
          account.cycle = nextCycle;
          account.phase = target;
          account.phaseInvocations = [];
          account.transitionInvocationId = claim.invocationId;
        }
      }
      if (target === "IMPLEMENT" && !this.reserveNextCycle(item, latest)) { this.diagnostic(claim, "EXECUTION_CYCLE_CAP_REACHED", { cycleLimit: this.options.executionControls?.attempts?.value }, latest); return false; }
      if (target || this.isClosure(claim)) owned.pendingSignal ??= { value: result, target };
      this.save(latest);
      if (target && !confirmed) await this.options.authority.transition(item, target);
      const state = this.state();
      if (state.active[claim.lane]?.invocationId === claim.invocationId) {
        const field = result === "RETURN_TO_IMPLEMENT" ? "control" : "result";
        state.active[claim.lane][field] = result;
        if (this.isClosure(claim)) {
          state.closures ??= {};
          state.closures[claim.invocationId] = { ...state.active[claim.lane], completedAt: new Date(this.now()).toISOString() };
        }
      }
      this.diagnostic(claim, target ? `${result}_TO_${target}` : "FOUNDER_EXCEPTION", {}, state);
      // A control invalidates acceptance but retains ownership of the old child
      // until it exits; it is never stored as a terminal RESULT.
      return true;
    })();
    this.routing.set(claim.invocationId, pending);
    try { return await pending; } finally { this.routing.delete(claim.invocationId); }
  }
  trackSurvivingClosure(claim) {
    // Reuse the existing claim map and inspection timer, not a second observer.
    const active = { ...claim, recoveredProcess: true, lastOutputAt: this.now() };
    this.active.set(claim.invocationId, active);
    this.scheduleInspection(active);
  }
  async resumeAfterClosure(claim) {
    const desired = claim.pendingStatus ?? (claim.control === "RETURN_TO_IMPLEMENT" ? "IMPLEMENT" : null);
    if (!desired || this.stopped) return;
    if (await this.options.authority.currentStatus(claim.item) === desired) await this.start(claim.item, this.roleNames.PRODUCER, desired, undefined, claim.pendingOperatorEvent);
  }
  async readResult(claim) {
    const durable = await this.options.authority.durableResult({ ...claim, includeEvidence: true });
    if (allowedSignals(claim, this.roleNames).has(durable?.value)) {
      claim.signalEvidence = durable.evidence;
      const state = this.state();
      if (state.active[claim.lane]?.invocationId === claim.invocationId) {
        state.active[claim.lane].signalEvidence = durable.evidence;
        this.save(state);
      }
      return durable.value;
    }
    if (durable?.kind === "WORKER_IDENTITY_MISMATCH") this.diagnostic(claim, durable.kind, { evidence: durable.evidence });
    return durable;
  }
  async start(item, role, status, durableRead, operatorEvent) {
    if (this.stopped) return false;
    this.assertActiveConfiguration();
    if (!Object.values(this.roleNames).includes(role)) throw new Error("WORKER_ROLE_CONFIGURATION_MISMATCH");
    const lane = this.lane(item, role);
    if (status === "ACCEPT" && await this.options.authority.currentStatus(item) !== "ACCEPT") {
      this.emit({ issue: item.issue, role, outcome: "STALE_ACCEPT_EVENT" }); return false;
    }
    let persisted = this.state();
    if (persisted.limitEscalations?.[this.biuKey(item)]?.outcome === "EXECUTION_CYCLE_LIMIT") {
      this.emit({ issue: item.issue, role, outcome: "EXECUTION_CYCLE_LIMIT", biu: this.biuKey(item) }); return false;
    }
    if (operatorEvent && (routedSignal(persisted.active[lane]) === "FOUNDER_EXCEPTION"
        || persisted.diagnostics?.[lane]?.outcome === "FOUNDER_EXCEPTION") && !this.authorizedOperator(operatorEvent.sender)) {
      this.emit({ issue: item.issue, role, outcome: "UNAUTHORIZED_OPERATOR_RECOVERY" }); return false;
    }
    if (routedSignal(persisted.active[lane]) === "FOUNDER_EXCEPTION" && operatorEvent?.sender?.type === "User") {
      // Preserve the triggering event while the stopped invocation still owns
      // its PID. Fresh admission validates its author and remote time after exit.
      persisted.active[lane].pendingStatus = status;
      persisted.active[lane].pendingOperatorEvent = {
        sender: operatorEvent.sender,
        changes: { field_value: operatorEvent.changes?.field_value },
        projects_v2_item: { updated_at: operatorEvent.projects_v2_item?.updated_at },
      };
      this.save(persisted);
    }
    if ((status === "ACCEPT" || this.isClosure(persisted.active[lane])) && persisted.active[lane] && persisted.active[lane].status !== status) {
      persisted.active[lane].pendingStatus = status; this.save(persisted);
    }
    if ([...this.active.values()].some((entry) => entry.lane === lane) || this.routing.has(persisted.active[lane]?.invocationId)) {
      this.emit({ issue: item.issue, role, outcome: "ACTIVE_INVOCATION_EXISTS" }); return false;
    }
    const diagnostic = persisted.diagnostics?.[lane];
    const prior = persisted.active[lane] ?? (recoverable(diagnostic?.outcome) ? diagnostic : null);
    if (prior) {
      const claim = { ...prior, item, role, lane };
      if (this.ownedWorkAlive(claim)) { this.emit({ issue: item.issue, role, outcome: "ACTIVE_INVOCATION_EXISTS" }); return false; }
      // Reserve the exact prior invocation before awaiting its durable read.
      // Startup and Status events share this bounded recovery; no retry loop.
      if (!persisted.active[lane]) { persisted.active[lane] = claim; this.save(persisted); }
      this.active.set(claim.invocationId, claim);
      let durable, completed;
      try {
        durable = routedSignal(claim) ?? claim.pendingSignal?.value ?? (durableRead?.invocationId === claim.invocationId ? durableRead.value : await this.readResult(claim));
        if (this.routing.has(claim.invocationId)) await this.routing.get(claim.invocationId);
        if (this.stopped) return false;
        durable = routedSignal(this.state().active[lane]) ?? durable;
        if (allowedSignals(claim, this.roleNames).has(durable) && !routedSignal(claim)) await this.routeResult(claim, durable);
        else if (!allowedSignals(claim, this.roleNames).has(durable)) this.diagnostic(claim, "DURABLE_RESULT_MISSING", durable?.evidence ? { evidence: durable.evidence } : {});
      } catch (error) { this.diagnostic(claim, "COMPLETION_ERROR", { error: error.message }); return false; }
      finally {
        completed = this.state().active[lane];
        this.release(claim); this.active.delete(claim.invocationId);
        this.reconcileResources();
      }
      if (allowedSignals(claim, this.roleNames).has(durable) && !routedSignal(claim)) {
        if (completed && routedSignal(completed)) await this.resumeAfterClosure(completed);
        return false;
      }
      // A successful missing-result read permits the existing successor path.
      persisted = this.state();
    }
    if (persisted.diagnostics?.[lane]?.outcome === "FOUNDER_EXCEPTION") {
      const previous = persisted.diagnostics[lane];
      const sender = operatorEvent?.sender;
      const from = operatorEvent?.changes?.field_value?.from;
      const fromStatus = typeof from === "string" ? from : from?.name;
      const explicit = this.authorizedOperator(sender)
        && typeof fromStatus === "string" && fromStatus.toUpperCase() !== status;
      if (!explicit) { this.emit({ issue: item.issue, role, outcome: "FOUNDER_EXCEPTION" }); return false; }
      let evidence = previous.signalEvidence;
      if (!evidence?.createdAt) {
        const durable = await this.options.authority.durableResult({ ...previous, includeEvidence: true });
        if (durable?.value === "FOUNDER_EXCEPTION") evidence = durable.evidence;
      }
      if (!(Date.parse(operatorEvent.projects_v2_item?.updated_at) > Date.parse(evidence?.createdAt))) {
        this.emit({ issue: item.issue, role, outcome: "STALE_OR_UNVERIFIABLE_OPERATOR_EVENT" }); return false;
      }
      if (await this.options.authority.currentStatus(item) !== status) return false;
      // Re-read after the external check so competing operator deliveries cannot
      // reserve two workers or replace an already-newer diagnostic.
      persisted = this.state();
      if (persisted.active[lane] || persisted.diagnostics?.[lane]?.invocationId !== previous.invocationId) return false;
      persisted.founderExceptions ??= {};
      persisted.founderExceptions[previous.invocationId] ??= previous;
      this.save(persisted);
    }
    if (this.options.executionEnabled === false) { this.emit({ issue: item.issue, role, outcome: "DRY_RUN_ACTIONABLE" }); return false; }
    if (this.options.executionControls && Object.keys(persisted.active).length >= this.options.executionControls.concurrency.value) { this.emit({ issue: item.issue, role, outcome: "CONCURRENCY_CAP_REACHED", concurrencyLimit: this.options.executionControls.concurrency.value }); return false; }
    const limit = this.limitFor(item);
    if (limit && (status === "IMPLEMENT" || status === "VERIFY")) {
      const account = this.limitState(persisted, item, status);
      if (account.phase !== status) {
        this.limitHold(persisted, item, "BIU_LIMIT_PHASE_MISMATCH", { cycle: account.cycle, expectedPhase: account.phase, observedPhase: status });
        return false;
      }
      if (account.phaseInvocations.length >= 1 + limit.maxReplacementsPerPhase) {
        this.limitHold(persisted, item, "PHASE_REPLACEMENT_LIMIT", { cycle: account.cycle, phase: status, maxReplacementsPerPhase: limit.maxReplacementsPerPhase });
        return false;
      }
      this.save(persisted);
    }
    const invocationId = this.invocation(item, role);
    const workerLogin = this.configuredWorkerLogin(role);
    const claim = { invocationId, item, role, status, startedAt: new Date(this.now()).toISOString(), ...(typeof workerLogin === "string" && workerLogin.trim() ? { workerLogin } : {}) };
    // Synchronous check-and-reserve: no await may separate the lane guard and save.
    persisted.active[lane] = claim; this.save(persisted);
    const active = { ...claim, lane, lastOutputAt: this.now() };
    this.active.set(invocationId, active);
    try {
      this.allocateResource(active);
      const resource = this.state().resources?.[invocationId];
      const preflight = await this.options.preflight({ role, item, invocationId, worktree: active.worktree, resource });
      if (!preflight?.ok || this.stopped) {
        this.updateResource(invocationId, { admissionFailed: true });
        this.release(active); this.active.delete(invocationId); this.reconcileResources();
        this.emit({ issue: item.issue, role, outcome: this.stopped ? "SERVICE_STOPPED" : "PREFLIGHT_FAILED" }); return false;
      }
      if (!this.reservePhaseAttempt(item, role, status)) { this.updateResource(invocationId, { admissionFailed: true }); this.release(active); this.active.delete(invocationId); this.reconcileResources(); this.emit({ issue: item.issue, role, outcome: "REPLACEMENT_CAP_REACHED", replacementLimit: this.options.executionControls?.replacements?.value }); return false; }
      const supervision = this.options.launch.plan?.({ role, item, invocationId, resource });
      if (this.options.workers?.[role]?.supervision && !supervision) throw new Error("SUPERVISION_PLAN_REQUIRED");
      if (limit && (status === "IMPLEMENT" || status === "VERIFY")) {
        const accounting = this.state();
        const account = this.limitState(accounting, item, status);
        if (account.phase !== status || account.phaseInvocations.length >= 1 + limit.maxReplacementsPerPhase) throw new Error("BIU_LIMIT_RESERVATION_CHANGED");
        account.phaseInvocations.push(invocationId);
        this.save(accounting);
      }
      this.updateResource(invocationId, { lifecycle: "LAUNCHING", ...(supervision ? { supervision } : {}) });
      const child = this.options.launch({ role, item, invocationId, worktree: active.worktree, resource: this.state().resources?.[invocationId], bootstrap: workerBootstrap(role, item, invocationId, status, this.roleNames, this.options.workerDisplayNames) });
      active.child = child;
      this.active.set(invocationId, active);
      child.stdout?.on("data", () => { active.lastOutputAt = this.now(); });
      child.stderr?.on("data", () => { active.lastOutputAt = this.now(); });
      child.once("error", (error) => { this.diagnostic(active, "WORKER_TECHNICAL_FAILURE", { error: error.message }); });
      child.once("close", (code, signal) => {
        active.exitCode = code ?? child.exitCode; active.signal = signal ?? child.signalCode ?? null;
        active.closed = true;
        this.complete(active).catch((error) => this.emit({ issue: item.issue, role, outcome: "COMPLETION_ERROR", error: error.message }));
      });
      const current = this.state();
      if (current.active[lane]?.invocationId === invocationId && Number.isInteger(child.pid)) {
        if (current.resources?.[invocationId]) Object.assign(current.resources[invocationId], { pid: child.pid, lifecycle: "RUNNING" });
        current.active[lane].pid = child.pid; this.save(current);
      }
      this.scheduleInspection(active);
      return true;
    } catch (error) {
      this.diagnostic(active, "WORKER_TECHNICAL_FAILURE", { error: error.message });
      if (!active.child && !this.state().resources?.[invocationId]?.supervision) {
        const resource = this.state().resources?.[invocationId];
        if (resource && ["ALLOCATING", "READY"].includes(resource.lifecycle)) this.updateResource(invocationId, { admissionFailed: true });
        this.release(active); this.active.delete(invocationId); this.reconcileResources();
      }
      throw error;
    }
  }
  async complete(active) {
    if (this.active.get(active.invocationId) !== active) return;
    if (active.completing) return active.completing;
    if (this.state().resources?.[active.invocationId]?.supervision && this.ownedWorkAlive(active)) return;
    this.cancelInspection(active);
    active.completing = (async () => {
      let completedClaim;
      try {
        // A webhook or timer may already be routing this invocation.
        if (this.routing.has(active.invocationId)) await this.routing.get(active.invocationId);
        const claim = this.state().active[active.lane];
        if (claim?.invocationId !== active.invocationId) return;
        if (!routedSignal(claim)) {
          const durable = claim.pendingSignal?.value ?? await this.readResult(active);
          if (this.routing.has(active.invocationId)) await this.routing.get(active.invocationId);
          if (routedSignal(this.state().active[active.lane])) return;
          if (allowedSignals(active, this.roleNames).has(durable)) await this.routeResult(active, durable);
          else this.diagnostic(active, "DURABLE_RESULT_MISSING", {
            exitCode: active.exitCode ?? active.child?.exitCode, signal: active.signal ?? active.child?.signalCode ?? null,
            ...(durable?.evidence ? { evidence: durable.evidence } : {}),
          });
        }
      } catch (error) {
        // A failed read is not proof that no marker exists. Keep a retryable
        // exact invocation diagnostic without leaving a dead active claim.
        this.diagnostic(active, "COMPLETION_ERROR", { error: error.message, exitCode: active.exitCode ?? active.child?.exitCode });
      } finally {
        completedClaim = this.state().active[active.lane];
        this.release(active);
        if (this.active.get(active.invocationId) === active) this.active.delete(active.invocationId);
        if (active.closed || active.child?.exitCode != null || active.child?.signalCode != null) this.updateResource(active.invocationId, { exitedAt: new Date(this.now()).toISOString() });
        this.reconcileResources();
        if (completedClaim?.invocationId === active.invocationId) await this.resumeAfterClosure(completedClaim);
      }
    })();
    return active.completing;
  }
  cancelInspection(active) {
    if (active.timer !== undefined) (this.options.clearTimeout ?? clearTimeout)(active.timer);
    active.timer = undefined;
  }
  scheduleInspection(active) {
    if (this.stopped || active.completing || this.active.get(active.invocationId) !== active) return;
    // One pending inspection per owned child, bounded to 1 second through 5 minutes.
    const requested = this.options.inspectionIntervalMs ?? 60000;
    const interval = Number.isFinite(requested) ? Math.min(300000, Math.max(1000, requested)) : 60000;
    active.timer = (this.options.setTimeout ?? setTimeout)(async () => {
      active.timer = undefined;
      if (this.stopped || this.active.get(active.invocationId) !== active) return;
      try {
        const outcome = await this.inspectLiveness(active.invocationId);
        if (!this.stopped) this.emit({ issue: active.item.issue, role: active.role, invocationId: active.invocationId, outcome });
      } catch (error) { this.emit({ invocationId: active.invocationId, outcome: "LIVENESS_INSPECTION_ERROR", error: error.message }); }
      finally { this.scheduleInspection(active); }
    }, interval);
    active.timer?.unref?.();
  }
  async inspectLiveness(invocationId) {
    const active = this.active.get(invocationId);
    if (!active || this.stopped || (!active.child && !active.recoveredProcess)) return "PROCESS_GONE";
    const supervised = this.state().resources?.[invocationId]?.supervision;
    if (supervised ? !this.ownedWorkAlive(active) : ((active.recoveredProcess && !this.processAlive(active.pid)) || active.closed || active.child?.exitCode != null || active.child?.signalCode != null)) {
      await this.complete(active); return "PROCESS_GONE";
    }
    if (routedSignal(this.state().active[active.lane])) return "RESULT_ALREADY_DURABLE";
    const durable = this.state().active[active.lane]?.pendingSignal?.value ?? await this.readResult(active);
    if (this.stopped || this.active.get(invocationId) !== active || active.completing) return "PROCESS_GONE";
    if (allowedSignals(active, this.roleNames).has(durable)) { await this.routeResult(active, durable); return "RESULT_ALREADY_DURABLE"; }
    const signals = (this.options.inspectWorker ?? inspectWorker)(active.child ?? { pid: active.pid });
    const quiet = this.now() - active.lastOutputAt >= (this.options.quietInspectionMs ?? 300000);
    if (/^(tty_read|n_tty_read)$/.test(signals.waitChannel ?? "")) return "WAITING_FOR_INPUT";
    if (quiet && /^[TtD]/.test(signals.state ?? "")) return "STUCK";
    return quiet ? "QUIET_BUT_PLAUSIBLY_WORKING" : "HEALTHY_ACTIVE";
  }
  stop() {
    this.stopped = true;
    for (const active of this.active.values()) this.cancelInspection(active);
  }
  async startupReconcile() {
    if (this.started || this.stopped) return;
    this.assertActiveConfiguration();
    this.reconcileResources();
    this.started = true; this.metrics.projectLists++;
    for (const item of await this.options.authority.listItems()) {
      if (this.stopped) return;
      try {
      const snapshot = this.state();
      const producerLane = this.lane(item, this.roleNames.PRODUCER);
      const closure = snapshot.active[producerLane] ?? (recoverable(snapshot.diagnostics?.[producerLane]?.outcome) ? snapshot.diagnostics[producerLane] : null);
      const interrupted = [...Object.entries(snapshot.active), ...Object.entries(snapshot.diagnostics ?? {})]
        .find(([lane, claim]) => claim.item?.repository === item.repository && claim.item.issue === item.issue
          && claim.pendingSignal?.target && !routedSignal(claim)
          && (!snapshot.active[lane] || snapshot.active[lane].invocationId === claim.invocationId)
          && (snapshot.active[lane] || recoverable(claim.outcome)));
      // The persisted admission phase survives the Project's new status.
      const role = interrupted?.[1].role ?? (this.isClosure(closure) ? this.roleNames.PRODUCER : this.roles[item.status?.toUpperCase()]);
      if (!role) continue;
      const lane = this.lane(item, role);
      let persisted = snapshot.active[lane];
      if (!persisted && interrupted) { persisted = interrupted[1]; snapshot.active[lane] = persisted; this.save(snapshot); }
      if (!persisted && this.isClosure(closure)) { persisted = closure; snapshot.active[lane] = closure; this.save(snapshot); }
      let durableRead;
      if (persisted) {
        const claim = { ...persisted, lane, item, role };
        const durable = routedSignal(persisted) ?? persisted.pendingSignal?.value ?? await this.readResult(claim);
        if (allowedSignals(claim, this.roleNames).has(durable)) {
          const routed = routedSignal(persisted) || await this.routeResult(claim, durable);
          if (!this.ownedWorkAlive(claim)) {
            const completed = this.state().active[lane];
            this.release(claim);
            this.reconcileResources();
            if (this.isClosure(claim)) await this.resumeAfterClosure(completed ?? claim);
            else if (routed && interrupted && item.status === persisted.pendingSignal?.target && this.roles[item.status]) {
              // Startup used to admit the target lane here. Settle the old exact
              // intent first, then preserve that admission after confirmation.
              await this.start(item, this.roles[item.status], item.status);
            } else if (routed && item.status === "ACCEPT") await this.start(item, this.roleNames.PRODUCER, "ACCEPT");
          } else if (this.isClosure(claim) || item.status === "ACCEPT" || this.state().resources?.[claim.invocationId]?.supervision) {
            const surviving = this.state().active[lane];
            if (!this.isClosure(claim) && item.status === "ACCEPT") {
              surviving.pendingStatus = "ACCEPT";
              const state = this.state(); state.active[lane] = surviving; this.save(state);
            }
            this.trackSurvivingClosure({ ...surviving, lane });
          }
          continue;
        }
        if (this.ownedWorkAlive(claim)) {
          if (this.isClosure(claim) || this.state().resources?.[claim.invocationId]?.supervision) this.trackSurvivingClosure(claim);
          this.emit({ issue: item.issue, role, outcome: "SURVIVING_INVOCATION_EXISTS", invocationId: claim.invocationId }); continue;
        }
        durableRead = { invocationId: claim.invocationId, value: durable };
      }
      await this.start(item, role, item.status, durableRead);
      } catch (error) {
        // One failed external read must not strand unrelated startup items.
        // Retain the exact claim for the existing bounded event recovery path.
        const state = this.state();
        for (const [lane, claim] of Object.entries(state.active)) {
          if (claim.item?.repository === item.repository && claim.item.issue === item.issue) this.diagnostic({ ...claim, lane }, "COMPLETION_ERROR", { error: error.message });
        }
        this.emit({ issue: item.issue, outcome: "STARTUP_RECONCILIATION_ERROR", error: error.message });
      }
    }
  }
}
