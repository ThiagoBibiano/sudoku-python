# Algoritmos de Resolução (visão técnica)

Este documento resume o funcionamento dos solvers disponíveis na aplicação, com foco em backtracking e nas heurísticas MRV/LCV que reduzem o espaço de busca.

## Backtracking (força bruta com retrocesso)
- **Ideia:** Explora o tabuleiro como um labirinto. Preenche uma célula vazia, segue adiante; se não houver saída válida, volta (backtrack) à decisão anterior e tenta outro valor.
- **Passos:** escolher célula vazia -> tentar valores 1..9 válidos -> avançar recursivamente -> se esgotar candidatos, desfaz e tenta outra ramificação.
- **Garantia:** Encontra solução se existir, mas pode ser lento sem heurísticas.

## MRV (Minimum Remaining Values) — "Falhar primeiro"
- **O que faz:** Escolhe sempre a célula vazia com **menos candidatos** válidos.
- **Motivação:** Enfrentar cedo os gargalos; se uma célula só aceita um dígito, preencha-a já.
- **Efeito:** Reduz a árvore de busca porque elimina cedo ramificações inviáveis.

## LCV (Least Constraining Value) — "Deixar portas abertas"
- **O que faz:** Dado um conjunto de candidatos para uma célula, testa primeiro o valor que **menos restringe** os vizinhos (linha, coluna, box).
- **Motivação:** Evitar que uma escolha elimine opções de muitas outras células, aumentando a chance de avançar sem backtrack.
- **Efeito:** Ordena candidatos por impacto; valores que incomodam menos são testados antes.
