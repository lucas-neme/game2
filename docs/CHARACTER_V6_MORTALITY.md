# Frequência Zero — V6: personagens e mortalidade

Status: REVIEW. Os PNGs V6 foram gerados e reunidos no pacote fz-personagens-v6-morte-review.zip, mas ainda não foram transferidos ao GitHub. Não ativar referências inexistentes nem substituir atlas de produção por folhas compostas.

## Identidade artística
Meio-termo entre a anatomia do protagonista antigo e a expressividade V5. Preservar identidade, roupas, proporções, paleta e orientação. Idle deve ser um ciclo sutil de respiração/piscar do mesmo modelo, sem trocar rosto. Caminhada em quatro direções. Interações, sentar e levantar com mobiliário separado. Corrigir resíduos e opacidade, especialmente Helena; verificar continuidade do Raul.

## Inventário V6
characters/{hero,lia,raul,nora,helena,bento,celina}/{actions,death}.png; creatures/actions.png; references/investigator.png; manifest.json. Cada folha death contém 24 poses candidatas (4 linhas por 6 colunas), com orientação a verificar individualmente. Fundos compostos exigem segmentação, revisão visual, ancoragem e atlas. Não preencher lacunas com frames repetidos.

## Mortalidade
Todos os personagens humanos, incluindo moradores secundários e protagonista, podem morrer quando as regras narrativas e de combate permitirem. Estados ALIVE, DOWNED, DYING, DEAD. Distinguir derrota recuperável de morte permanente. DYING executa sequência direcional uma única vez; DEAD mantém último quadro. Interromper deslocamento, diálogo, ações, ocupação de assentos e agenda; remover da navegação e encontros futuros. Registrar local, horário, causa narrativa e consequências em save versionado. Não ressuscitar por recarregar, avançar horário ou mudar região. Morte do protagonista encerra a partida com opções de recuperar save anterior ou novo jogo. Não matar moradores arbitrariamente para preencher conteúdo. Missões devem ter rotas alternativas por documentos, testemunhas ou resultados explicitamente encerrados. Não bloquear campanha silenciosamente. Atualizar reações sociais e diário sem vazar informações desconhecidas.

## Gate
Verificar todos os frames contra fundos verdes/claros/escuros; preservar pixels internos e retirar mobiliário incorporado. Validar direção, escala e transparência em Chromium real. Testar morte durante caminhada, diálogo, assento, transição de região, salvar/recarregar, consequência narrativa e morte do protagonista. Não declarar integração antes dos PNGs presentes, renderizados e homologados. Moradores secundários ainda precisam de folhas de morte próprias.
