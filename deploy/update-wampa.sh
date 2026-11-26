#!/bin/sh
# Updates game2 on the Wampa VPS to a commit (default: origin/main) and checks health.
# Usage (on the server): sh /srv/game2/deploy/update-wampa.sh [ref]
# If the new build is not healthy, it goes back to the previous commit.
set -eu
REF=${1:-origin/main}
cd /srv/game2
up() { docker compose -p game2 -f compose.yaml -f deploy/compose.wampa.yaml up -d --build --quiet-pull 2>&1 | tail -2; }
ok() {
  for i in $(seq 1 30); do
    [ "$(docker inspect -f '{{.State.Health.Status}}' game2-web 2>/dev/null)" = healthy ] && break; sleep 3
  done
  curl -fsS -o /dev/null http://127.0.0.1:8092/game2/ && docker exec NProxyM curl -fsS -o /dev/null http://game2-web/game2/
}
git fetch -q origin
PREV=$(git rev-parse HEAD)
git -c advice.detachedHead=false checkout -q "$REF"
if up && ok; then echo "game2 at $(git rev-parse --short HEAD) (was ${PREV%${PREV#???????}})"; exit 0; fi
echo "new build failed health check; going back to $PREV"
git -c advice.detachedHead=false checkout -q "$PREV"; up; ok && echo "restored $PREV"; exit 1
