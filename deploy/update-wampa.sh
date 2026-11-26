#!/bin/sh
# Manual / emergency deploy of game2 on the Wampa VPS. Normally the Wampa Auto Deploy service
# (https://wampa.com.br/deploy/) does this by itself after CI passes; both use the same lock, so they never overlap.
# Usage (on the server): sh /srv/game2/deploy/update-wampa.sh [ref]   (default origin/main; deploys the resolved SHA)
# If the new build is not healthy, it goes back to the previous image and commit.
set -eu
REF=${1:-origin/main}
cd /srv/game2
mkdir -p /run/lock/wampa-deploy
exec 9>/run/lock/wampa-deploy/game2.lock
flock -n 9 || { echo "another game2 deploy is running (lock busy); try again in a minute"; exit 75; }
C="docker compose -p game2 -f compose.yaml -f deploy/compose.wampa.yaml"
git fetch -q origin
SHA=$(git rev-parse --verify "$REF^{commit}")
PREV=$(git rev-parse HEAD)
PREV_IMG=$(docker inspect -f '{{.Image}}' game2-web 2>/dev/null || true)
[ -z "$PREV_IMG" ] || docker tag "$PREV_IMG" "game2-web:sha-$(printf %.12s "$PREV")"
healthy() {
  for i in $(seq 1 30); do
    [ "$(docker inspect -f '{{.State.Health.Status}}' game2-web 2>/dev/null)" = healthy ] && break; sleep 3
  done
  docker exec NProxyM curl -fsS -o /dev/null http://game2-web/game2/
}
live_is() { docker exec NProxyM curl -fsS http://game2-web/game2/version.json | grep -q "\"commit\":\"$1\""; }
git -c advice.detachedHead=false checkout -q "$SHA"
AV=$(git rev-parse "$SHA:assets" | cut -c1-12)
if $C build --build-arg GIT_SHA="$SHA" --build-arg ASSET_V="$AV" \
     --build-arg BUILT_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)" game2 2>&1 | tail -2 \
   && $C up -d --no-build game2 2>&1 | tail -1 && healthy && live_is "$SHA"; then
  docker tag game2-web:local "game2-web:sha-$(printf %.12s "$SHA")"
  echo "game2 at $(printf %.7s "$SHA") (was $(printf %.7s "$PREV"))"; exit 0
fi
echo "new build failed health check; going back to $PREV"
git -c advice.detachedHead=false checkout -q "$PREV"
[ -z "$PREV_IMG" ] || docker tag "$PREV_IMG" game2-web:local
$C up -d --no-build game2 2>&1 | tail -1
healthy && echo "restored $PREV"; exit 1
