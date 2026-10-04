import json
import re
from pathlib import Path

log = Path("/data/usershare/kylin-memory-bench-20260918/migrate-logs")
probe = json.loads((log / "env-probe.stdout.log").read_text(encoding="utf-8"))
print("PROBE_KEYS", list(probe.keys()))
print("PROBE_STATUS", probe.get("status"))
for key in ("openkylin", "system", "environment", "platform"):
    if key in probe:
        val = probe[key]
        text = json.dumps(val, ensure_ascii=False)
        print("PROBE_%s" % key.upper(), text[:1500])

uni = (log / "unittest.stderr.log").read_text(encoding="utf-8", errors="ignore")
print("UNITTEST_TAIL")
print("\n".join(uni.splitlines()[-30:]))

syslog = log / "system-scenarios-rerun.log"
if syslog.is_file():
    print("SYS_RERUN_TAIL")
    print("\n".join(syslog.read_text(encoding="utf-8", errors="ignore").splitlines()[-25:]))

# secret scan excluding this checker
hits = []
for path in log.iterdir():
    if not path.is_file() or path.name in ("vm_check.py", "vm_check2.py", "vm_check.out"):
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    if re.search(r"sk-[A-Za-z0-9]{16,}", text):
        hits.append(path.name)
print("SECRET_SCAN", "CLEAN" if not hits else hits)
print("LOG_FILES")
for p in sorted(log.iterdir()):
    if p.is_file():
        print(p.name, p.stat().st_size)
