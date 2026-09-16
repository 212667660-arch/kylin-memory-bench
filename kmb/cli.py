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
    args = parser.parse_args(argv)
    if args.command in ("serve", "workbench"):
        from .workbench import serve as serve_workbench
        serve_workbench(root=args.root, host=args.host, port=args.port)
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
        (Path(args.out) / "radar.svg").write_text(radar_svg(summary["dimensions"]), encoding="utf-8")
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
