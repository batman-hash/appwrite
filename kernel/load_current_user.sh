#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
MODULE_PATH="$SCRIPT_DIR/linux_kernel_bridge.ko"

if [[ ! -f "$MODULE_PATH" ]]; then
	echo "Missing $MODULE_PATH. Run 'make' in kernel/ first." >&2
	exit 1
fi

# When this runs under sudo, whoami would report root, so preserve the caller.
current_user="${SUDO_USER:-$(whoami)}"
allowed_uid="$(id -u "$current_user")"

echo "Loading linux_kernel_bridge for user '$current_user' (uid $allowed_uid)"

if [[ $EUID -eq 0 ]]; then
	exec insmod "$MODULE_PATH" "allowed_uid=$allowed_uid"
fi

exec sudo insmod "$MODULE_PATH" "allowed_uid=$allowed_uid"
