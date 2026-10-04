#!/usr/bin/env bash
set -u
REMOTE_ROOT=/data/usershare/kylin-memory-bench-20260918
LOGDIR=$REMOTE_ROOT/migrate-logs
KMB=$REMOTE_ROOT/.kmb-venv/bin/python
cd $REMOTE_ROOT || exit 1
codes=$LOGDIR/exit-codes.txt
: > $codes
run() {
  name=$1; shift
  echo === $name ===
  $@ > $LOGDIR/$name.stdout.log 2> $LOGDIR/$name.stderr.log
  ec=$?
  echo $name=$ec | tee -a $codes
  tail -n 15 $LOGDIR/$name.stdout.log || true
  if [ -s $LOGDIR/$name.stderr.log ]; then echo -- stderr tail --; tail -n 10 $LOGDIR/$name.stderr.log; fi
  return $ec
}
run uname-a uname -a
run os-release cat /etc/os-release
run python3-version python3 --version
run kmb-python-version $KMB --version
run import-kmb $KMB -c 'import kmb, yaml; print(kmb.__file__)'
run env-probe $KMB scripts/env_probe.py --require-openkylin --json
run unittest $KMB -m unittest discover -s tests -v
run validate-core $KMB -m kmb.cli validate --strict --suite suites/core-zh.yaml
echo DONE codes:
cat $codes
