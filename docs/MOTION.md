# Motor de movimentação e colisão

Código: bloco `/*MOTION:BEGIN*/ … /*MOTION:END*/` em `index.html`. As formas de colisão saem do pipeline
(`tools/asset-pipeline/canon_build.py` → `ART.colliders` e `assets/manifests/production.json` → `collision`).

## Coordenadas
- **Mundo físico:** unidades de célula (1 célula = 3 m), plano dos pés. O corpo do protagonista é `s.px, s.py` (float).
- **Lógica:** `s.x, s.y` continuam inteiros (eventos, rotinas, prazos, saves) e são a célula arredondada do corpo.
- **Render:** `iso(x,y) = [ox+(x−y)·64, oy+(x+y)·32]`; câmera em `cam` (x, y, zoom); interface em pixels de tela.
  `screenToWorld()` e `worldToScreen2()` convertem; `screenToWorldDir()` faz a direção pressionada na tela virar a
  mesma direção visual no mundo isométrico.

## Controle
- WASD/setas (8 direções), analógico (gamepad, joystick de toque no mapa), d-pad móvel segurando.
- Velocidades: andar 2,4 · correr 4,3 (Shift / botão B) · furtivo 1,15 células/s (Ctrl segurado ou C alterna).
- Aceleração/desaceleração exponenciais (16 e 24/s), delta time limitado a 50 ms, laço em `requestAnimationFrame`.
- Diagonal normalizada; a animação avança pela distância percorrida (sem pé deslizando); bloqueado = parado.

## Colisão
- Estáticos num hash espacial de 1 célula: construções = área no chão (caixa por célula do footprint 2×2),
  árvores/rochas = tronco (círculo 0,20/0,27), móveis e postes = base (círculos 0,08–0,36), lago = caixa d'água.
  Telhados e copas não colidem.
- Corpos: protagonista e moradores = círculos de 0,22 nos pés.
- Movimento em sub-passos de 0,07 célula (sem tunneling) + empurrão pela normal de contato (desliza nas paredes).
- Interação só com linha livre até o alvo (`losBlocked`), sem atravessar paredes.

## Moradores
Plano global por BFS na grade (custo uniforme = A*), caminho suavizado por linha de visão, execução contínua com
steering, separação entre corpos, espera quando o protagonista bloqueia, replanejamento após 2,5 s preso.
Teleporte só fora do campo de visão (mantido do motor anterior).

## Tempo
8 minutos por célula efetivamente percorrida (`s.distAcc`), igual ao custo antigo por passo; segurar a tecla não
dispara repetições. Saves antigos (sem `px/py`) carregam no centro da célula.

## Interiores
Estação e escritório: faixa caminhável na frente dos móveis, colisões retangulares por móvel, pontos de investigação
por proximidade (E) com destaque; os botões continuam clicáveis.

## Depuração e testes
- `?debug=hitbox` ou F3: desenha colisores estáticos, corpos e rotas dos moradores.
- `tests/motion-chromium.mjs`: 16 verificações em Chromium real (contínuo, 8 direções, corrida/furtivo, parede +
  deslizamento + contorno, árvore, banco, tunneling, morador, morador × morador, tempo × distância, linha de visão,
  interior, câmera, migração de save, desempenho, d-pad móvel).
- `tests/motion-videos.mjs`: 8 vídeos dos cenários.

## Limitações conhecidas (arte)
Os sprites têm 4 direções diagonais (frente/costas espelhadas); o movimento em 8 direções usa a diagonal mais
próxima. Faltam quadros próprios para direções cardeais (N, S, L, O) e animações desenhadas de corrida/furtivo para
cada personagem: hoje são derivadas dos recortes canônicos (cabeça/tronco fixos, membros redesenhados).
