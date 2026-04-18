#!/usr/bin/env bash

set -u

status=0

say() {
  printf '%s %s\n' "$1" "$2"
}

check_cmd() {
  local cmd="$1"
  local level_missing="${2:-ERROR}"
  if command -v "$cmd" >/dev/null 2>&1; then
    say "[OK]" "$cmd: $(command -v "$cmd")"
  else
    say "[$level_missing]" "$cmd not found"
    [[ "$level_missing" == "ERROR" ]] && status=1
  fi
}

kernel_ok() {
  local os kernel
  os="$(uname -s)"
  if [[ "$os" != "Linux" ]]; then
    say "[ERROR]" "unsupported OS: $os (run this inside Ubuntu Linux)"
    status=1
    return
  fi

  kernel="$(uname -r | cut -d- -f1)"
  if printf '%s\n%s\n' "5.10" "$kernel" | sort -V -C; then
    say "[OK]" "kernel $kernel >= 5.10"
  else
    say "[ERROR]" "kernel $kernel < 5.10"
    status=1
  fi
}

perf_smoke() {
  if ! command -v perf >/dev/null 2>&1; then
    say "[ERROR]" "perf not found"
    status=1
    return
  fi

  if sudo -n perf stat true >/dev/null 2>&1; then
    say "[OK]" "sudo -n perf stat true succeeded"
  else
    say "[WARN]" "perf exists, but sudo -n perf stat true did not run without prompting; try 'sudo perf stat true' manually"
  fi
}

say "[INFO]" "Modern Operating Systems environment check"
kernel_ok
check_cmd gcc
check_cmd make
check_cmd git
check_cmd strace
check_cmd valgrind
check_cmd node
check_cmd npm
check_cmd perf
check_cmd /usr/bin/time
check_cmd bpftrace WARN
perf_smoke

if [[ $status -eq 0 ]]; then
  say "[OK]" "environment check passed"
else
  say "[ERROR]" "environment check failed"
fi

exit $status
