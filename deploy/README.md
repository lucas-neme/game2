# Publicação independente — /game2/

Publicado em **https://wampa.com.br/game2/** (VPS Wampa, 26/11/2026). O jogo é estático: não usa Vanguarda, banco,
credenciais nem serviços do PC local; o progresso fica no `localStorage` do navegador.

## Como está montado na VPS

- Clone em `/srv/game2`, preso a um commit testado (checkout destacado).
- Container `game2-web` (imagem `game2-web:local`, `nginx:1.27-alpine`), projeto compose `game2`:
  `docker compose -p game2 -f compose.yaml -f deploy/compose.wampa.yaml up -d --build`.
  Limite de 64 MB, `no-new-privileges`, logs rotacionados, healthcheck em `/healthz`.
- Porta `127.0.0.1:8092` só para conferência no host (estava livre antes da subida). O tráfego público não passa por ela.
- O Nginx Proxy Manager alcança o container pela rede `proxynet` como `game2-web:80`.
- Rota: NPM → proxy host 17 (`wampa.com.br`, `www.wampa.com.br`) → aba **Advanced** com o conteúdo de
  `wampa-location.conf`. O `location /` do site Wampa e os demais hosts não foram alterados. O upstream é resolvido na
  hora do pedido, então o NPM continua subindo mesmo com o `game2-web` parado (a rota devolve 502).

## Atualizar

No servidor: `sh /srv/game2/deploy/update-wampa.sh [commit]` (padrão `origin/main`). Ele reconstrói, espera o
healthcheck, confere o HTTP no host e pela `proxynet`, e volta ao commit anterior se falhar. Depois, valide de fora:

```
BASE=https://wampa.com.br/game2/ node tests/playtest-full.mjs
```

(`HOST_MAP="wampa.com.br <IPv4 da Cloudflare>"` força IPv4 em redes com IPv6 instável.)

## Desfazer

- Rota: restaurar o `17.conf` e esvaziar o *Advanced* do host 17. As cópias de antes ficam em
  `/root/backups/npm-game2-<data>/` na VPS (`17.conf` e `database.sqlite`); depois, `docker exec NProxyM nginx -t` e
  `nginx -s reload`.
- Container: `docker compose -p game2 -f compose.yaml -f deploy/compose.wampa.yaml down` em `/srv/game2`.

## Testes

- `node tests/demo-smoke.mjs` — lógica (sem navegador).
- `node tests/browser-smoke.mjs` — Chromium real com servidor local (também no CI).
- `tests/playtest-full.mjs` — partida completa contra uma URL: assets SVG, áudio (AudioContext), diálogos com retrato,
  cofre, armário e previsão do sinal, mesa de evidências, salvar e recarregar, duas rotas de decisão com destinos
  diferentes, os quatro quadros do desfecho e o layout móvel.
