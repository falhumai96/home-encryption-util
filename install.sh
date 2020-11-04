#!/usr/bin/env sh

if [ -z "$HOME_ENCRYPTION_UTIL_INSTALL_PREFIX" ]; then
    export HOME_ENCRYPTION_UTIL_INSTALL_PREFIX="/usr"
fi
if [ -z "$HOME_ENCRYPTION_UTIL_INSTALL" ]; then
    export HOME_ENCRYPTION_UTIL_INSTALL="/opt/home-encryption-util"
fi
HOME_ENCRYPTION_UTIL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

mkdir -p "$HOME_ENCRYPTION_UTIL_INSTALL_PREFIX/bin"
mkdir -p "$HOME_ENCRYPTION_UTIL_INSTALL"
cp -R "$HOME_ENCRYPTION_UTIL_DIR/lib" "$HOME_ENCRYPTION_UTIL_INSTALL"
cp "$HOME_ENCRYPTION_UTIL_DIR/home-encryption-util.sh" "$HOME_ENCRYPTION_UTIL_INSTALL"
rm -f "$HOME_ENCRYPTION_UTIL_INSTALL_PREFIX/bin/home-encryption-util"
ln -s "$HOME_ENCRYPTION_UTIL_INSTALL/home-encryption-util.sh" "$HOME_ENCRYPTION_UTIL_INSTALL_PREFIX/bin/home-encryption-util"
chmod a+x "$HOME_ENCRYPTION_UTIL_INSTALL/home-encryption-util.sh"
chmod a+x "$HOME_ENCRYPTION_UTIL_INSTALL_PREFIX/bin/home-encryption-util"
chmod a+rx -R "$HOME_ENCRYPTION_UTIL_INSTALL"
