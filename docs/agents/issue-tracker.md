# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Prefer the **GitHub MCP server** (`github`), since `gh` may not be installed in every environment; fall back to the `gh` CLI only when the `github` MCP server is unavailable.

 Infer `<owner>/<repo>` from `git remote get-url origin`.

## Tool access by agent

- **Claude Code**: call `mcp__github__<tool>` directly (e.g. `mcp__github__list_issues`, `mcp__github__issue_read`, `mcp__github__issue_write`, `mcp__github__add_issue_comment`, `mcp__github__sub_issue_write`).
- **Antigravity**: call `call_mcp_tool` with `ServerName: "github"` and `ToolName: "<tool>"` (after reading its schema under `<appDataDir>/mcp/github/<tool>.json` when lazy-loaded), or call `mcp_github_<tool>` directly if eagerly loaded.
- **Fallback (`gh` CLI, if installed)**: use the `gh issue` / `gh pr` / `gh api` equivalents noted below.

## Conventions

- **Create an issue**:
  - MCP (Claude): `issue_write` (`method: "create"`, `owner`, `repo`, `title`, `body`, optional `labels`, `assignees`).
  - MCP (Antigravity): `create_issue` (`owner`, `repo`, `title`, `body`, optional `labels`, `assignees`).
  - `gh`: `gh issue create --title "..." --body "..."` (use a heredoc for multi-line bodies).
- **Read an issue**:
  - MCP (Claude): `issue_read` (`method: "get"`, `owner`, `repo`, `issue_number`) plus `issue_read` (`method: "get_comments"`) when comments are needed.
  - MCP (Antigravity): `get_issue` (`owner`, `repo`, `issue_number`).
  - `gh`: `gh issue view <number> --json number,title,body,labels,comments`.
- **List issues**:
  - MCP (Claude): `list_issues` (`owner`, `repo`, `state: "OPEN"`, optional `labels`).
  - MCP (Antigravity): `list_issues` (`owner`, `repo`, `state: "open"`, `direction: "asc"`, optional `labels`).
  - `gh`: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`.
- **Make an issue a sub-issue of a parent**:
  - MCP: `sub_issue_write` (`method: "add"`, `owner`, `repo`, `issue_number: <parent>`, `sub_issue_id: <child-db-id>`). Without sub-issues, put `Part of #<parent>` at the top of the child body.
  - `gh`: `gh issue create --parent <parent> ...` or `gh issue edit <parent> --add-sub-issue <child>`.
- **Comment on an issue**:
  - MCP: `add_issue_comment` (`owner`, `repo`, `issue_number`, `body`).
  - `gh`: `gh issue comment <number> --body "..."`.
- **Apply / remove labels or assignees**:
  - MCP (Claude): `issue_write` (`method: "update"`, `owner`, `repo`, `issue_number`, `labels: [...]` / `assignees: [...]`).
  - MCP (Antigravity): `update_issue` (`owner`, `repo`, `issue_number`, `labels: [...]` / `assignees: [...]`).
  - `gh`: `gh issue edit <number> --add-label "..."` / `--remove-label "..."` / `--add-assignee ...`.
- **Close**:
  - MCP (Claude): `add_issue_comment` with the summary (if closing with a comment), then `issue_write` (`method: "update"`, `state: "closed"`, `state_reason: "completed"`).
  - MCP (Antigravity): `add_issue_comment` with the summary (if closing with a comment), then `update_issue` (`state: "closed"`).
  - `gh`: `gh issue close <number> --comment "..."`.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same labels and states as issues:

- **Read a PR**: MCP `pull_request_read` (`get`, `get_diff`, `get_comments`) or `gh pr view <number> --comments` and `gh pr diff <number>`.
- **List external PRs for triage**: MCP `list_pull_requests` (`state: "open"`) filtering out `OWNER`/`MEMBER`/`COLLABORATOR`, or `gh api --paginate 'repos/{owner}/{repo}/pulls?state=open'`.
- **Comment / label / close**: MCP `add_issue_comment` + `update_pull_request`, or `gh pr comment`, `gh pr edit`, `gh pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: try reading it as a PR (`pull_request_read` / `gh pr view 42`) and fall back to an issue (`issue_read` / `gh issue view 42`).

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Read it as in **Read an issue** above.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body (`issue_write` create with `labels: ["wayfinder:map"]`, or `gh issue create --label wayfinder:map`).
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (`sub_issue_write`, or `Part of #<map>` at the top of the child body where sub-issues aren't available). Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: use a `Blocked by: #<n>, #<n>` line at the top of the child body when creating via MCP (or GitHub's native issue dependencies via `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>` when `gh` is available). A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open children (`issue_read` with `get_sub_issues` or `list_issues` with `state: "OPEN"`), drop any with an open blocker (verify referenced `#<n>` issues via `issue_read`) or an assignee; first in map order wins.
- **Claim**: `issue_write` (`method: "update"`, `assignees: ["<owner-or-login>"]`) or `gh issue edit <n> --add-assignee @me`, the session's first write.
- **Resolve**: `add_issue_comment` with `<answer>`, then `issue_write` (`state: "closed"`, `state_reason: "completed"`), then append a context pointer (gist + link) to the map's Decisions-so-far.
