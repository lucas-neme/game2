# Escala universal — Frequência Zero

Configuração única: bloco `/*SCALE:BEGIN*/` em `index.html` (`SCALE`). Calibração: `?debug=scale` (fila de comparação
com medidas; desligada em produção). `?scale=<fator>` só para comparações.

## Unidade
- Mundo: 1 célula = 3 m = losango 128×64 px; 1 m ≈ 21,3 px na vertical.
- **Unidade humana = altura do protagonista em pé na tela.** Fonte: walk-v2 (64×96, figura de 84 px, pivô 32,90).
- Fator escolhido por comparação com a mesma câmera (1,0 / 1,25 / 1,35 / 1,40 / 1,50 em
  `browser-evidence/scale/cmp-*.png`): **1,40** → protagonista desenhado a 0,70 da arte = **58,8 px**. Assento do banco
  na altura do joelho, porta da clínica acima da cabeça; 1,50 começa a competir com a porta.
- A escala física é separada da resolução do PNG: cada personagem usa a altura **visível** (sem margem transparente).

## Humanos (relativo ao protagonista)
| Personagem | Altura | Nota |
|---|---|---|
| Protagonista | 100% | autoridade artística |
| Raul | 104% | robusto |
| Lia | 97% | |
| Helena | 96% | |
| Nora, Celina | 95% | |
| Bento | 94% | idoso, levemente curvado |
| Criança (Tico) | 62% do adulto | |
Faixas: adulto 90–110 %, idoso 85–100 %, adolescente 75–95 %, criança 50–75 %. Sequências desenhadas em outra escala
na folha recebem fator uniforme por sequência (`k` no manifesto v5), nunca esticamento.

## Criaturas (`SCALE.creature`)
cão 40 %, inseto 25 %, rastejante 40 %, corvo 30 %, larva 25 %, drone 55 %, eco 105 %, humanoide 100 %, humanoide grande
130 %, mutante 160 %, guardião 190 %, colosso 320 %. Quadrúpedes: altura menor, comprimento e colisor maiores.
Voadoras: altitude de desenho separada da posição física (pendente de implementação com arte V5).

## Mobiliário (`SCALE.furniture`, `SCALE.props`)
assento de banco 28 %, encosto 52 %, cadeira 28 %, mesa 45 %, balcão 58 %, porta 122 %, cama 120 %.
Ajustes de desenho: banco 0,9, lixeira 0,82, hidrante 0,85, barril/caixas 0,9 (colisores inalterados).

## Colisores e âncoras
Pés: círculo 0,22 célula (protagonista e NPCs; não cresce com a altura do sprite). Construções: área no chão. Assento:
âncora no centro do banco, elevação = 22 % da altura do sprite × escala do banco; camada dianteira redesenhada sobre
quem está sentado.

## Rejeitados / pendentes
- Moradores ambiente antigos (cabeçudos): fora da produção (`?legacy=1` para revisar).
- Monstros grandes: a arte V4 de 70 px ampliada 3,2× vira blocos (proibido); colosso e guardião precisam de arte na
  própria escala. Modelos avulsos V4 com resíduo de rótulo seguem em REVIEW.
- V5 monstros (19 conjuntos): não integrados nesta entrega.
