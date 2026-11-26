#!/bin/sh
# Build-time stamp (run by deploy/Dockerfile):
#  - version.json with the exact commit, so anyone can check what is live (/game2/version.json);
#  - cache busting: every string in index.html that starts with assets/ points to v/<hash of the assets tree>/assets/,
#    served as immutable by nginx. The hash only changes when a file under assets/ changes, so code-only deploys keep
#    the browser and Cloudflare caches, and asset changes always reach the player (no stale sprites after a deploy);
#  - a discreet version badge in the corner (pointer-events: none).
set -eu
D=$1; SHA=$2; AV=$3; AT=${4:-}
[ -n "$AT" ] || AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '{"project":"game2","commit":"%s","asset_version":"%s","built_at":"%s","deployed_at":"%s","environment":"production"}\n' \
  "$SHA" "$AV" "$AT" "$AT" > "$D/version.json"
if [ -n "$AV" ]; then
  case "$AV" in *[!0-9a-f]*) echo "ASSET_V must be hex" >&2; exit 2;; esac
  sed -i -E "s#([\"'\`(])assets/#\1v/$AV/assets/#g" "$D/index.html"
fi
SHORT=$(printf %.7s "$SHA")
printf '\n<div id="wampa-build" data-commit="%s" aria-hidden="true" style="position:fixed;right:6px;bottom:4px;font:10px/1 ui-monospace,Consolas,monospace;color:#fff;opacity:.3;pointer-events:none;z-index:2147483647;text-shadow:0 0 2px #000">v %s</div>\n' \
  "$SHA" "$SHORT" >> "$D/index.html"
