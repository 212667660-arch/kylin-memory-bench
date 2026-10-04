# Four-Agent Quick Compare Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the four preinstalled openKylin Agents discoverable and comparable through one user-facing quick workflow without requiring YAML editing, manual suite parameters, or multiple setup commands.

**Architecture:** Keep the existing runner, scoring, evidence schema, and advanced configuration flow. Add a registry/discovery layer that produces safe Agent profiles, adapters that translate each Agent's observable state into existing evidence events, and a fixed quick-compare entrypoint used by both CLI and workbench. KylinAgent remains explicitly limited when only GUI evidence is available.

**Tech Stack:** Python 3.9+, standard library, existing PyYAML/HTTP workbench, existing JSONL evidence protocol, browser UI served by `kmb.workbench`.

**Spec:** `docs/native-memory-compare.md`, `docs/ecosystem-agent-export.md`, and the approved 2026-09-22 design in the conversation.

## Global Constraints

- Do not download or install Agent software from the benchmark runner.
- Preserve existing `kmb run`, `kmb compare`, YAML profiles, and evidence files.
- Never synthesize memory events when an Agent exposes only text or GUI evidence.
- Every result must preserve the existing source/evidence_class distinction and state its observability mode.
- Native model memory must remain distinct from Agent-owned process/storage evidence.
- Default quick mode uses a fixed suite, seed `42`, retries `1`, timeout `180` seconds, and the repository scorer version.
- Do not expose API keys in browser payloads, YAML, logs, or result files.

---

### Task 1: Define the discovery and evidence metadata contract

**Files:**
- Create: `kmb/agent_registry.py`
- Modify: `kmb/agents.py`
- Test: `tests/test_agent_registry.py`

**Interfaces:**
- `AgentProfile` dataclass fields: `id`, `display_name`, `installed`, `adapter`, `version`, `evidence_mode`, `memory_paths`, `capabilities`, `config_path`, `reason`.
- `discover_agents(root: Path | None = None) -> list[AgentProfile]` returns the four ordered profiles (`kylinbot`, `hermes`, `openclaw`, `kylinagent`) plus optional local baselines only when explicitly requested.
- `profile_to_dict(profile: AgentProfile) -> dict[str, Any]` returns browser/CLI-safe metadata with no secret values.
- `AgentAdapter.describe()` gains stable `evidence_mode` and `memory_paths` fields while retaining current metadata.

- [ ] Write tests for discovery with temporary HOME fixtures: installed KylinBot, Hermes, OpenClaw, KylinAgent; absent paths must be reported as unavailable rather than raising.
- [ ] Write tests that profile serialization never contains credential values or arbitrary file contents.
- [ ] Run `\.venv-kmb-system\Scripts\python.exe -m unittest tests.test_agent_registry -v` and verify the new tests fail before implementation.
- [ ] Implement path-safe discovery using environment/Home paths and command lookup; do not access databases during discovery.
- [ ] Implement metadata propagation in `AgentAdapter.describe()` and existing config-backed agents.
- [ ] Run the focused tests and existing `tests.test_agents` suite.

### Task 2: Add fixture-backed storage adapters for the four Agent evidence sources

**Files:**
- Create: `kmb/agent_adapters/__init__.py`
- Create: `kmb/agent_adapters/sqlite_memory.py`
- Create: `kmb/agent_adapters/kylinbot.py`
- Create: `kmb/agent_adapters/hermes.py`
- Create: `kmb/agent_adapters/openclaw.py`
- Create: `kmb/agent_adapters/kylinagent.py`
- Test: `tests/test_agent_adapters.py`

**Interfaces:**
- `MemorySnapshotAdapter.snapshot() -> dict[str, Any]` reads only a configured path and returns redacted, bounded metadata.
- `MemorySnapshotAdapter.diff(before, after) -> list[dict[str, Any]]` emits only observed changes.
- `KylinBotAdapter.run(case) -> list[EvidenceEvent]` reuses the current CLI driver and emits `source=process` events.
- `HermesAdapter`, `OpenClawAdapter`, and `KylinAgentAdapter` expose the same `run(case)` contract; each reports its evidence mode honestly.

- [ ] Create SQLite/JSON/text fixtures matching the screenshot's storage locations and test read-only snapshots and bounded redaction.
- [ ] Test that unrelated historical rows never become current-case writes.
- [ ] Test Hermes `messages`, OpenClaw transcript plus `USER.md`/`MEMORY.md`, and KylinAgent `memory.db` observations independently.
- [ ] Test KylinAgent GUI-only fallback emits `conversation_only`/`gui_observed` metadata without fabricating `memory_write` or `memory_recall`.
- [ ] Implement shared snapshot/diff helpers and per-Agent adapters; reuse `scripts/kylinbot_command_agent.py` rather than duplicating KylinBot behavior.
- [ ] Run focused adapter tests and `tests.test_kylinbot_driver`.

### Task 3: Build fixed quick-compare orchestration

**Files:**
- Create: `kmb/quick_compare.py`
- Modify: `kmb/cli.py`
- Modify: `kmb/runner.py`
- Create: `suites/quick.yaml`
- Test: `tests/test_quick_compare.py`

**Interfaces:**
- `QUICK_SUITE_PATH` points to `suites/quick.yaml`.
- `QuickCompareOptions` contains `agent_ids`, `out_dir`, `seed=42`, `retries=1`, `timeout=180`.
- `run_quick_compare(options, root=None) -> dict[str, Any]` discovers profiles, validates availability, runs the fixed suite, and returns comparison metadata plus result paths.
- CLI command: `python -m kmb.cli quick-compare [--agents A B] [--out PATH]`.

- [ ] Add tests for default parameters, deterministic suite selection, unavailable Agent failure messages, and preserving evidence modes in output.
- [ ] Add tests that a quick comparison runs exactly two distinct Agents and rejects duplicate selections.
- [ ] Implement orchestration over existing `run_suite`/`write_compare`; do not create a second scoring implementation.
- [ ] Add a fixed quick suite with one representative case per supported capability, using natural-language turns and no prewritten memory operations for native Agents.
- [ ] Add `discover-agents` and `quick-compare` CLI output designed for direct user use.
- [ ] Run focused quick-compare tests and CLI help/list tests.

### Task 4: Integrate automatic discovery and quick mode into the workbench

**Files:**
- Modify: `kmb/workbench.py`
- Modify: `kmb/web/app.js`
- Modify: `kmb/web/index.html`
- Modify: `kmb/web/styles.css`
- Test: `tests/test_workbench.py`

**Interfaces:**
- `GET /api/agents` returns safe `AgentProfile` metadata.
- `POST /api/quick-compare` accepts only Agent IDs and optional output label; server applies fixed quick parameters.
- Existing `/api/configs`, `/api/runs`, and manual run endpoints remain unchanged.

- [ ] Add backend tests for `/api/agents`, quick-compare validation, and no-secret response payloads.
- [ ] Add a first-screen quick comparison panel with discovered Agents, availability/evidence badges, and a single start button.
- [ ] Keep advanced YAML/manual run controls under the existing advanced view.
- [ ] Render explicit evidence-mode labels and unavailable reasons beside each Agent.
- [ ] Implement progress polling and link the completed job to the existing comparison result viewer.
- [ ] Run all workbench tests and a local browser smoke test against the served UI.

### Task 5: Package the one-install user path and document it

**Files:**
- Modify: `packaging/deb/` launcher/control files as needed
- Modify: `README.md`
- Create: `docs/quick-start.md`
- Modify: `docs/workbench.md`
- Test: `tests/test_packaging_quick_start.py`

**Interfaces:**
- Installed command: `kmb start` launches the local workbench.
- Installed command: `kmb discover-agents` prints a concise table suitable for support logs.
- Quick-start documentation contains only install, start, select two Agents, compare, and inspect evidence.

- [ ] Test launcher resolution from an installed package layout and failure messages when the browser cannot be opened.
- [ ] Ensure package contents include quick suite, registry, adapters, UI assets, and no credentials/runs/cache.
- [ ] Update README to make quick mode the primary path and move YAML/VM/SSH to advanced reproduction.
- [ ] Add clear limitations for KylinAgent GUI-only evidence and wrapper-assisted results.
- [ ] Run package content audit and all local tests.

### Task 6: VM acceptance after code completion

**Files:**
- Create: `runs/openkylin-validation-20260922/quick-compare/`
- Modify: `docs/mimo.md`

- [ ] Sync only the completed package/code to the already-installed openKylin 3.0 VM.
- [ ] Run `kmb discover-agents` and archive sanitized availability/version/evidence metadata.
- [ ] Run the quick comparison for available Agent pairs with fixed parameters.
- [ ] Verify every result with `scripts/verify_run.py`; preserve failures and unavailable Agent explanations.
- [ ] Update the project ledger with exact commands, exit codes, evidence modes, and cleanup actions.
