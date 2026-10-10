# Workflow notes: jianjun / wf-c

Three sessions on 2026-10-10 with Gemini CLI / Gemini 3.8 Flash. C1 did not pass the gate.

## Final numbers

Last row of progress.csv (s03): 3169 passed, 5 failed, 10 errors, 1 tortoise model, 1163 test functions (baseline 1158), 3851 asserts (baseline 3837), 12 skip markers, 109 SQLAlchemy files, 56 SQLAlchemy models. Note: s02 with the same commit reported 32 failed / 0 errors — the suite is flaky.

Total cost across three sessions: ~NZ$3.3, ~130 minutes wall time.

## The three most important things that happened

1. C1 (Foundation — the simplest step) did not pass in three sessions. s01 wrote the scaffolding; s02 fixed three concrete errors; s03 produced zero code changes.
2. Workflow C assumes the agent will diagnose gate failures itself. The agent cannot. It defaulted to running the full suite repeatedly (4 no-op reruns in s03) and eventually drifted into unrelated searches.
3. The same commit produced different test counts across runs (32 failed / 0 errors in s02; 5 failed / 10 errors in s03). The gate as specified cannot be applied to a flaky suite.

## Why I think they happened

- Model capability: Flash is optimized for speed, not long-context reasoning. When it faces 32 failing tests across multiple files, it cannot form a hypothesis about the root cause.
- No enforced sandbox: "Do C1 and nothing else" is text, not a boundary.
- Human over-helping: In s02 the reviewer gave direct solutions ("use aerich.models", "add a TortoiseModelRegistry placeholder model"). This deviates from Workflow C's "human checks the gate only" rule.
- Flaky test suite: The dual-ORM coexist setup breaks a variable number of integration tests depending on pytest-xdist worker ordering.

## Did the agent's behaviour seem specific to this tool or model?

Yes. The failure modes match a lighter model:
- Instruction decay in long contexts (P23).
- Instruction forgetting across turns (P7, P15, P17).
- Premature self-certification (P16).
- Sandbox loops (P14).
- Goal drift under uncertainty (P20).

## What I would change if I ran this workflow again

- Use a stronger model for C1, or split C1 into sub-steps.
- Set a hard token budget that ends the session automatically.
- Reject every attempt to access outside the code repository as a first-class failure.
- Never give the agent a solution when it loops. Stop the session instead.
- Push after every session.
- Address the flaky test suite before applying any gate.

## Anything about the Mealie codebase that made this easier or harder

Harder: the async ORM switch interacts with pytest-xdist's per-worker event loops. The C1 gate requires zero new failures, but the dual-ORM coexist setup naturally breaks a handful of integration tests, and the number varies per run.
Easier: a fast test suite (full run under 1 minute) makes gate checks quick.
