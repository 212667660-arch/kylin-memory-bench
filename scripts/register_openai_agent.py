#!/usr/bin/env python3
"""CLI wrapper: register an OpenAI-compatible model as a KMB agent pack.

Delegates to ``kmb.register`` so this script and
``python -m kmb.cli register-agent`` share one implementation.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kmb.register import register_from_args  # noqa: E402


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Register an OpenAI-compatible model as wrapped KMB agents")
    parser.add_argument("--name", required=True, help="display name, e.g. OpenRouter or MyBot")
    parser.add_argument("--base-url", required=True, help="e.g. https://api.example.com/v1")
    parser.add_argument("--model", required=True, help="model id sent to the API")
    parser.add_argument(
        "--api-key-env",
        default="",
        help="environment variable name that holds the API key (value is never saved)",
    )
    parser.add_argument("--endpoint", default="/chat/completions")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument(
        "--id",
        default="",
        help="config file id (default: slug of --name). Files become agent-<id>*.yaml",
    )
    parser.add_argument("--configs-dir", default=str(ROOT / "configs"))
    args = parser.parse_args(argv)
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
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
