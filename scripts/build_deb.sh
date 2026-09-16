#!/usr/bin/env bash
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
OUTPUT_DIR="${1:-$ROOT/dist}"
VERSION="${KMB_DEB_VERSION:-$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$ROOT/pyproject.toml" | head -n 1)}"

if ! command -v dpkg-deb >/dev/null 2>&1; then
  printf '%s\n' 'dpkg-deb is required; run this script on openKylin or another Debian build host.' >&2
  exit 2
fi
if [ -z "$VERSION" ] || ! printf '%s' "$VERSION" | grep -Eq '^[0-9][A-Za-z0-9.+:~_-]*$'; then
  printf 'invalid Debian package version: %s\n' "$VERSION" >&2
  exit 2
fi

mkdir -p "$OUTPUT_DIR"
STAGE="$(mktemp -d "${TMPDIR:-/tmp}/kmb-deb.XXXXXX")"
trap 'rm -rf -- "$STAGE"' EXIT HUP INT TERM
PACKAGE_ROOT="$STAGE/kylin-memory-bench_${VERSION}_all"
PAYLOAD="$PACKAGE_ROOT/usr/share/kylin-memory-bench"
DOCROOT="$PACKAGE_ROOT/usr/share/doc/kylin-memory-bench"
mkdir -p "$PACKAGE_ROOT/DEBIAN" "$PACKAGE_ROOT/usr/bin" "$PAYLOAD" "$DOCROOT"

sed "s/@VERSION@/$VERSION/g" "$ROOT/packaging/deb/control.in" > "$PACKAGE_ROOT/DEBIAN/control"
install -m 0755 "$ROOT/packaging/deb/kmb-launcher" "$PACKAGE_ROOT/usr/bin/kmb"
install -m 0644 "$ROOT/README.md" "$ROOT/CHANGELOG.md" "$ROOT/NOTICE" "$ROOT/THIRD_PARTY_NOTICES.md" "$ROOT/LICENSE-MIT-CANDIDATE.txt" "$DOCROOT/"
install -m 0644 "$ROOT/packaging/deb/copyright" "$DOCROOT/copyright"

for path in kmb configs suites docs pyproject.toml setup.py; do
  if [ ! -e "$ROOT/$path" ]; then
    printf 'required release path is missing: %s\n' "$path" >&2
    exit 2
  fi
  cp -a "$ROOT/$path" "$PAYLOAD/"
done
mkdir -p "$PAYLOAD/scripts"
install -m 0755 "$ROOT/scripts/verify_run.py" "$PAYLOAD/scripts/verify_run.py"
install -m 0755 "$ROOT/scripts/rescore_run.py" "$PAYLOAD/scripts/rescore_run.py"
install -m 0755 "$ROOT/scripts/aggregate_repeats.py" "$PAYLOAD/scripts/aggregate_repeats.py"
install -m 0755 "$ROOT/scripts/aggregate_stability.py" "$PAYLOAD/scripts/aggregate_stability.py"
install -m 0755 "$ROOT/scripts/system_scenarios.py" "$PAYLOAD/scripts/system_scenarios.py"
mkdir -p "$PAYLOAD/tests"
install -m 0755 "$ROOT/packaging/deb/smoke_test.py" "$PAYLOAD/tests/smoke_test.py"

# The package must never ship credentials, local environments, research cache,
# generated results, package artifacts, or Python bytecode.
find "$PAYLOAD" -type d \( -name '__pycache__' -o -name '.kmb-venv' -o -name '.venv-*' -o -name '.pip-cache*' -o -name '.tmp-*' -o -name 'runs' \) -prune -exec rm -rf {} +
if find "$PAYLOAD" -type f \( -name '*.pyc' -o -name '.env' -o -name 'credentials.env' \) -print -quit | grep -q .; then
  printf '%s\n' 'release staging contains forbidden credential or bytecode files.' >&2
  exit 2
fi

PACKAGE_PATH="$OUTPUT_DIR/kylin-memory-bench_${VERSION}_all.deb"
dpkg-deb --build --root-owner-group "$PACKAGE_ROOT" "$PACKAGE_PATH" >/dev/null
printf 'built: %s\n' "$PACKAGE_PATH"
dpkg-deb --info "$PACKAGE_PATH"
dpkg-deb --contents "$PACKAGE_PATH"
