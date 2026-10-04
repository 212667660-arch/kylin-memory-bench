import argparse
import json
from pathlib import Path

from .agents import build_agent, build_agent_from_config, load_agent_config
from .report import radar_svg, write_compare, write_html_report, write_markdown
from .runner import load_suite, run_suite, validate_cases


def _agent_name(value: str) -> str:
    path = Path(value)
    if path.exists():
        config = load_agent_config(str(path))
        return str(config.get("name") or config.get("type") or "reference")
    return value


def _build_agent(value: str):
    path = Path(value)
    if path.exists():
        return build_agent_from_config(str(path))
    return build_agent(_agent_name(value))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="kmb", description="Evidence-based long-term memory benchmark")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one agent")
    run.add_argument("--agent", required=True)
    run.add_argument("--suite", required=True)
    run.add_argument("--out", default="runs/run")
    run.add_argument("--retries", type=int, default=0)
    run.add_argument("--seed", type=int, default=None)
    run.add_argument("--run-id", default=None)
    run.add_argument("--timeout", type=float, default=30.0, help="maximum seconds per case")
    compare = sub.add_parser("compare", help="compare agents")
    compare.add_argument("--agents", nargs="+", required=True)
    compare.add_argument("--suite", required=True)
    compare.add_argument("--out", default="runs/compare")
    compare.add_argument("--retries", type=int, default=0)
    compare.add_argument("--seed", type=int, default=None)
    compare.add_argument("--run-id", default=None)
    compare.add_argument("--timeout", type=float, default=30.0, help="maximum seconds per case")
    validate = sub.add_parser("validate", help="validate a suite")
    validate.add_argument("--suite", required=True)
    validate.add_argument("--strict", action="store_true", help="require all six benchmark capabilities")
    list_cases = sub.add_parser("list-cases", help="list suite cases")
    list_cases.add_argument("--suite", required=True)
    serve = sub.add_parser("serve", aliases=["workbench"], help="start the local browser workbench")
    serve.add_argument("--host", default="127.0.0.1", help="bind address (default: loopback only)")
    serve.add_argument("--port", type=int, default=8765, help="listen port")
    serve.add_argument("--root", default=".", help="project workspace root")
    discover = sub.add_parser("discover-agents", help="discover supported Agents already installed on this host")
    discover.add_argument("--root", default=".", help="project workspace root")
    discover.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON (the default output format)",
    )
    quick = sub.add_parser("quick-compare", help="compare two installed Agents with fixed benchmark parameters")
    quick.add_argument("--agents", nargs=2, metavar=("AGENT_A", "AGENT_B"), help="two discovered Agent ids")
    quick.add_argument("--out", default="", help="result directory (default: runs/quick-compare-<id>)")
    quick.add_argument("--root", default=".", help="project workspace root")
    quick.add_argument("--preflight-only", action="store_true", help="read-only readiness check; starts no Agent turns and consumes no Tokens")
    official = sub.add_parser("official-acceptance", help="run the one-command official acceptance path")
    official.add_argument("--out", default="runs/official-acceptance")
    official.add_argument("--mode", choices=("offline", "installed"), default="offline")
    official.add_argument("--agent-a", default=None)
    official.add_argument("--agent-b", default=None)
    official.add_argument("--repeats", type=int, default=1)
    repeat = sub.add_parser("official-repeat", help="run isolated repeat batches against two installed Agents")
    repeat.add_argument("--agents", nargs=2, required=True, metavar=("AGENT_A", "AGENT_B"))
    repeat.add_argument("--suite", default="suites/quick.yaml")
    repeat.add_argument("--repeats", type=int, default=3)
    repeat.add_argument("--seed", type=int, default=42)
    repeat.add_argument("--timeout", type=float, default=180.0)
    repeat.add_argument("--isolated-home", action="store_true", required=True)
    repeat.add_argument("--out", required=True)
    register = sub.add_parser(
        "register-agent",
        help="register an OpenAI-compatible model as http + memory_controller + memory_disabled pack",
    )
    register.add_argument("--name", required=True, help="display name, e.g. OpenRouter or MyBot")
    register.add_argument("--base-url", required=True, help="e.g. https://api.example.com/v1")
    register.add_argument("--model", required=True, help="model id sent to the API")
    register.add_argument(
        "--api-key-env",
        default="",
        help="environment variable name that holds the API key (value is never saved)",
    )
    register.add_argument("--endpoint", default="/chat/completions")
    register.add_argument("--temperature", type=float, default=0.0)
    register.add_argument("--timeout", type=int, default=180)
    register.add_argument(
        "--id",
        default="",
        help="config file id (default: slug of --name). Files become agent-<id>*.yaml",
    )
    register.add_argument(
        "--configs-dir",
        default="configs",
        help="directory for agent YAML files (default: configs)",
    )
    args = parser.parse_args(argv)
    if args.command in ("serve", "workbench"):
        from .workbench import serve as serve_workbench
        serve_workbench(root=args.root, host=args.host, port=args.port)
        return 0
    if args.command == "discover-agents":
        from .agent_registry import discover_agents, profiles_to_dicts
        print(json.dumps({"agents": profiles_to_dicts(discover_agents(Path(args.root).resolve()))}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "quick-compare":
        from .quick_compare import QuickCompareOptions, run_quick_compare
        try:
            result = run_quick_compare(
                QuickCompareOptions(agent_ids=args.agents, out_dir=args.out, preflight_only=getattr(args, "preflight_only", False)),
                root=Path(args.root).resolve(),
            )
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise SystemExit(str(exc))
        print(json.dumps({
            "run_id": result["run_id"],
            "agents": [item["id"] for item in result["agents"]],
            "out": result["result_directory"],
            "parameters": result["parameters"],
        }, ensure_ascii=False))
        return 0
    if args.command == "official-acceptance":
        from scripts.official_acceptance import run_official_acceptance
        result = run_official_acceptance(args.out, args.mode, args.agent_a, args.agent_b, args.repeats)
        print(json.dumps({"status": result.status, "exit_code": result.exit_code, "out": str(Path(args.out).resolve())}, ensure_ascii=False))
        return result.exit_code
    if args.command == "official-repeat":
        from scripts.official_repeat import run_official_repeat
        try:
            summary = run_official_repeat(
                args.agents,
                args.out,
                repeats=args.repeats,
                suite=args.suite,
                seed=args.seed,
                timeout=args.timeout,
            )
        except (FileNotFoundError, RuntimeError, ValueError, FileExistsError) as exc:
            raise SystemExit(str(exc))
        print(json.dumps({
            "status": summary["status"],
            "agents": summary["agents"],
            "repeats": summary["repeats"],
            "out": str(Path(args.out).resolve()),
        }, ensure_ascii=False))
        return 0 if summary["status"] == "completed" else 3 if summary["status"] == "partial" else 2
    if args.command == "register-agent":
        from .register import register_from_args
        try:
            register_from_args(
                name=args.name,
                base_url=args.base_url,
                model=args.model,
                api_key_env=args.api_key_env,
                endpoint=args.endpoint,
                temperature=args.temperature,
                timeout=args.timeout,
                agent_id=args.id,
                configs_root=Path(args.configs_dir),
            )
        except (ValueError, FileExistsError) as exc:
            raise SystemExit(str(exc))
        return 0
    cases = load_suite(args.suite)
    if args.command == "validate":
        validate_cases(cases, require_all_capabilities=args.strict)
        print(json.dumps({"suite": args.suite, "cases": len(cases), "status": "valid"}, ensure_ascii=False))
        return 0
    if args.command == "list-cases":
        for case in cases:
            print("%s\t%s\t%s" % (case.id, case.capability, case.title))
        return 0
    if args.command == "run":
        agent = _build_agent(args.agent)
        summary = run_suite(agent, cases, args.out, timeout_seconds=args.timeout, retries=args.retries, run_id=args.run_id, seed=args.seed)
        write_markdown(summary, str(Path(args.out) / "result.md"))
        (Path(args.out) / "radar.svg").write_text(radar_svg(summary["dimensions"], score_valid=summary.get("score_valid", True)), encoding="utf-8")
        write_html_report([summary], str(Path(args.out) / "result.html"))
        print(json.dumps({"agent": summary["agent"], "overall": summary["overall"], "out": args.out}, ensure_ascii=False))
        return 0
    names = [_agent_name(value) for value in args.agents]
    if len(names) < 2:
        raise ValueError("compare requires at least two agents")
    if len(set(names)) != len(names):
        raise ValueError("compare requires distinct agent names")
    summaries = []
    for value in args.agents:
        name = _agent_name(value)
        summaries.append(run_suite(_build_agent(value), cases, str(Path(args.out) / name), timeout_seconds=args.timeout, retries=args.retries, run_id=args.run_id, seed=args.seed))
    write_compare(summaries, args.out)
    print(json.dumps({"agents": [item["agent"] for item in summaries], "out": args.out}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
