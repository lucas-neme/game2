# Frequência Zero — V6: personagens e mortalidade

Status (27/11/2026): **INTEGRADO**. Folhas importadas (`assets/review/chatgpt-import/fz-personagens-v6-morte-review/`),
frames individuais em `assets/source/v6/<personagem>/<animação>/<direção>/NN.png`, atlas em
`assets/production/characters/v6/`, manifesto `assets/manifests/v6.json`, pipeline `tools/asset-pipeline/v6_build.py`.
Mortalidade no motor (bloco `/*MORTALITY*/` do `index.html`); homologação em `tests/mortality-chromium.mjs`.

Decisões e limites:
- Laterais guardadas olhando à direita (o motor espelha). Escala de cada sequência normalizada pela altura em pé do
  idle sul; as folhas de morte vêm ~2,3× maiores e são normalizadas pela 1ª pose.
- Sentar: o banco/cadeira desenhado nas folhas não se separa automaticamente com qualidade (mesma paleta das roupas e
  redesenhado a cada quadro); as poses sentadas mantêm o próprio assento e o banco do mapa é ocultado enquanto ocupado.
  Retirada limpa exige quadros sentados sem móvel (pedido de arte) ou máscaras manuais.
- Raul, Helena e Celina têm identidade redesenhada no V6 (consistente entre ações e morte); adotada por ordem do titular.
- Bento não tem animação de trabalho no V6 (usa idle). Moradores secundários continuam sem folhas de morte próprias.
- Mortes de moradores só por regra narrativa (`mortKill(id, causa)`); nenhum evento atual do capítulo I mata morador.

Texto original (26/11) abaixo, mantido como especificação.

## Identidade artística
Meio-termo entre a anatomia do protagonista antigo e a expressividade V5. Preservar identidade, roupas, proporções, paleta e orientação. Idle deve ser um ciclo sutil de respiração/piscar do mesmo modelo, sem trocar rosto. Caminhada em quatro direções. Interações, sentar e levantar com mobiliário separado. Corrigir resíduos e opacidade, especialmente Helena; verificar continuidade do Raul.

## Inventário V6
characters/{hero,lia,raul,nora,helena,bento,celina}/{actions,death}.png; creatures/actions.png; references/investigator.png; manifest.json. Cada folha death contém 24 poses candidatas (4 linhas por 6 colunas), com orientação a verificar individualmente. Fundos compostos exigem segmentação, revisão visual, ancoragem e atlas. Não preencher lacunas com frames repetidos.

## Mortalidade
Todos os personagens humanos, incluindo moradores secundários e protagonista, podem morrer quando as regras narrativas e de combate permitirem. Estados ALIVE, DOWNED, DYING, DEAD. Distinguir derrota recuperável de morte permanente. DYING executa sequência direcional uma única vez; DEAD mantém último quadro. Interromper deslocamento, diálogo, ações, ocupação de assentos e agenda; remover da navegação e encontros futuros. Registrar local, horário, causa narrativa e consequências em save versionado. Não ressuscitar por recarregar, avançar horário ou mudar região. Morte do protagonista encerra a partida com opções de recuperar save anterior ou novo jogo. Não matar moradores arbitrariamente para preencher conteúdo. Missões devem ter rotas alternativas por documentos, testemunhas ou resultados explicitamente encerrados. Não bloquear campanha silenciosamente. Atualizar reações sociais e diário sem vazar informações desconhecidas.

## Gate
Verificar todos os frames contra fundos verdes/claros/escuros; preservar pixels internos e retirar mobiliário incorporado. Validar direção, escala e transparência em Chromium real. Testar morte durante caminhada, diálogo, assento, transição de região, salvar/recarregar, consequência narrativa e morte do protagonista. Não declarar integração antes dos PNGs presentes, renderizados e homologados. Moradores secundários ainda precisam de folhas de morte próprias.
