#!/bin/bash
# Put a commit of the site in place on the Oracle server and (re)start it.
#
#   sudo bash deploy.sh <commit or origin/dev> <host>    < the settings (KEY=value lines)
#
# Run by .github/workflows/deploy-oracle.yml over SSH; the settings come
# from the repository secret ORACLE_APP_ENV. <host> is the server's public
# IP or domain: an IP is served as <ip with dashes>.sslip.io, a free name
# that points at it, so Caddy can get an HTTPS certificate.
set -euo pipefail
commit="$1"
host="$2"
site=/srv/app/site
venv=/srv/app/venv
env_file=/etc/langsite/env

# The settings, only readable by root (systemd reads them for the app).
umask 077
cat > "$env_file.new"
mv "$env_file.new" "$env_file"
umask 022

sudo -u app git -C "$site" fetch -q origin dev
sudo -u app git -C "$site" checkout -q --force "$commit"

if [ ! -x "$venv/bin/python" ]; then
  sudo -u app uv venv --python 3.11 "$venv"
fi
sudo -u app env VIRTUAL_ENV="$venv" uv pip install -q -r "$site/requirements.txt"

# Migrations and the idempotent seeds, as on Render.
# The settings are read line by line (KEY=value, as systemd reads them),
# not sourced, so that & or ? in a database address stay as they are.
run_flask() {
  sudo -u app bash -c '
    while IFS= read -r line || [ -n "$line" ]; do
      line="${line%$'"'"'\r'"'"'}"
      [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] && export "$line"
    done
    cd "$0" && FLASK_APP=run.py "$1/bin/flask" "${@:2}"
  ' "$site" "$venv" "$@" < "$env_file"
}
run_flask db upgrade
run_flask vocabulary seed --update
run_flask vocabulary dacco-import
run_flask vocabulary apertium-words
run_flask vocabulary extra-words
run_flask vocabulary apertium-import
run_flask vocabulary pivot-import
run_flask grammar seed

cat > /etc/systemd/system/langsite.service <<UNIT
[Unit]
Description=Language learning site (gunicorn)
After=network-online.target
Wants=network-online.target

[Service]
User=app
Group=app
WorkingDirectory=$site
EnvironmentFile=$env_file
Environment=FLASK_APP=run.py
ExecStart=$venv/bin/gunicorn run:app --bind 127.0.0.1:8000 --workers 2 --threads 4 --timeout 120 --max-requests 2000 --max-requests-jitter 200
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

if [[ "$host" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  domain="${host//./-}.sslip.io"
else
  domain="$host"
fi
cat > /etc/caddy/Caddyfile <<CADDY
$domain {
	encode gzip
	reverse_proxy 127.0.0.1:8000
}
CADDY

systemctl daemon-reload
systemctl enable --now langsite
systemctl restart langsite
systemctl reload caddy || systemctl restart caddy

for attempt in $(seq 1 30); do
  if curl -fsS -o /dev/null http://127.0.0.1:8000/; then
    echo "Deployed $commit: https://$domain/"
    exit 0
  fi
  sleep 2
done
journalctl -u langsite -n 50 --no-pager
echo "The site did not answer." >&2
exit 1
