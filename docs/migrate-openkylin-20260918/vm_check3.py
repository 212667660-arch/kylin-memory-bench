import json
from pathlib import Path

log = Path("/data/usershare/kylin-memory-bench-20260918/migrate-logs")
probe = json.loads((log / "env-probe.stdout.log").read_text(encoding="utf-8"))
print("STATUS", probe.get("status"))
print("CHECKS", json.dumps(probe.get("checks"), ensure_ascii=False, indent=2)[:4000])
print("NOTES", probe.get("notes"))
print("INSTALL_EXIT", (log / "install.exitcode").read_text(encoding="utf-8").strip() if (log / "install.exitcode").is_file() else "missing")
print("INSTALL_STDOUT_TAIL")
print("\n".join((log / "install.stdout.log").read_text(encoding="utf-8", errors="ignore").splitlines()[-20:]))
print("EXIT_CODES_FILE")
print((log / "exit-codes.txt").read_text(encoding="utf-8") if (log / "exit-codes.txt").is_file() else "missing")
