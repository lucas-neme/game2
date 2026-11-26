# Pipeline de assets — Frequência Zero

O GitHub (`lucas-neme/game2`, `main`) é a fonte central de toda a arte do jogo. Os ZIPs gerados pelo ChatGPT servem só de
transporte e backup (`D:\FrequencyAssets\assets-import`, fora do repo); cada membro deles existe aqui como arquivo próprio.

## Onde fica cada coisa

| Pasta | Estado | Conteúdo |
|---|---|---|
| `assets/production/` | APPROVED / PRODUCTION | Atlas carregados pelo `index.html` (personagens, V5, criaturas, ambiente, interiores, V4, UI). **Não mover**: o motor e o cache-busting do deploy dependem desses caminhos. |
| `assets/source/` | SOURCE | Originais canônicos (canon, protagonista-walk-v2, v4, v5-npcs) de onde `tools/asset-pipeline` recorta a produção. |
| `assets/review/chatgpt-import/<pacote>/` | REVIEW / REJECTED | Todos os membros dos 22 pacotes, como arquivos individuais, deduplicados por SHA-256 (`import-manifest.json` aponta cada membro para a cópia única). Fora da imagem de deploy (`.dockerignore`). |
| `assets/manifests/` | — | `production.json`, `v4.json` e `v5.json` (contratos do runtime), `asset-registry.json`/`.csv`, `animation-index.json`, `audit-report.json`, `registry-config.json`. |

Estados: SOURCE, REVIEW, APPROVED, PRODUCTION, ARCHIVED e REJECTED. O que acabou de ser importado é REVIEW.
`frequencia-zero-npcs-coletivo-review` é REJECTED (pernas destacadas; `production.json` → `rejected_packs`).

## Ferramentas

```
python tools/import-chat-assets.py D:\FrequencyAssets\assets-import --commit --push   # pacotes do ChatGPT -> review
python tools/assets/asset_tools.py registry      # registro JSON + CSV + índice de animações + docs/ANIMATION_REGISTRY.md
python tools/assets/asset_tools.py audit         # corrompidos, vazios, sem alfa, duplicatas, refs quebradas, lacunas
python tools/assets/asset_tools.py sheet out.png <frames...>   # folha de contato sobre xadrez
python tools/assets/asset_tools.py gif out.gif <frames...> --fps 8
python tools/asset-pipeline/v5_build.py          # NPCs V5: frames -> atlas + manifesto + bloco V5 do index.html
```

`v5_build.py` reescreve o bloco `/*V5:BEGIN*/` do `index.html`. O bloco atual tem ajustes manuais (idle de 1 frame,
`faceByAnim`); depois de rodar, mescle só tamanhos, âncoras e escalas, como no commit 1265683.

## Novo personagem ou animação

1. Colocar o ZIP em `D:\FrequencyAssets\assets-import` e rodar o importador (`--commit --push`).
2. Revisar os frames em `assets/review/...` (`sheet`/`gif`) sobre fundo verde, claro e escuro.
3. Recortar e montar o atlas com `tools/asset-pipeline`, gravar em `assets/production/...` e declarar no manifesto.
4. `registry` + `audit` (0 refs quebradas), `node tests/demo-smoke.mjs`, `tests/browser-smoke.mjs`,
   `tests/v5-chromium.mjs` e `tests/playtest-full.mjs` (Chromium real). O Wampa Auto Deploy publica o push que muda o
   artefato e passa no CI.
