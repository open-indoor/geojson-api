#!/bin/bash
set -x
set -e

chmod +x /geojson/geojson
chmod +x /usr/bin/action
chmod +x /usr/bin/tic

crontab -l | { cat; echo "* * * * * /usr/bin/tic >/dev/stdout 2>/dev/stderr"; } | crontab -
echo "Start cron task" && crontab -l && /usr/sbin/cron -l 8
cat /usr/bin/action

# cat /tmp/Caddyfile | envsubst | tee /etc/caddy/Caddyfile
cat /etc/caddy/Caddyfile

(caddy run --watch --config /etc/caddy/Caddyfile & fcgiwrap -f -s unix:/var/run/fcgiwrap.socket)
