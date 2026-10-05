#!/usr/bin/env python3
"""KylinAgent driver: drive an isolated Kylin-Agent-Runtime (hermes-agent engine)
per benchmark turn and translate the observed message stream into kmb evidence.

Protocol: reads one BenchmarkCase JSON on stdin, emits kmb EvidenceEvent JSONL on
stdout (CommandAgent contract, same as scripts/kylinbot_command_agent.py).

Mapping rules (honest observation only — no suite answers are written into events):
- user turn text                 -> user_message      (source=runner)
- assistant content              -> assistant_message (source=model)
- model memory-tool call + result -> memory_recall    (source=memory_layer,
  key=query, hit=count>0, value=first snippet). KylinAgent's memory is a
  session-search paradigm (FTS over past sessions); it has no key-value write
  tool, so no memory_write events are emitted — an architectural difference
  reported as-is.
- model write_file/terminal/... call + result -> action (source=model, executed
  from the observed tool result)

Isolation: --hermes-home must point at an ISOLATED clone of the runtime home
(config.yaml + auth.json copied, state fresh) so benchmark sessions never touch
the user's live agent state; --runtime-code points at the read-only engine code.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional


def _parse_tool_calls(message: Dict[str, Any]) -> List[Dict[str, Any]]:
    calls = []
    for call in message.get("tool_calls") or []:
        if not isinstance(call, dict):
            continue
        function = call.get("function") or {}
        arguments = function.get("arguments")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"raw_arguments": arguments}
        calls.append({
            "name": str(function.get("name") or ""),
            "arguments": arguments if isinstance(arguments, dict) else {},
            "call_id": call.get("id", ""),
            "resolved": False,
        })
    return calls


def _parse_tool_result(content: Any) -> Dict[str, Any]:
    if isinstance(content, dict):
        return content
    try:
        parsed = json.loads(content or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def map_case_to_events(case: Dict[str, Any], turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Translate per-turn AIAgent results into kmb evidence dicts.

    ``turns[i]`` is the raw ``run_conversation`` result for ``case["turns"][i]``:
    ``{"final_response": str, "messages": [ {role, content, tool_calls,
    tool_name, ...}, ... ]}`` — the triggering user message is messages[0].
    """
    events: List[Dict[str, Any]] = []

    def emit(kind: str, data: Dict[str, Any], step: int, source: str) -> None:
        events.append({"case_id": case.get("id", ""), "kind": kind, "data": data, "step": step, "source": source})

    for index, turn in enumerate(case.get("turns", []) or []):
        step = index + 1
        user = str((turn or {}).get("user", ""))
        emit("user_message", {"text": user}, step, "runner")
        result = turns[index] if index < len(turns) else {}
        messages = result.get("messages") or []
        unresolved: List[Dict[str, Any]] = []
        saw_assistant_text = False
        for position, message in enumerate(messages):
            role = str(message.get("role") or "")
            if position == 0 and role == "user":
                continue  # the triggering message is already emitted
            if role == "assistant":
                text = str(message.get("content") or "").strip()
                if text:
                    emit("assistant_message", {"text": text}, step, "model")
                    saw_assistant_text = True
                new_calls = _parse_tool_calls(message)
                unresolved.extend(new_calls)
                for call in new_calls:
                    if call["name"] != "memory":
                        emit("action", {
                            "tool": call["name"],
                            "path": call["arguments"].get("path"),
                            "arguments": {k: v for k, v in call["arguments"].items() if k != "content"},
                            "tool_call_observed": True,
                            "execution_observed": False,
                        }, step, "model")
            elif role == "tool":
                tool_name = str(message.get("tool_name") or "")
                result_data = _parse_tool_result(message.get("content"))
                pending = None
                for waiting in unresolved:  # prefer same-tool FIFO, else plain FIFO
                    if waiting["resolved"]:
                        continue
                    if pending is None or waiting["name"] == tool_name:
                        pending = waiting
                        if waiting["name"] == tool_name:
                            break
                if pending is None:
                    continue
                pending["resolved"] = True
                if pending["name"] == "memory":
                    hits = result_data.get("results") or []
                    emit("memory_recall", {
                        "key": str(pending["arguments"].get("query") or ""),
                        "hit": bool(hits),
                        "value": (hits[0] or {}).get("snippet") if hits else None,
                        "query": pending["arguments"].get("query"),
                        "mode": result_data.get("mode"),
                        "count": result_data.get("count"),
                        "state_observed": True,
                        "decision": "agent_tool_memory_search",
                    }, step, "memory_layer")
                else:
                    executed = bool(result_data.get("success", result_data.get("executed", False)))
                    for event in events:
                        if (event["kind"] == "action" and event["source"] == "model"
                                and not event["data"].get("execution_observed")
                                and event["data"].get("tool") == tool_name):
                            event["data"]["executed"] = executed
                            event["data"]["exit_code"] = 0 if executed else 1
                            event["data"]["execution_observed"] = True
                            event["data"]["state_observed"] = executed
                            break
        if not saw_assistant_text and result.get("final_response"):
            emit("assistant_message", {"text": str(result["final_response"])}, step, "model")
    return events


def _build_agent(hermes_home: str, runtime_code: str):
    """Construct the runtime's AIAgent against an isolated HERMES_HOME (VM only)."""
    import os

    os.environ["HERMES_HOME"] = hermes_home
    os.environ.setdefault("AGENT_RUNTIME_HOME", hermes_home)
    for candidate in (runtime_code,):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)
    from run_agent import AIAgent  # noqa: E402  (runtime code only)

    config: Dict[str, Any] = {}
    config_file = os.path.join(hermes_home, "config.yaml")
    if os.path.isfile(config_file):
        import yaml  # noqa: E402

        config = yaml.safe_load(open(config_file, encoding="utf-8")) or {}
    model_cfg = config.get("model") or {}
    if not isinstance(model_cfg, dict):
        model_cfg = {}
    model = os.environ.get("KMB_KYLINAGENT_MODEL") or str(model_cfg.get("default") or "deepseek-v4-flash")
    agent = AIAgent(
        base_url=model_cfg.get("base_url"),
        api_key=model_cfg.get("api_key"),
        model=model,
        skip_context_files=True,
        skip_memory=False,
    )
    # The gateway's streaming transport hangs intermittently mid-conversation
    # (model.transport.start with no completion). The runtime's own degradation
    # hook switches the whole session to non-streaming — use it.
    agent._disable_streaming = True
    return agent, model


def _ensure_fts_index(hermes_home: str, runtime_code: str) -> None:
    """Create + backfill the messages FTS index in the isolated home.

    The chat-persistence path creates memory.db without the FTS schema (the
    schema migration is skipped when a schema_version row already exists), so a
    fresh isolated home has no search index and the runtime's memory tool finds
    nothing. Apply the runtime's own FTS_SQL and backfill existing rows; the
    attached triggers keep it synced for new inserts.
    """
    import os
    import sqlite3

    try:
        if runtime_code and runtime_code not in sys.path:
            sys.path.insert(0, runtime_code)
        import kylin_agent_runtime_state as state_mod  # noqa: E402
    except Exception as exc:  # pragma: no cover - runtime env only
        print("fts bootstrap skipped: %s" % exc, file=sys.stderr)
        return
    for name in ("memory.db", "kylin_agent_runtime_state.db", "state.db"):
        db_path = os.path.join(hermes_home, name)
        if not os.path.isfile(db_path):
            continue
        try:
            conn = sqlite3.connect(db_path)
            conn.executescript(state_mod.FTS_SQL)
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            if "messages" in tables:
                conn.execute(
                    "INSERT INTO messages_fts(rowid, content) "
                    "SELECT id, COALESCE(content, '') || ' ' || COALESCE(tool_name, '') || ' ' || COALESCE(tool_calls, '') "
                    "FROM messages WHERE id NOT IN (SELECT rowid FROM messages_fts)"
                )
            conn.commit()
            conn.close()
        except Exception as exc:  # pragma: no cover - runtime env only
            print("fts bootstrap failed for %s: %s" % (name, exc), file=sys.stderr)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="KylinAgent benchmark driver (CommandAgent protocol)")
    parser.add_argument("--hermes-home", required=True, help="isolated HERMES_HOME clone for this run")
    parser.add_argument("--runtime-code", required=True, help="path to the engine code (agent-runtime checkout)")
    parser.add_argument("--no-agent", action="store_true", help="offline mapping test: do not construct the agent")
    args = parser.parse_args(argv)

    case = json.loads(sys.stdin.read() or "{}")
    turns: List[Dict[str, Any]] = []
    if args.no_agent:
        turns = [{} for _ in case.get("turns", [])]
    else:
        # The runtime banner/progress writes to stdout; keep it off the evidence
        # stream (CommandAgent parses every stdout line as JSON).
        real_stdout = sys.stdout
        sys.stdout = sys.stderr
        try:
            _ensure_fts_index(args.hermes_home, args.runtime_code)
            agent, _model = _build_agent(args.hermes_home, args.runtime_code)
            for turn in case.get("turns", []) or []:
                turns.append(agent.run_conversation(str(turn.get("user", ""))))
        finally:
            sys.stdout = real_stdout

    for event in map_case_to_events(case, turns):
        sys.stdout.write(json.dumps(event, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
