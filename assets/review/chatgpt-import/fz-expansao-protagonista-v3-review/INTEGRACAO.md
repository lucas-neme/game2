# Integração
O diretório walk-v2 contém a caminhada anteriormente produzida: 8 frames por direção, 64×96, pivot (32,90). A folha nova contém estudos de ação, não ciclos completos.
O motor deve selecionar west/east quando o deslocamento visual for lateral, north/south quando vertical. Não mapear todas as direções para front/back com espelhamento. Verificar a projeção isométrica e o vetor de velocidade em tela.
Sentar: aproximar-se do banco, verificar assento livre, alinhar âncora ao assento, tocar transição, permanecer na pose sentada, bloquear deslocamento até levantar, liberar assento. O banco deve ter camada dianteira separada e colisor no chão. As poses novas precisam ser isoladas e reconstruídas antes de integração.
