FROM nginx:1.27-alpine
# Filled by the Wampa Auto Deploy (and by deploy/update-wampa.sh); local builds still work with the defaults.
ARG GIT_SHA=dev
ARG ASSET_V=
ARG BUILT_AT=
LABEL org.opencontainers.image.source="https://github.com/lucas-neme/game2" \
      org.opencontainers.image.revision="${GIT_SHA}"
COPY index.html /usr/share/nginx/html/game2/index.html
COPY assets /usr/share/nginx/html/game2/assets
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/stamp.sh /tmp/stamp.sh
RUN sh /tmp/stamp.sh /usr/share/nginx/html/game2 "$GIT_SHA" "$ASSET_V" "$BUILT_AT" && rm /tmp/stamp.sh && nginx -t
RUN exit 1
EXPOSE 80
