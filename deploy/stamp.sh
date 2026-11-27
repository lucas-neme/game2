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
  # 1) per-file versions: every literal asset path naming an existing file points to v/<sha256[:12] of that file>/, so a
  #    deploy only changes the URLs of files that really changed; the rest stays cached in browsers and at the Cloudflare
  #    edge (a tree-wide version made every player refetch ~10 MB through the slow origin path after each asset change).
  grep -oE "[\"'\`(]assets/[A-Za-z0-9_./-]+" "$D/index.html" | cut -c2- | sort -u \
    | awk '{print length($0) " " $0}' | sort -rn | cut -d' ' -f2- > /tmp/stamp-refs
  n=0
  while IFS= read -r p; do
    f="$D/$p"; [ -f "$f" ] || continue
    h=$(sha256sum "$f" | cut -c1-12)
    q=$(printf %s "$p" | sed 's/[.]/[.]/g')
    sed -i -E "s|([\"'\`(])$q([\"'\`)?#])|\1v/$h/$p\2|g" "$D/index.html"
    n=$((n+1))
  done < /tmp/stamp-refs
  rm -f /tmp/stamp-refs
  # 2) paths assembled at runtime keep the assets-tree version
  sed -i -E "s#([\"'\`(])assets/#\1v/$AV/assets/#g" "$D/index.html"
  echo "stamp: $n asset files versioned by content"
fi
SHORT=$(printf %.7s "$SHA")
printf '\n<div id="wampa-build" data-commit="%s" aria-hidden="true" style="position:fixed;right:6px;bottom:4px;font:10px/1 ui-monospace,Consolas,monospace;color:#fff;opacity:.3;pointer-events:none;z-index:2147483647;text-shadow:0 0 2px #000">v %s</div>\n' \
  "$SHA" "$SHORT" >> "$D/index.html"
