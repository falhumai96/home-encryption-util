#!/usr/bin/env sh

if [ -z "$HOME_ENCRYPTION_UTIL_INSTALL_PREFIX" ]; then
    export HOME_ENCRYPTION_UTIL_INSTALL_PREFIX="/usr"
fi
if [ -z "$HOME_ENCRYPTION_UTIL_INSTALL" ]; then
    export HOME_ENCRYPTION_UTIL_INSTALL="/opt/home-encryption-util"
fi
HOME_ENCRYPTION_UTIL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

rm -rf "$HOME_ENCRYPTION_UTIL_INSTALL"
rm -f "$HOME_ENCRYPTION_UTIL_INSTALL_PREFIX/bin/home-encryption-util"
