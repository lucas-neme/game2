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

## Situação (27/11/2026)

- V6 dos 7 personagens integrado (`docs/CHARACTER_V6_MORTALITY.md`), 660 quadros individuais em `assets/source/v6/`.
- Criaturas V5 harmonizadas: 10 espécies em `assets/source/v5-creatures/` e no atlas `assets/production/creatures/v5/`
  (`assets/manifests/v5-creatures.json`). Pendentes: `mutante_floresta` (sequências sem separação nítida) e as 7 folhas
  opacas com grade (anomalia_temporal, cepa_esporal, colosso_ressonancia, entidade_luz, enxame, espectro_infantil,
  guardiao_bunker, mutacao_aquatica) — precisam de recorte manual do fundo.
- Criaturas da folha V6 (`creatures/actions.png`) e cenários V3 (cidade expandida, interiores em corte, natureza/bunker,
  objetos) seguem em REVIEW: ainda não há regiões do mapa para eles.
