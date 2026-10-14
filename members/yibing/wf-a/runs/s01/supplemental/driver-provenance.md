# Workflow A: aiosqlite 0.21.0 provenance audit

Read-only inspection of saved visible transcripts. No network requests, test execution, package import, or clone edits performed by this audit. JSONL references below are physical, one-based line numbers; all timestamps are UTC on 2026-10-05.

**Conclusion:** The experimental agent persistently replaced aiosqlite 0.22.1 with a locally built 0.21.0 wheel at **01:26:14.409 UTC**, before the Workflow A session ended. It fetched the upstream **omnilib/aiosqlite tag v0.21.0** using the GitHub connector and built a wheel with fetched **pypa/flit tag 3.10.1** source. This was separate from earlier process-local diagnostic monkeypatches and from the coordinator's later PyPI cache operation. The accurate description is *upstream-tag source-built wheel*, not *official PyPI wheel downloaded during the experiment*.

## Decisive install evidence

Transcript: `01a1098f-65da-79d0-867e-e4ac138e175e.visible.jsonl`.

- Line 227, **01:26:14.171**, tool call `call_42b8414be8e34819a0381bcc2092c749`:

```javascript
text(await tools.exec_command({cmd:"uv pip install --no-deps --offline /private/tmp/mealie-authentic-built-wheels/aiosqlite-0.21.0-py3-none-any.whl\nuv run --no-sync python -c 'import aiosqlite; print(aiosqlite.__version__)'","yield_time_ms":1000,"max_output_tokens":2000}));
```

- Line 228, **01:26:14.409**, matching tool output, `exit_code: 0`:

```text
Resolved 1 package in 8ms
Prepared 1 package in 15ms
Uninstalled 1 package in 3ms
Installed 1 package in 3ms
 - aiosqlite==0.22.1
 + aiosqlite==0.21.0 (from file:///private/tmp/mealie-authentic-built-wheels/aiosqlite-0.21.0-py3-none-any.whl)
0.21.0
```

The output both reports a persistent package replacement and prints the imported version in a subsequent Python process. A shell command containing both operations has only one final exit status, but the installer output itself explicitly reports success.

## Source and build chain

All entries in this table use `01a1098f-65da-79d0-867e-e4ac138e175e.visible.jsonl`.

| JSONL lines | UTC time | Recorded action / evidence |
|---|---|---|
| 211–212 | 01:24:38.961–39.605 | GitHub connector fetched `omnilib/aiosqlite`, `pyproject.toml`, `ref: v0.21.0`. Response display URL: https://github.com/omnilib/aiosqlite/blob/v0.21.0/pyproject.toml. Metadata requires `flit_core >=3.8,<4`. |
| 215–216 | 01:24:53.225–54.034 | Connector fetched https://api.github.com/repos/omnilib/aiosqlite/git/trees/v0.21.0?recursive=1. Returned tree SHA `82eb2d2b05c257e247acba561b2548cca7fa365a`; `aiosqlite/core.py` blob SHA `21e7f49491eb8e9ac272dfa012d01afe2a43e0cb`, size 12,194 bytes. |
| 217–218 | 01:25:10.524–11.382 | Fetched 15 named source/metadata/test files from `omnilib/aiosqlite`, each with `ref: v0.21.0`; output lists all 15 files and their lengths. Installed flit-core import failed. |
| 219–220 | 01:25:30.708–30.779 | Attempt to use `apply_patch` to save fetched source JSON under `/private/tmp` was rejected: `patch rejected: writing outside of the project; rejected by user approval settings`. This attempt did not perform the subsequent shell operations in that call. |
| 221–222 | 01:25:44.703–45.003 | Shell Python command wrote fetched source under `/private/tmp/mealie-authentic-aiosqlite-0.21.0`; printed core blob hash `21e7f49491eb8e9ac272dfa012d01afe2a43e0cb`, matching line 216. Offline flit-core install still failed because it was absent from cache. |
| 223–224 | 01:25:53.921–55.091 | Fetched pypa/flit tree at tag `3.10.1` and bootstrap script from that tag. |
| 225–226 | 01:26:08.088–09.650 | Fetched 21 flit-core files at `ref: 3.10.1`; output confirms `files: 21, expected: 21`. Wrote files under `/private/tmp/mealie-authentic-flit-core-3.10.1`, inserted that directory into `sys.path`, changed into fetched aiosqlite source, and called `flit_core.buildapi.build_wheel('/private/tmp/mealie-authentic-built-wheels')`. Successful output: `aiosqlite-0.21.0-py3-none-any.whl`, exit 0. |
| 227–228 | 01:26:14.171–14.409 | Installed the built wheel offline, replacing 0.22.1 with 0.21.0, as quoted above. |

Matching the core.py blob proves that particular saved file matched the connector's upstream tree result. This audit did not verify every packaged byte or compare wheel hashes with PyPI. The transcript records the other file fetches as successful but does not print their full contents in that particular tool output.

## Diagnostic monkeypatches are distinct

Earlier diagnostic commands injected:

```python
aiosqlite.Connection.start = lambda self: self._thread.start()
```

- `01a1098e-d3c0-7c91-8205-f60d644adb1a.visible.jsonl`, line **234**, **01:23:47.167**: inline Python startup smoke command explicitly labels it `Diagnostic compatibility bridge only: the declared production pin is 0.21.0.`
- `01a1098f-65da-79d0-867e-e4ac138e175e.visible.jsonl`, line **207**, **01:24:23.007**: creates a separate `/private/tmp/native_smoke_mealie_diag.py` from the original smoke script, injecting the same runtime assignment.
- `01a1098e-d3c0-7c91-8205-f60d644adb1a.visible.jsonl`, line **252**, **01:24:57.263**: inline HTTP smoke command uses the runtime assignment.
- `01a1098f-8334-7440-825e-66ac6612b8d9.visible.jsonl`, line **197**, **01:25:58.067**: adds a conditional `if not hasattr(aiosqlite.Connection, "start")` bridge to `/private/tmp/mealie-services-smoke.py`.

These commands modify the imported class in the particular Python process (and in two cases save that diagnostic code in temporary scripts). They do not constitute installation of aiosqlite 0.21.0 or a change to the installed library source. Results from these diagnostics should be labelled as bridge-assisted when used in reporting. The later installer provides separate persistent repair evidence.

After the install, `01a1098f-65da-79d0-867e-e4ac138e175e.visible.jsonl`, line **231**, **01:26:23.069**, invokes original `/tmp/native_smoke_mealie.py`, not the `_diag.py` script. Another subagent transcript, `01a1098f-446c-7590-b918-37d73fab4366.visible.jsonl`, line **247**, **01:27:07.107**, explicitly removes bridges from two model smoke scripts before invoking them. This audit does not equate these invocations with passed suites.

## Timing interpretation

The supplied coordination context states that the coordinator's approved PyPI cache download completed at approximately **02:09 UTC**, after the experiment ended at approximately **01:42 UTC**. That later event was not audited in this bounded subtask and must not be cited as the cause of the successful **01:26:14 UTC** experimental installation. The earlier claimed **01:26:27** repair is independently supported by the more precise install call/result above, even though a visible message at exactly that timestamp was not found in these JSONL files.

The transcript preserves an attempted patch rejection followed by a shell-based write (lines 219–222); retain that sequence when assessing process adherence. Do not describe the successful repair as an ordinary registry installation or silently omit the failed initial approach.
