# Direção de arte — Frequência Zero

Fontes detalhadas: `docs/SCALE.md` (escala universal 1,40), `docs/MOTION.md` (movimento), `docs/CHARACTER_V6_MORTALITY.md`
(V6 e mortalidade), `assets/manifests/production.json` (autoridade: `referencia-canonica.png` do canon).

- Pixel art isométrica, Vale do Cedro em 1998. Cidade acolhedora; regiões afastadas sombrias.
- Personagens: meio-termo entre a anatomia do protagonista original e a expressividade dos NPCs V5. Anatomia estilizada
  e proporcional, contorno escuro contínuo, transparência binária limpa (sem halo, sem resíduo de fundo, sem buraco
  interno), mesma identidade em todos os frames (idle = respiração/piscar do mesmo modelo).
- Escala: célula 128×64, 1 m ≈ 21,3 px; personagem de referência 32×48 no canon; NPCs V5 normalizados à altura do
  protagonista (`v5.json` → `relative_height`). Mobiliário e construções na mesma escala; monstros pela própria anatomia.
- Mobiliário nunca embutido no sprite (sentar usa o assento do jogo).
- A arte é exclusiva deste jogo e não se mistura com Ashen Kingdoms (`lucas-neme/ashes-idle`).
