#!/usr/bin/env bash
set -euo pipefail

# Template IO injector: create background sync-heavy writes.
# Adapt path/size to stay VM-friendly.

DIR=${DIR:-/tmp/inc_io}
DURATION=${DURATION:-30}

mkdir -p "${DIR}"

echo "[inject] io/writeback: dir=${DIR} duration=${DURATION}s" >&2

# Simple portable approach: repeated small fsyncs.
python3 - <<'PY' &
import os, time
p = os.environ.get('DIR','/tmp/inc_io')
dur = int(os.environ.get('DURATION','30'))
end = time.time() + dur
fn = os.path.join(p, 'fsync.log')
with open(fn, 'ab', buffering=0) as f:
    i = 0
    while time.time() < end:
        f.write(b'x'*4096)
        os.fsync(f.fileno())
        i += 1
PY

echo $! > io.pid
