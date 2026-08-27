"""GitHub panel: 24h tech-progress metrics + a table of PRs in progress.
Options (in flightdeck.toml):
  [[panels]] name="github_prs"
  repos = ["owner/repo", ...]        # repos to include
  base_branch = "main"               # branch merges land on (default main)
  active_projects = ["Foo", "Bar"]   # optional; label mapping via project_labels
  [panels.project_labels]            # optional regex -> project name
  "manager|estimate" = "Manager Estimates"
Auth: a GitHub token in creds ("github_token") or $GH_TOKEN/$GITHUB_TOKEN, or the `gh` CLI."""
from __future__ import annotations
import json, re, subprocess, datetime
from .base import Panel
from .. import creds

def _gh_json(repo, args):
    token = creds.get_secret("github_token")
    env = None
    cmd = ["gh", "pr", "list", "--repo", repo, "--json",
           "number,title,url,headRefName,isDraft,reviewDecision,statusCheckRollup,mergedAt,createdAt,updatedAt,additions,deletions"] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []
    except Exception:
        return []

class GithubPRs(Panel):
    NAME = "github_prs"
    CALLOUT = "abstract"
    TITLE = "Tech progress"

    def _project(self, pr):
        labels = self.ctx.opts.get("project_labels", {})
        hay = f"{pr.get('headRefName','')} {pr.get('title','')}".lower()
        for pat, name in labels.items():
            if re.search(pat, hay):
                active = self.ctx.opts.get("active_projects")
                if active and name not in active:
                    return "Support"
                return name
        return "—"

    def render(self):
        repos = self.ctx.opts.get("repos", [])
        if not repos:
            return ["- (configure `repos` for this panel)"]
        base = self.ctx.opts.get("base_branch", "main")
        now = self.ctx.now
        w24 = (now - datetime.timedelta(hours=24)).isoformat()
        opened, merged, inprog = [], [], []
        for repo in repos:
            for pr in _gh_json(repo, ["--state", "merged", "--search", f"merged:>={w24[:10]}", "--limit", "60"]):
                if (pr.get("mergedAt") or "") >= w24:
                    merged.append(pr)
            for pr in _gh_json(repo, ["--state", "open", "--limit", "60"]):
                if (pr.get("createdAt") or "") >= w24:
                    opened.append(pr)
                if not pr.get("isDraft"):
                    inprog.append(pr)
        add = sum(p.get("additions") or 0 for p in merged)
        dele = sum(p.get("deletions") or 0 for p in merged)
        L = ["**Last 24h**", "",
             "| PRs opened | merged | lines + | lines - |", "|---|---|---|---|",
             f"| {len(opened)} | {len(merged)} | +{add:,} | -{dele:,} |", ""]
        if merged:
            L += ["**Merged (24h)**", "", "| PR | project | what |", "|---|---|---|"]
            for p in sorted(merged, key=lambda x: -x["number"]):
                L.append(f"| [#{p['number']}]({p['url']}) | {self._project(p)} | {p['title'][:70]} |")
            L.append("")
        L += ["**In progress**", "", "| PR | project | what |", "|---|---|---|"]
        seen = set()
        for p in sorted(inprog, key=lambda x: x.get("updatedAt",""), reverse=True):
            if p["number"] in seen:
                continue
            seen.add(p["number"])
            L.append(f"| [#{p['number']}]({p['url']}) | {self._project(p)} | {p['title'][:70]} |")
        if not inprog:
            L.append("| — | — | nothing open |")
        return L
