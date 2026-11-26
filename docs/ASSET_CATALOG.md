# Catálogo de assets — Frequência Zero

- `assets/manifests/asset-registry.json`: um registro por arquivo gráfico, com id, nome, categoria, caminho, URLs
  (GitHub/raw), personagem, animação, direção, frame (os frames V5 são rotulados pelo `v5.json`), dimensões, âncora,
  escala, colisor, SHA-256, cópias idênticas, origem (pacote ZIP), licença, versão, estado, atlas, manifestos que o
  declaram e uso atual no jogo (`in_game`, `runtime_reference`).
- `assets/manifests/asset-registry.csv`: colunas principais para consulta rápida.
- `assets/manifests/animation-index.json` e `docs/ANIMATION_REGISTRY.md`: animações disponíveis (arquivos individuais e
  as declaradas nos atlas, marcadas `(atlas)`) e faltantes por personagem.
- `assets/manifests/audit-report.json`: integridade.
- `assets/review/chatgpt-import/import-manifest.json`: proveniência de cada membro de cada ZIP.

Regenerar: `python tools/assets/asset_tools.py registry && python tools/assets/asset_tools.py audit`.

## Pendente de arquivo do titular

`fz-personagens-v6-morte-review.zip` (folhas V6 de ações e as 168 poses de morte dos sete personagens principais) **não
existe** em `D:\FrequencyAssets\assets-import` nem em nenhum outro lugar do PC (busca em 26/11/2026). Sem ele, as
animações de morte e as folhas V6 não podem ser importadas; `docs/CHARACTER_V6_MORTALITY.md` continua como especificação.
