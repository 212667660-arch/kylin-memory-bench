#!/usr/bin/env python3
"""Collect platform facts and run local prerequisites without claiming openKylin support."""

import argparse
import importlib
import json
import platform
import shutil
import sys
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _os_release() -> dict:
    path = Path("/etc/os-release")
    if not path.exists():
        return {}
    result = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            result[key] = value.strip().strip('"')
    return result


def collect_probe(suite_path: str = None, require_openkylin: bool = False) -> dict:
    suite = Path(suite_path) if suite_path else ROOT / "suites" / "core-zh.yaml"
    release = _os_release()
    openkylin_id = (release.get("ID", "") + " " + release.get("NAME", "")).lower()
    openkylin_detected = "openkylin" in openkylin_id
    checks = {}
    checks["python"] = {"ok": sys.version_info >= (3, 9), "version": platform.python_version(), "executable": sys.executable}
    try:
        yaml = importlib.import_module("yaml")
        checks["pyyaml"] = {"ok": True, "version": str(getattr(yaml, "__version__", "unknown"))}
    except Exception as exc:
        checks["pyyaml"] = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    try:
        importlib.import_module("kmb.cli")
        checks["cli_import"] = {"ok": True}
    except Exception as exc:
        checks["cli_import"] = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    try:
        from kmb.runner import load_suite, validate_cases
        cases = load_suite(str(suite))
        validate_cases(cases, require_all_capabilities=True)
        checks["core_suite"] = {"ok": True, "path": str(suite), "cases": len(cases)}
    except Exception as exc:
        checks["core_suite"] = {"ok": False, "path": str(suite), "error": "%s: %s" % (type(exc).__name__, exc)}
    checks["dpkg_deb"] = {"ok": shutil.which("dpkg-deb") is not None}
    try:
        disk = shutil.disk_usage(str(ROOT))
        checks["workspace_disk"] = {"ok": disk.free > 5 * 1024 * 1024 * 1024, "path": str(ROOT), "free_gb": round(disk.free / (1024 ** 3), 2)}
    except OSError as exc:
        checks["workspace_disk"] = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    checks["wsl"] = {"ok": shutil.which("wsl") is not None}
    if checks["wsl"]["ok"]:
        try:
            result = subprocess.run(["wsl", "--list", "--quiet"], capture_output=True, text=True, timeout=5, check=False)
            output = result.stdout.replace("\x00", "")
            checks["wsl"]["distributions"] = [line.strip() for line in output.splitlines() if line.strip()]
            checks["wsl"]["list_exit_code"] = result.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            checks["wsl"]["list_error"] = "%s: %s" % (type(exc).__name__, exc)
    checks["docker"] = {"ok": shutil.which("docker") is not None}
    if checks["docker"]["ok"]:
        try:
            docker_result = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)
            checks["docker"]["daemon"] = docker_result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            checks["docker"]["daemon"] = False
    checks["virtualization_tools"] = {
        name: shutil.which(command) is not None
        for name, command in {
            "qemu": "qemu-system-x86_64", "virtualbox": "VBoxManage",
            "vmware": "vmrun", "libvirt": "virsh", "podman": "podman",
        }.items()
    }
    checks["hyperv"] = {"ok": shutil.which("Get-VM") is not None or os.name != "nt"}
    checks["openkylin"] = {"ok": openkylin_detected, "required": require_openkylin, "os_release": release}
    local_names = ("python", "pyyaml", "cli_import", "core_suite")
    local_ok = all(checks[name]["ok"] for name in local_names)
    overall_ok = local_ok and (openkylin_detected if require_openkylin else True)
    return {
        "status": "ok" if overall_ok else "failed",
        "environment": {"system": platform.system(), "release": platform.release(), "machine": platform.machine(), "platform": platform.platform()},
        "checks": checks,
        "notes": [
            "openKylin compatibility is not inferred from another operating system.",
            "dpkg-deb is reported for packaging readiness only; it is not required for local CLI execution.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="KylinMemoryBench environment probe")
    parser.add_argument("--suite", default=None)
    parser.add_argument("--require-openkylin", action="store_true")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    payload = collect_probe(args.suite, args.require_openkylin)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("status: %s" % payload["status"])
        for name, check in payload["checks"].items():
            print("%s: %s" % (name, "ok" if check["ok"] else "failed"))
    return 0 if payload["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
