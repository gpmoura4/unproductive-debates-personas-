# Resultados preliminares — Moderação participativa (D5)

## Corpus

- Desenho: balanceado
- Temas: Abortion, Drug Legalization
- Células (tema × par de personas): 10
- Réplicas: 10
- Debates: 20 (8 turnos cada)
- Execuções descartadas na seleção: 40

## Resultado principal

A moderação participativa reduziu a hostilidade média de **3,15** para **1,96** na escala 0–4 (Δ = **-1,19**), com efeito na mesma direção em 10 das 10 células.

## Tabelas

| Recorte | Células | Controle | Tratamento | Δ | DP(Δ) | Células com Δ<0 |
|---|---:|---:|---:|---:|---:|---:|
| Global | 10 | 3,15 | 1,96 | -1,19 | 0,24 | 10/10 |
| Abortion | 5 | 3,20 | 2,00 | -1,20 | 0,28 | 5/5 |
| Drug Legalization | 5 | 3,10 | 1,93 | -1,18 | 0,19 | 5/5 |

**Tabela 1 — Efeito principal do D5 sobre a hostilidade.** Hostilidade média por debate (escala 0–4, mediana de três execuções do juiz), agregada por célula (tema × par de personas). Δ é a diferença pareada tratamento − controle dentro de cada célula; valores negativos indicam redução de hostilidade sob moderação. DP(Δ) é o desvio-padrão populacional entre células.


| Métrica | Valor |
|---|---:|
| Turnos de tratamento | 80 |
| Mensagens avaliadas pelo moderador | 80 (100%) |
| Mensagens reformuladas | 72 (90%) |
| Reformuladas / avaliadas | 90% |
| Decisões fora do limiar | 0 (0%) |

**Tabela 2 — Acionamento da moderação participativa (D5).** Toda mensagem candidata na condição de tratamento passa pelo moderador; "reformuladas" são aquelas em que ele substituiu o texto antes da publicação. "Decisões fora do limiar" conta turnos em que a decisão de intervir discordou da própria pontuação atribuída pelo moderador (limiar: hostilidade ≥ 2), medindo sua calibragem interna.


| Métrica | Valor |
|---|---:|
| Mensagens pontuadas | 160 |
| Execuções por mensagem | 3 |
| Unanimidade entre execuções | 160 (100%) |
| Amplitude 0 entre execuções | 160 |

**Tabela 3 — Consistência intra-juiz.** Cada mensagem publicada foi pontuada três vezes de forma independente pelo mesmo modelo juiz (temperatura 0). Amplitude é a diferença entre a maior e a menor pontuação das três execuções; amplitude 0 indica acordo perfeito. A consistência inter-juiz (modelos distintos avaliando o mesmo corpus) permanece pendente.


| Tema | Par | Réplica | Controle | Tratamento | Δ |
|---|---|---:|---:|---:|---:|
| Abortion | pair-00 | 1 | 3,12 | 1,88 | -1,25 |
| Abortion | pair-01 | 1 | 3,38 | 2,50 | -0,88 |
| Abortion | pair-02 | 1 | 3,12 | 1,62 | -1,50 |
| Abortion | pair-03 | 1 | 3,12 | 2,25 | -0,88 |
| Abortion | pair-04 | 1 | 3,25 | 1,75 | -1,50 |
| Drug Legalization | pair-00 | 1 | 3,12 | 2,12 | -1,00 |
| Drug Legalization | pair-01 | 1 | 3,00 | 2,00 | -1,00 |
| Drug Legalization | pair-02 | 1 | 3,25 | 1,75 | -1,50 |
| Drug Legalization | pair-03 | 1 | 2,88 | 1,75 | -1,12 |
| Drug Legalization | pair-04 | 1 | 3,25 | 2,00 | -1,25 |

**Tabela 4 — Efeito por célula.** Hostilidade média de cada debate e diferença pareada, por tema e par de personas. Cada linha é uma réplica independente: controle e tratamento compartilham tema e par, diferindo apenas pela presença do moderador.


## Figuras

![g1_efeito_principal](figures/g1_efeito_principal.png)

**Figura 1 — Hostilidade média por condição.** Escala 0–4 (mediana de três execuções do juiz), agregada por célula. A moderação participativa reduziu a hostilidade em 1,19 ponto na média global, com efeito de magnitude semelhante nos dois temas. Barras de erro: desvio-padrão entre células.

![g2_trajetoria_turnos](figures/g2_trajetoria_turnos.png)

**Figura 2 — Trajetória da hostilidade ao longo do debate.** Média por turno em cada condição; faixa sombreada indica ±1 desvio-padrão entre células. O controle escala progressivamente, enquanto o tratamento mantém patamar mais baixo. Ressalva metodológica: a partir do turno 2 as condições deixam de compartilhar o mesmo histórico, pois os debatedores sob tratamento respondem a mensagens já reformuladas — parte da diferença é efeito direto da reescrita e parte é desescalada indireta, e o desenho não as separa.

![g3_distribuicao_notas](figures/g3_distribuicao_notas.png)

**Figura 3 — Distribuição das pontuações de hostilidade.** Contagem de mensagens publicadas por nível da escala em cada condição. Sob controle a massa concentra-se nos níveis 3 e 4; sob tratamento desloca-se para 1 e 2, indicando que a moderação não apenas reduz a média mas redistribui as mensagens ao longo da escala.

![g4_delta_por_celula](figures/g4_delta_por_celula.png)

**Figura 4 — Efeito por célula.** Diferença pareada em cada réplica, ordenada por magnitude. O efeito é negativo em 10 das 10 células, indicando que a redução de hostilidade não se concentra em poucos pares de personas mas se repete em todo o corpus.

## Ressalvas

1. **Históricos divergentes.** A partir do turno 2 as condições deixam de compartilhar o mesmo histórico: sob tratamento, os debatedores respondem a mensagens já reformuladas. Parte do efeito é a reescrita direta da mensagem, parte é desescalada indireta do interlocutor; o desenho atual não separa as duas.

2. **Preservação argumentativa é autodeclarada.** Em 72 das 72 reformulações o moderador declarou o que preservou, mas essa declaração provém da mesma chamada que produziu a reformulação. Não constitui evidência de que a posição original sobreviveu — verificação independente permanece pendente.

3. **Geração estocástica.** O campo `seed` registrado nos manifestos não é repassado ao modelo; réplicas da mesma célula são execuções independentes, não reproduções exatas.

4. **Modelos pequenos.** Debatedor, moderador e juiz são modelos de 7–9B em quantização Q4, imposição do hardware disponível.
