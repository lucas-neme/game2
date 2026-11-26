# Fontes artísticas finais de Frequência Zero

Originais dos pacotes que o jogo usa **hoje**, sem alteração, para que o pipeline (`tools/asset-pipeline`) rode só a
partir do repositório. Tudo em `assets/production` é derivado destas pastas (mesmos bytes ao reconstruir).
Não entram na imagem publicada (`.dockerignore`). Pacotes antigos ou rejeitados não estão aqui.

| Pasta | Pacote de origem | Usado para | Script |
|---|---|---|---|
| `canon/` | frequencia-zero-canon.zip (referência canônica: `canon/referencia-canonica.png`) | construções, árvores, móveis, placas, terreno, retratos, ícones, logo, interior do escritório, criaturas do cenário | `canon_build.py` |
| `protagonista-walk-v2/` | frequencia-zero-protagonista-walk-v2.zip | protagonista: 4 vistas × 8 quadros (64×96, pivô 32,90) e pose sentada derivada | `canon_build.py` |
| `v4/` | fz-monstros-itens-enigmas-v4-completo.zip | 47 itens do inventário, animações do Eco Humanoide e da Anomalia Esférica, 10 painéis de enigmas | `v4_build.py` |
| `v5-npcs/<npc>/` | fz-harmonizado-v5-completo.zip (só `source.png` + `manifest.json` de cada NPC) | Lia, Raul, Nora, Helena, Bento, Celina | `v5_build.py` (classificação em `v5_map.py`) |

SHA-256 dos zips de origem:

| Zip | sha256 |
|---|---|
| `frequencia-zero-canon.zip` | `91c551d6c3f77586…` |
| `frequencia-zero-protagonista-walk-v2.zip` | `f452db0d641bc8ba…` |
| `fz-monstros-itens-enigmas-v4-completo.zip` | `a4beb4781ca39f10…` |
| `fz-harmonizado-v5-completo.zip` | `2a711cb948fff9e4…` |

Reconstruir: `python tools/asset-pipeline/canon_build.py && python tools/asset-pipeline/v4_build.py && python tools/asset-pipeline/v5_build.py`
(Python 3.12, Pillow, NumPy). Especificação de escala: `docs/SCALE.md`; estados de revisão por asset nos manifestos
`assets/manifests/{production,v4,v5}.json`.
