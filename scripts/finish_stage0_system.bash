#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  printf 'Run this script with sudo: sudo bash %s\n' "$0" >&2
  exit 2
fi

apt-get update
apt-get install -y --no-install-recommends ubuntu-drivers-common
driver_package="$(ubuntu-drivers devices | awk '/recommended/{print $3; exit}')"
if [[ -z "$driver_package" ]]; then
  printf 'No recommended NVIDIA driver was reported. Stop and inspect ubuntu-drivers devices.\n' >&2
  exit 3
fi
apt-get install -y --no-install-recommends "$driver_package"

if [[ -z "$(swapon --noheadings --show=NAME)" ]]; then
  if [[ ! -e /swapfile ]]; then
    fallocate -l 16G /swapfile
  fi
  chmod 600 /swapfile
  if ! file /swapfile | grep -q 'swap file'; then
    mkswap /swapfile
  fi
  swapon /swapfile
fi

if ! grep -qE '^/swapfile[[:space:]]' /etc/fstab; then
  printf '/swapfile none swap sw 0 0\n' | tee -a /etc/fstab >/dev/null
fi

printf '\nInstalled %s and configured swap. Reboot, then run:\n' "$driver_package"
printf '  nvidia-smi\n  swapon --show\n'
