import json
import kmb
import yaml
from pathlib import Path

root = Path("/data/usershare/kylin-memory-bench-20260918")
log = root / "migrate-logs"
print("kmb_file", kmb.__file__)
print("yaml", yaml.__version__)
print("kmb_under_root", str(kmb.__file__).startswith(str(root)))

probe_path = log / "env-probe.stdout.log"
if probe_path.is_file():
    data = json.loads(probe_path.read_text(encoding="utf-8"))
    openkylin = data.get("openkylin")
    if openkylin is None:
        openkylin = (data.get("system") or {}).get("openkylin")
    print("probe_status", data.get("status"))
    print("openkylin", json.dumps(openkylin, ensure_ascii=False))
    if isinstance(openkylin, dict):
        print("openkylin.ok", openkylin.get("ok"))
else:
    print("probe_missing")

secret_hits = []
for path in log.rglob("*"):
    if not path.is_file():
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    if "sk-" in text and any(ch.isdigit() for ch in text):
        for line in text.splitlines():
            if "sk-" in line and len(line) > 20:
                secret_hits.append(str(path.name))
                break
print("secret_scan", "CLEAN" if not secret_hits else secret_hits)
print("DONE_CHECK")
