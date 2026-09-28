"""Read AlienIntent Project and Issue comments with the configured GitHub App credential."""
from __future__ import annotations
import json, sys, time
from pathlib import Path

class AppReadError(RuntimeError): pass

class AppGitHubReader:
    def __init__(self, self_hosting_config: Path | str):
        self.path = Path(self_hosting_config)
        self.doc = json.loads(self.path.read_text())
        store = Path(self.doc["paths"]["repositoryStore"])
        src = store / "src"
        if str(src) not in sys.path: sys.path.insert(0, str(src))
        from alienintent.installation.adapters.app_jwt import app_assertion
        from alienintent.installation.adapters.protected_local_file_secret import ProtectedLocalFileSecretProvider
        from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport
        from alienintent.installation.application.installation_credentials import InstallationCredentials
        from alienintent.installation.domain.app_credentials import AppIdentity
        app = self.doc["githubApp"]
        key = Path(app["privateKeyPath"])
        self.transport = UrllibGitHubTransport()
        self.credentials = InstallationCredentials(
            AppIdentity(app["applicationId"], app["installationId"], "app-key"),
            ProtectedLocalFileSecretProvider({"app-key": key}), self.transport, time.time, app_assertion)
        self.owner = self.doc["project"]["owner"]
        self.number = self.doc["project"]["number"]
        self.repo_owner = self.doc["repository"]["owner"]
        self.repo_name = self.doc["repository"]["name"]

    def _graphql(self, query: str, variables: dict) -> dict:
        body = json.dumps({"query": query, "variables": variables}).encode()
        headers = dict(self.credentials.authorization()) | {"Content-Type": "application/json"}
        response = self.transport.request("POST", "https://api.github.com/graphql", headers, body)
        if response.status != 200: raise AppReadError(f"GitHub App GraphQL answered {response.status}")
        doc = json.loads(response.body or b"{}")
        if doc.get("errors"): raise AppReadError("GitHub App GraphQL reported errors")
        return doc["data"]

    def board(self, max_attempts: int = 3) -> list[dict]:
        query = '''query($owner:String!,$number:Int!,$cursor:String){organization(login:$owner){projectV2(number:$number){items(first:100,after:$cursor){totalCount pageInfo{hasNextPage endCursor} nodes{id type content{__typename ... on Issue{number repository{nameWithOwner} labels(first:100){nodes{name}}} ... on PullRequest{number}} status:fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{name}} priority:fieldValueByName(name:"Priority"){... on ProjectV2ItemFieldSingleSelectValue{name}}}}}}}'''
        for _ in range(max_attempts):
            rows=[]; cursor=None; expected=None; unstable=False
            while True:
                data=self._graphql(query,{"owner":self.owner,"number":self.number,"cursor":cursor})
                items=data["organization"]["projectV2"]["items"]
                total=items["totalCount"]
                if expected is None: expected=total
                elif total != expected: unstable=True; break
                for node in items["nodes"]:
                    content=node.get("content") or {}
                    rows.append({"id":node["id"],"type":node["type"],"issue":content.get("number"),
                        "status":(node.get("status") or {}).get("name"),"priority":(node.get("priority") or {}).get("name"),
                        "repository":(content.get("repository") or {}).get("nameWithOwner"),
                        "labels":[x.get("name") for x in ((content.get("labels") or {}).get("nodes") or []) if isinstance(x,dict) and isinstance(x.get("name"),str)]})
                info=items["pageInfo"]
                if not info["hasNextPage"]: break
                cursor=info.get("endCursor")
                if not cursor: raise AppReadError("Project pagination cursor missing")
            if not unstable:
                if expected != len(rows): raise AppReadError("Project snapshot incomplete")
                return rows
        raise AppReadError("Project snapshot unstable after retries")

    def comments(self, issue: int) -> list[dict]:
        query='''query($owner:String!,$name:String!,$issue:Int!,$cursor:String){repository(owner:$owner,name:$name){issue(number:$issue){comments(first:100,after:$cursor){totalCount pageInfo{hasNextPage endCursor} nodes{body lastEditedAt author{login} editor{login}}}}}}'''
        result=[]; cursor=None; total=None
        while True:
            data=self._graphql(query,{"owner":self.repo_owner,"name":self.repo_name,"issue":issue,"cursor":cursor})
            conn=data["repository"]["issue"]["comments"]
            total=conn["totalCount"]
            result.extend({"author":(n.get("author") or {}).get("login"),"editor":(n.get("editor") or {}).get("login"),
                           "lastEditedAt":n.get("lastEditedAt"),"body":n["body"]} for n in conn["nodes"])
            info=conn["pageInfo"]
            if not info["hasNextPage"]: break
            cursor=info.get("endCursor")
            if not cursor: raise AppReadError(f"issue #{issue} comment cursor missing")
        if total != len(result): raise AppReadError(f"issue #{issue} comments incomplete")
        return result
