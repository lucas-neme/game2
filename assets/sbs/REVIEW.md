# Revisão artística do kit `frequencia-zero-kit.zip` (26/11/2026)

Kit importado como **fonte catalogada**, sem alteração: 280 entradas no `manifest.json` (272 complementos procedurais +
8 construções derivadas do SBS), 11 atlas, licença `SBS-LICENSE.txt` (CC0). O próprio kit se declara "rascunho
artístico, não homologado no motor". Conferência automática: nenhum arquivo ausente, dimensões batem com o manifesto,
nenhuma duplicata byte a byte. Avaliação visual por categoria (atlas abertos lado a lado com o pacote SBS original):

| Categoria | Qtde | Decisão | Motivo |
|---|---|---|---|
| architecture | 8 | **Referência, não promovida** | Composições SBS de 1 andar. O recorte dos telhados usa passo de 144 px numa folha de 143 px (desvio acumulado) e o beiral fica 7 px acima do topo das paredes. Refeitas em `tools/asset-pipeline` com alinhamento medido e vários andares. Os nomes (casas de Helena, Bento e Celina) foram mantidos. |
| terrain | 32 | Rejeitada | Losangos chapados com ruído pontual: é exatamente o "tabuleiro". O chão de produção é renderizado como uma camada contínua. |
| vegetation | 24 | Rejeitada | Copas de círculos sem direção de luz nem contorno; 8 variações quase iguais. |
| urban | 32 | Rejeitada | Cadeiras e caixas como cubos lisos, postes = cubo num palito, latas = cilindros cinza repetidos. |
| rail | 24 | Rejeitada | 16 trilhos idênticos e postes-cubo. |
| interior | 48 | Rejeitada | Cubos com uma linha; mesmas 4 formas em 48 cópias. |
| characters | 24 | Rejeitada | Um único boneco estático em 24 cores, sem quadros de animação. |
| creatures | 8 | Rejeitada | Polígono único em 4 cores. |
| effects | 24 | Rejeitada | Anéis concêntricos genéricos. |
| icons | 40 | Rejeitada | Três desenhos (chave, papel, moeda) repetidos. |
| signs | 16 | Rejeitada | Cubo num palito, igual ao poste. |

Nada desta pasta é carregado pelo jogo. O que vai para produção sai de `tools/asset-pipeline` (pacote SBS original +
complementos redesenhados) e é listado em `assets/manifests/production.json`.
