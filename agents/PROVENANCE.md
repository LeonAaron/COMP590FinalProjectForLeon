# Where this agent code comes from

`agents/` is a copy of my course coding-agent project (`leoa_590_agents`), exported from
commit `1cbe15b` with `git archive` (tracked files only, so no `.env`, keys or virtualenv).

- **Baseline (single agent):** `src/agents590/leoa_ShellAgent/`. One model loop with one `shell` tool,
  `MAX_TURNS = 30`. This is the exact code every baseline eval run used, unchanged.
- **Multi-agent version:** `src/agents590/leoa_TeamAgent/` (added for this project).

Both agents share `provider.py` (UNC Azure gateway, Responses API) and the same model
(`gpt-6-luna`), so the comparison changes only the agent architecture.

To run evals against this copy, point Harbor's `package_path` at this folder and give it an
`.env` made from `.env.example`.
