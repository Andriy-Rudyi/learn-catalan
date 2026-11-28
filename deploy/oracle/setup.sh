#!/bin/bash
# First boot of the Oracle Cloud server (Ubuntu 24.04: Ampere A1, or the
# small AMD VM.Standard.E2.1.Micro while no Ampere server is available).
#
# Paste into "Initialization script" when creating the instance (or run
# once with sudo). It installs what the site needs; the site itself is
# put in place and started by deploy.sh, which the GitHub workflow
# .github/workflows/deploy-oracle.yml runs over SSH after every push to dev.
#
#   /srv/app/site   the repository (branch dev)
#   /srv/app/venv   Python 3.11 with requirements.txt
#   /etc/langsite/env  the site's settings (written by deploy.sh)
#   gunicorn on 127.0.0.1:8000 (systemd: langsite), Caddy in front with HTTPS
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y git curl gnupg debian-keyring debian-archive-keyring apt-transport-https \
  iptables-persistent unattended-upgrades

# A swap file, so the small Always Free AMD server (1 GB of memory) gets
# through installing the packages and the seeds.
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# Oracle's Ubuntu images only let SSH in: open the web ports too (the
# instance's security list must allow them as well).
for port in 443 80; do
  iptables -C INPUT -p tcp --dport "$port" -m state --state NEW -j ACCEPT 2>/dev/null ||
    iptables -I INPUT 5 -p tcp --dport "$port" -m state --state NEW -j ACCEPT
done
netfilter-persistent save

# Caddy: the web server in front, with free automatic HTTPS certificates.
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key |
  gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
  -o /etc/apt/sources.list.d/caddy-stable.list
apt-get update
apt-get install -y caddy

# uv installs Python 3.11 (the version the site runs on) and the packages.
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh

id app >/dev/null 2>&1 || useradd --system --create-home --home-dir /srv/app --shell /usr/sbin/nologin app
mkdir -p /etc/langsite
if [ ! -d /srv/app/site/.git ]; then
  sudo -u app git clone --branch dev https://github.com/Andriy-Rudyi/learn-catalan.git /srv/app/site
fi
echo "Server ready; the site is installed by the first deploy."
