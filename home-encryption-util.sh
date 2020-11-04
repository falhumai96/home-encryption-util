#!/usr/bin/env sh

HOME_ENCRYPTION_UTIL_DIR="$(cd "$(dirname $(readlink -f "${BASH_SOURCE[0]}"))" >/dev/null 2>&1 && pwd)"
python3 "$HOME_ENCRYPTION_UTIL_DIR/lib/main.py" "$@"
exit $?
