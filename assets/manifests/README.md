# Catálogo de assets de Frequência Zero

O GitHub é a fonte central de todos os assets. Nenhuma IA precisa dos ZIPs originais.

| Arquivo | O que contém |
|---|---|
| `asset-registry.json` / `.csv` | Um registro por arquivo gráfico em `assets/` (id, caminho, URLs, categoria, personagem, animação, direção, frame, dimensões, âncora, escala, SHA-256, origem, versão, estado, uso no jogo). |
| `animation-index.json` | Animações disponíveis e faltantes por personagem (também em `docs/ANIMATION_REGISTRY.md`). |
| `audit-report.json` | Integridade: corrompidos, vazios, sem alfa, duplicatas, referências quebradas, lacunas de frames. |
| `../review/chatgpt-import/import-manifest.json` | Um registro por membro de cada ZIP gerado pelo ChatGPT: pacote, caminho interno, SHA-256 e `stored_at` (a única cópia no repo daqueles bytes). |
| `production.json`, `v4.json`, `v5.json` | Contratos de produção: âncoras, escala, animações e linhas de cada atlas em uso. |

Estados: `PRODUCTION`/`APPROVED` vão para o jogo; `SOURCE` é original canônico; `REVIEW` é candidato importado
(fora da imagem de deploy, ver `.dockerignore`); `REJECTED` tem defeito conhecido (`production.json` → `rejected_packs`).

Promover um asset: tratar a partir de `SOURCE`/`REVIEW` com `tools/asset-pipeline`, gravar em `assets/production/...`,
declarar no manifesto de produção, homologar em Chromium real e rodar `python tools/assets/asset_tools.py registry` e `audit`.

Importar pacotes novos: `python tools/import-chat-assets.py <pasta-dos-zips> --commit --push`. Bytes idênticos não são
gravados duas vezes, e nada já existente é movido.
