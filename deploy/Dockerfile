FROM nginx:1.27-alpine
COPY index.html /usr/share/nginx/html/game2/index.html
COPY assets /usr/share/nginx/html/game2/assets
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
RUN nginx -t
EXPOSE 80
