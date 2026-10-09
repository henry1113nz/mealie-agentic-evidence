# Session log: jianjun / wf-c

One row per session. Fill it in straight after the session, not later.

| Session | Date | Agent time (min) | Tokens | Cost (USD, API-equivalent) | Commit | What the agent did | Questions it asked and our answers | Problems seen (with transcript line or commit) |
|---|---|---|---|---|---|---|---|---|
| s01 | 2026-10-10 | 31m 49s wall / 28m 40s active | 4,079,351 in / 6,590 out (3.49M cache reads) | ~NZ$1.5 | 92c829709 | Wrote C1 foundation: mealie/db/tortoise/{config,models,setup,__init__}.py, updated mealie/app.py with a lifespan that inits/closes Tortoise, updated tests/conftest.py for dual-ORM coexistence, added tests/unit_tests/test_tortoise_foundation.py. SQLAlchemy untouched. Gate FAILED (test suite crashes on import due to pk=True DeprecationWarning). | No text questions. 79 tool-permission prompts, all reviewed: 1 rejected for out-of-scope git log across other branches; 2 rejected for pk→primary_key changes (human misjudgment); 1 rejected for filterwarnings suppression. | See P1-P10 below. measure.sh: 0 passed, no-report, 1 mypy error, 1163 test functions (+5), 3851 asserts (+14), 12 skip markers, 1 tortoise model, 18 test-setup lines, 53 test-file lines. |
| s02 | 2026-10-10 | 26m 33s wall / 23m 0s active | 2,405,714 in / 4,099 out (2.11M cache reads) | ~NZ$0.8 | 247428e53 | Fixed C1 gate failures: pk=True -> primary_key=True (lines 40, 47 of models.py); resolved mypy str|None error in config.py; added TortoiseModelRegistry placeholder model so Tortoise finds a concrete model. Gate STILL FAILING: 32 tests fail (baseline 0), all in recipe CRUD (27) and pagination ordering (5). Agent initially marked C1 as "done" in AGENTS.md — human corrected to "in progress". | No questions asked. 6 rejections: 1 for installing aerich in C1, 1 for filterwarnings suppression, 4 for repeated rejected changes. | P11-P17 below. measure.sh s02: 3152 passed, 32 failed, 0 mypy errors, 1 tortoise model, 1163 test functions (+5), 3851 asserts (+14), 12 skip markers. |

## Problems to watch for

Write down each one as soon as you see it, with the commit or transcript line:

- Loss of context in long sessions (forgets earlier decisions, repeats work, re-reads files)
- Hallucinated APIs (calls Tortoise methods or options that do not exist)
- Tests deleted, skipped or weakened (also check the integrity columns in progress.csv)
- Premature claims of completion (says done; measure.sh disagrees)
- Drift from project conventions (naming, layering, style)

## Problems seen in s01

- **P1 Out-of-scope reconnaissance.** Told "Read AGENTS.md first... do step C1 and nothing else", the agent still ran `git branch -a` and `git log -n 5 --oneline` across other members' branches (haodong/wf-a, yawen/wf-a, yibing/wf-a). Redirected with "Do only step C1. Do not look at other branches."
- **P2 Sandbox testing spiral.** Before writing any config files, the agent ran three `uv run python -c` sandbox tests: (1) `import tortoise`, (2) trying to load `mealie.db.models` into Tortoise (impossible, those are SQLAlchemy models), (3) a stub test with `pass` and a comment. Echoes Workflow A's failure mode.
- **P3 API detail missed on first pass.** Used SQLAlchemy syntax `index=True` on `DatetimeField`; Tortoise uses `db_index=True`. Caught by the test run.
- **P4 Blind trial-and-error after first failure.** After fixing `index` → `db_index`, the agent proposed `pk=True` → `primary_key=True` without citing any error. Rejected twice (see P8).
- **P5 Tortoise loop management risk.** conftest.py calls `asyncio.run(init_tortoise())` at import time, `asyncio.run(close_tortoise())` in teardown, and adds an `async tortoise_db` fixture with default function scope. Three separate event-loop entry points likely to cause `TortoiseLoopSwitchWarning` or `No TortoiseContext` once the pk bug is fixed.
- **P6 Warning suppression proposed.** Attempted to add `"ignore::DeprecationWarning:tortoise.*"` to pyproject.toml filterwarnings with no cited warning. Rejected (see P8).
- **P7 Instruction forgetting.** After being told "pk=True is correct; primary_key=True is not a Tortoise parameter", the agent proposed the exact same change again in the next turn. Flash does not retain human corrections across turns.
- **P8 Human misjudgment (bidirectional failure).** The agent's `pk` → `primary_key` change was actually correct: Tortoise 1.1.8 emits `DeprecationWarning: pk is deprecated, please use primary_key instead`, and pyproject.toml turns this into a hard error. Two rejections by the human reviewer were wrong. The agent failed to cite the error message, and the reviewer failed to verify. Root cause: poor agent communication of change justification.
- **P9 No text interaction.** All 79 tool prompts were permission confirmations; the agent never asked a clarifying question. Unusual for Workflow C, where the human is expected to check the gate.
- **P10 AGENTS.md not updated at end of session.** Workflow C's core mechanism is that the agent updates the "Tortoise ORM rewrite" section at the end of every session. In s01 the agent did NOT update the progress table or Decisions log; the C1 row still shows `not started` and the Decisions log is empty.

## Problems seen in s02

- **P11 Attempted to read evidence repository.** After reading AGENTS.md and models.py, the agent ran `FindFiles '*measure*'` and `find /home/luna -name "measure.sh"` and tried `cat /home/luna/mealie-agentic-evidence/scripts/measure.sh`. Rejected: "Do NOT access ~/mealie-agentic-evidence." Without this guard, the agent would have seen the entire experiment design.
- **P12 Warning suppression (2nd attempt).** Proposed adding `"ignore:Module has no models:RuntimeWarning"` to pyproject.toml filterwarnings instead of fixing the config. Rejected; directed to add a concrete placeholder model.
- **P13 C1 scope violation - installing Aerich early.** Discovered aerich is not installed and tried `uv add --dry-run aerich`. Aerich belongs to C7, not C1. Rejected; redirected to a placeholder model.
- **P14 Sandbox testing loop (4 iterations).** Spent four `uv run python -c` sandbox tests trying to find a valid Tortoise config with no concrete models. All rejected by Tortoise. Had to be told directly to use the placeholder-model approach.
- **P15 Instruction forgetting (3rd occurrence).** After being told "Do not install aerich", the agent re-proposed `uv add --dry-run aerich` on the next turn. Same pattern as P7 in s01.
- **P16 Premature claim of completion.** Marked C1 as `done | s02 | 35` in the AGENTS.md progress table, in the same row that recorded 35 failing tests (baseline 0). Per the gate rule, the gate did NOT pass. Human corrected to `in progress`.
- **P17 Gate still failing after two sessions.** s02 improved from 0 passed / no-report (s01) to 3152 passed / 32 failed (s02). Failures cluster in test_recipe_crud.py (27) and test_pagination.py (5).

## Human side notes (not AI problems)

- **Human over-helping in s02.** When the agent looped on the "no models" RuntimeWarning, the human reviewer gave direct solutions ("use ['aerich.models']", "add a TortoiseModelRegistry placeholder model"). Workflow C's design says the human only checks the gate and pastes measure.sh numbers — giving solutions is out of scope and weakens the experiment. The temptation to help when the AI is stuck is a real failure mode of the "human checks the gate only" design.
