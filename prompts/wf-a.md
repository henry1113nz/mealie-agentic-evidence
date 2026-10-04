# Workflow A: single high-level instruction (baseline)

**Decomposition:** none. The agent decides everything.
**Context:** the ground rules only. The repository's own AGENTS.md stays as it is.
**Verification:** once, by `measure.sh`, after each session. No checks in between.
**Human role:** answer questions from the ground rules; otherwise reply only `continue`.

Branch: `<member>/wf-a`. Time budget: about 6 hours of agent time, then stop.

## Session 1 prompt

```text
<paste the text block from prompts/ground-rules.md here>

Do the whole rewrite.
```

## Later sessions

Start a new session only when the previous one ends by itself (context or usage limit). Use:

```text
<paste the text block from prompts/ground-rules.md here>

Continue the rewrite. The work so far is in the git history of this branch.
```

## After every session

Commit (`[wf-a] sNN: <what changed>`), run `measure.sh`, export the transcript, fill in the log.
If the agent says the rewrite is finished, record that claim in the log next to what
`measure.sh` shows.
