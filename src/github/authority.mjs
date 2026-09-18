const defaultRoleNames = { PRODUCER: "PRODUCER", VERIFIER: "VERIFIER" };

export function allowedSignals(claim, roleNames = defaultRoleNames) {
  if (claim?.role === roleNames.PRODUCER) return claim.status === "ACCEPT"
    ? new Set(["DONE", "FOUNDER_EXCEPTION", "RETURN_TO_IMPLEMENT"])
    : new Set(["VERIFY", "FOUNDER_EXCEPTION"]);
  return new Set(claim?.role === roleNames.VERIFIER ? ["ACCEPT", "REJECT", "FOUNDER_EXCEPTION"] : []);
}

export function parseInvocationSignal(body, claim, roleNames = defaultRoleNames) {
  if (typeof body !== "string" || !claim?.invocationId) return null;
  const markers = [...body.matchAll(/<!-- B-DISP: INVOCATION=([^\s>]+) (RESULT|CONTROL)=([^\s>]+) -->/g)];
  if (markers.length !== 1) return null;
  const [, invocationId, kind, value] = markers[0];
  if (invocationId !== claim.invocationId || !allowedSignals(claim, roleNames).has(value)) return null;
  if (kind === "CONTROL") return value === "RETURN_TO_IMPLEMENT" ? value : null;
  return value === "RETURN_TO_IMPLEMENT" ? null : value;
}

function parseRepository(repository) {
  const [owner, name] = repository.split("/");
  if (!owner || !name) throw new Error("repository must be owner/name");
  return { owner, name };
}

export class GitHubAuthority {
  constructor({ gh, owner, projectNumber, repository, roleNames = defaultRoleNames, workerLogins = {} }) {
    this.gh = gh;
    this.roleNames = roleNames;
    this.owner = owner;
    this.projectNumber = projectNumber;
    this.repository = repository;
    this.workerLogins = workerLogins;
  }

  listItems() {
    const query = "query($owner: String!, $number: Int!) { organization(login: $owner) { projectV2(number: $number) { items(first: 100) { pageInfo { hasNextPage } nodes { id content { __typename ... on Issue { number repository { nameWithOwner } } } fieldValues(first: 100) { pageInfo { hasNextPage } nodes { ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } } } } } } } } }";
    const response = JSON.parse(this.gh(["api", "graphql", "-f", `query=${query}`, "-F", `owner=${this.owner}`, "-F", `number=${this.projectNumber}`]));
    const connection = response.data?.organization?.projectV2?.items;
    if (response.errors?.length || !Array.isArray(connection?.nodes) || connection.pageInfo?.hasNextPage !== false) {
      throw new Error("Project items are unavailable or incomplete");
    }
    const items = connection.nodes.filter((item) => item.content?.__typename === "Issue" && item.content.repository?.nameWithOwner === this.repository);
    if (items.some(item => !Array.isArray(item.fieldValues?.nodes) || item.fieldValues.pageInfo?.hasNextPage !== false)) {
      throw new Error("Project item field values are unavailable or incomplete");
    }
    return items.map((item) => ({ repository: this.repository, issue: item.content.number, itemId: item.id, status: item.fieldValues.nodes.find((value) => value.field?.name === "Status")?.name?.toUpperCase(), dependencies: [], founderException: false }));
  }

  enrichContentNode(contentNodeId, itemId) {
    const query = "query($id: ID!) { node(id: $id) { ... on Issue { number repository { nameWithOwner } projectItems(first: 100) { nodes { id databaseId project { number owner { ... on Organization { login } } } } pageInfo { hasNextPage } } } } }";
    const response = JSON.parse(this.gh(["api", "graphql", "-f", `query=${query}`, "-F", `id=${contentNodeId}`]));
    if (response.errors?.length) throw new Error("Project item resolution is unavailable or incomplete");
    const node = response.data?.node;
    if (!node?.repository?.nameWithOwner || !Number.isInteger(node.number)) return null;
    if (node.repository.nameWithOwner !== this.repository) return null;
    return this.resolveItem({ repository: node.repository.nameWithOwner, issue: node.number, itemId }, node.projectItems ?? null);
  }

  resolveItem(item, connection) {
    if (item?.repository !== this.repository || !Number.isSafeInteger(item.issue) || item.issue <= 0
      || !((typeof item.itemId === "string" && /^(PVTI_[A-Za-z0-9_-]+|[1-9][0-9]*)$/.test(item.itemId))
        || (Number.isSafeInteger(item.itemId) && item.itemId > 0))) {
      throw new Error("Project item identity is invalid or outside the configured repository");
    }
    // Target only this Issue's memberships; normal event processing never scans
    // the Project. A truncated response cannot establish unambiguous identity.
    if (connection === undefined) {
      const { owner, name } = parseRepository(item.repository);
      const query = "query($owner: String!, $name: String!, $issue: Int!) { repository(owner: $owner, name: $name) { issue(number: $issue) { projectItems(first: 100) { nodes { id databaseId project { number owner { ... on Organization { login } } } } pageInfo { hasNextPage } } } } }";
      const response = JSON.parse(this.gh(["api", "graphql", "-f", `query=${query}`, "-f", `owner=${owner}`, "-f", `name=${name}`, "-F", `issue=${item.issue}`]));
      if (response.errors?.length) throw new Error("Project item resolution is unavailable or incomplete");
      connection = response.data?.repository?.issue?.projectItems;
    }
    if (!Array.isArray(connection?.nodes) || connection.pageInfo?.hasNextPage !== false) {
      throw new Error("Project item resolution is unavailable or incomplete");
    }
    const matches = connection.nodes.filter(candidate => candidate?.project?.number === this.projectNumber
      && candidate.project.owner?.login === this.owner
      && (candidate.id === item.itemId || (Number.isSafeInteger(candidate.databaseId) && candidate.databaseId > 0
        && String(candidate.databaseId) === String(item.itemId))));
    if (matches.length !== 1 || typeof matches[0].id !== "string" || !/^PVTI_[A-Za-z0-9_-]+$/.test(matches[0].id)) {
      throw new Error("Project item resolution is missing, mismatched or ambiguous");
    }
    return { ...item, itemId: matches[0].id };
  }

  currentStatus(item) {
    if (item?.repository !== this.repository || !Number.isSafeInteger(item.issue) || item.issue <= 0
      || typeof item.itemId !== "string" || !/^PVTI_[A-Za-z0-9_-]+$/.test(item.itemId)) {
      throw new Error("Project item identity is invalid or outside the configured repository");
    }
    const query = 'query($id: ID!) { node(id: $id) { ... on ProjectV2Item { id project { number owner { ... on Organization { login } } } content { __typename ... on Issue { number repository { nameWithOwner } } } fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } } } } }';
    const response = JSON.parse(this.gh(["api", "graphql", "-f", `query=${query}`, "-F", `id=${item.itemId}`]));
    const current = response.data?.node;
    const status = current?.fieldValueByName?.name;
    if (response.errors?.length || current?.id !== item.itemId || current.content?.__typename !== "Issue"
      || current.content.number !== item.issue || current.content.repository?.nameWithOwner !== this.repository
      || current.project?.number !== this.projectNumber || current.project.owner?.login !== this.owner
      || typeof status !== "string" || !status.trim()) {
      throw new Error(`Project item ${item.itemId} is unavailable for transition confirmation`);
    }
    return status.toUpperCase();
  }

  transition(item, status) {
    if (typeof item?.itemId !== "string" || !/^PVTI_[A-Za-z0-9_-]+$/.test(item.itemId)) {
      throw new Error("Project item must be a resolved GraphQL node ID before transition");
    }
    const query = "query($owner: String!, $number: Int!) { organization(login: $owner) { projectV2(number: $number) { id fields(first: 100) { pageInfo { hasNextPage } nodes { ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }";
    const response = JSON.parse(this.gh(["api", "graphql", "-f", `query=${query}`, "-F", `owner=${this.owner}`, "-F", `number=${this.projectNumber}`]));
    const project = response.data?.organization?.projectV2;
    if (!project) throw new Error(`Project ${this.projectNumber} not found`);
    if (response.errors?.length || !Array.isArray(project.fields?.nodes) || project.fields.pageInfo?.hasNextPage !== false) {
      throw new Error("Project fields are unavailable or incomplete");
    }
    const field = project.fields.nodes.find((candidate) => candidate.name === "Status");
    const option = field?.options?.find((candidate) => candidate.name.toUpperCase() === status.toUpperCase());
    if (!field || !option) throw new Error(`Project Status option ${status} not found`);
    const mutation = "mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) { updateProjectV2ItemFieldValue(input: { projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: { singleSelectOptionId: $optionId } }) { projectV2Item { id } } }";
    this.gh(["api", "graphql", "-f", `query=${mutation}`, "-F", `projectId=${project.id}`, "-F", `itemId=${item.itemId}`, "-F", `fieldId=${field.id}`, "-F", `optionId=${option.id}`]);
  }

  durableResult(claim) {
    const { role, item, startedAt, invocationId, includeEvidence = false } = claim;
    if (item?.repository !== this.repository) throw new Error("Issue is outside the configured repository");
    const { owner, name } = parseRepository(item.repository);
    const comments = JSON.parse(this.gh(["api", `repos/${owner}/${name}/issues/${item.issue}/comments`, "--paginate"]));
    const expectedLogin = this.workerLogins?.[role];
    if (claim.workerLogin !== undefined && claim.workerLogin !== expectedLogin) return null;
    if (!invocationId || typeof expectedLogin !== "string" || !expectedLogin.trim()) return null;
    let mismatch = null;
    for (const comment of comments) {
      const value = parseInvocationSignal(comment.body, claim, this.roleNames);
      // GitHub comment timestamps have second precision; invocation IDs provide
      // exact correlation even when a fast worker finishes in its launch second.
      if (!value || !(Math.floor(Date.parse(comment.created_at) / 1000) >= Math.floor(Date.parse(startedAt) / 1000))) continue;
      if (comment.user?.login === expectedLogin) return includeEvidence
        ? { value, evidence: { commentId: comment.id, createdAt: comment.created_at, author: comment.user.login } }
        : value;
      mismatch ??= {
        kind: "WORKER_IDENTITY_MISMATCH",
        evidence: {
          commentId: comment.id,
          author: comment.user?.login ?? null,
          marker: value,
          repository: item.repository,
          issue: item.issue,
          role,
          expectedLogin,
          startedAt,
          invocationId,
          timestamp: comment.created_at,
        },
      };
    }
    return mismatch;
  }
}
