# Referências bibliográficas

Referências utilizadas no trabalho, em formato ABNT, agrupadas por função. Os
grupos servem para escolher o que citar em cada slide de fundamentação; para um
slide único de bibliografia, use a lista consolidada ao final.

> **Verificar antes da entrega final.** Quatro referências têm metadados
> incompletos — estão marcadas com ⚠ e listadas na última seção.

---

## 1. Fundamentação teórica — o diálogo de surdos

Base conceitual do experimento: as três patologias que a simulação precisa
provocar de forma controlada para depois testar se a dimensão D5 as mitiga.

ANGENOT, M. **Divergent reasonings and dialogues of the deaf**: why do we often
find others "irrational"? Keynote lecture. University of Alberta, 2006.

ANGENOT, M. **Dialogues de sourds**: traité de rhétorique antilogique. Paris:
Mille et une nuits, 2008.

ANGENOT, M. **El discurso social**: los límites históricos de lo pensable y lo
decible. Buenos Aires: Siglo XXI Editores, 2010.

**Mapeamento para as três categorias analíticas:**

| Categoria | Referência |
|---|---|
| Incomensurabilidade discursiva | Angenot (2010) |
| Retórica da incompreensão | Angenot (2008) |
| Ilusão da racionalidade | Angenot (2008) |

---

## 2. Trabalho anterior — origem do modelo D5

MOURA, G. P. C.; BRANDI, C. **From hostility to deliberation**: a
sociotechnical model for mitigating unproductive debates in AI-mediated social
media. In: International Conference on Computer-Human Interaction Research and
Applications (CHIRA), 2026. ⚠

---

## 3. Classificação política esquerda/direita

Fundamentam a regra de seleção das personas. Cada obra sustenta um componente
distinto da regra — o que torna a classificação auditável em vez de arbitrária.

BOBBIO, N. **Destra e sinistra**: ragioni e significati di una distinzione
politica. Roma: Donzelli, 1994. [Ed. brasileira: **Direita e esquerda**: razões
e significados de uma distinção política. São Paulo: Editora UNESP, 1995. Ed.
inglesa: **Left and right**: the significance of a political distinction.
Cambridge: Polity Press, 1996.]

FELDMAN, S.; JOHNSTON, C. D. Understanding the determinants of political
ideology: implications of structural complexity. **Political Psychology**,
v. 35, n. 3, p. 337–358, 2014. DOI: 10.1111/pops.12055.

JOST, J. T.; GLASER, J.; KRUGLANSKI, A. W.; SULLOWAY, F. J. Political
conservatism as motivated social cognition. **Psychological Bulletin**, v. 129,
n. 3, p. 339–375, 2003. DOI: 10.1037/0033-2909.129.3.339.

PIURKO, Y.; SCHWARTZ, S. H.; DAVIDOV, E. Basic personal values and the meaning
of left-right political orientations in 20 countries. **Political Psychology**,
v. 32, n. 4, p. 537–561, 2011. DOI: 10.1111/j.1467-9221.2011.00828.x.

**O que cada uma fundamenta:**

| Obra | Papel na regra |
|---|---|
| Bobbio (1994) | Critério definidor: atitude frente à igualdade. Sustenta a **âncora** e os **indicadores nucleares** |
| Jost et al. (2003) | Núcleo do conservadorismo: resistência à mudança + justificação da desigualdade. Sustenta os **indicadores periféricos** do eixo social |
| Piurko et al. (2011) | Universalismo/benevolência → esquerda; conformidade/tradição → direita. Sustenta o mapeamento de `values_priority` |
| Feldman & Johnston (2014) | Duas dimensões (econômica e social) são o mínimo necessário. Justifica **separar os eixos** em vez de somar tudo numa escala |

---

## 4. Dataset de personas

LI, X. et al. **MatrAIx Persona 1M**: a million structured synthetic personas.
arXiv:2608.04205, 2026. ⚠

Grounding do dataset em surveys reais: World Values Survey, General Social
Survey (GSS), Latinobarómetro e Pew Research Center.

---

## 5. Intervenções em discurso online mediadas por IA

Trabalho relacionado: intervenções que atuam **antes da postagem**, que é o
ponto em que a dimensão D5 opera.

ARGYLE, L. P.; BAIL, C. A.; BUSBY, E. C.; GUBLER, J. R.; HOWE, T.; RYTTING, C.;
SORENSEN, T.; WINGATE, D. Leveraging AI for democratic discourse: chat
interventions can improve online political conversations at scale.
**Proceedings of the National Academy of Sciences (PNAS)**, v. 120, n. 41,
e2311627120, 2023. DOI: 10.1073/pnas.2311627120.

KATSAROS, M.; YANG, K.; FRATAMICO, L. Reconsidering tweets: intervening during
tweet creation decreases offensive content. In: **Proceedings of the
International AAAI Conference on Web and Social Media (ICWSM)**, v. 16, 2022.
arXiv:2112.00773. ⚠

TESSLER, M. H.; BAKKER, M. A. et al. AI can help humans find common ground in
democratic deliberation. **Science**, v. 386, 2024. ⚠

---

## 6. Simulação de dinâmicas de opinião com agentes LLM

CHUANG, Y.-S. et al. Simulating opinion dynamics with networks of LLM-based
agents. arXiv:2311.09618, 2023. ⚠

---

## 7. Modelos utilizados no experimento

Não são referências bibliográficas, mas devem constar no slide de método para
que o experimento seja reprodutível.

| Papel | Modelo | Provedor |
|---|---|---|
| Debatedor (A) | `llama3.1:8b-instruct-q4_K_M` | Ollama, local |
| Moderador D5 (B) | `qwen2.5:7b-instruct-q4_K_M` | Ollama, local |
| Juiz (C) | `gemma2:9b-instruct-q4_K_M` | Ollama, local |

Todos em quantização Q4_K_M, executados localmente em MacBook Air M2 (24 GB).
A escolha por modelos locais está documentada em `local_models_decision.md`: os
modelos gratuitos via API introduziam **viés de disponibilidade** — a condição
de tratamento, que usa um modelo a mais, falhava sistematicamente enquanto o
controle passava.

---

## Lista consolidada (slide único de bibliografia)

Ordem alfabética por sobrenome do primeiro autor.

1. ANGENOT, M. **Divergent reasonings and dialogues of the deaf**: why do we
   often find others "irrational"? Keynote lecture. University of Alberta, 2006.
2. ANGENOT, M. **Dialogues de sourds**: traité de rhétorique antilogique.
   Paris: Mille et une nuits, 2008.
3. ANGENOT, M. **El discurso social**: los límites históricos de lo pensable y
   lo decible. Buenos Aires: Siglo XXI Editores, 2010.
4. ARGYLE, L. P. et al. Leveraging AI for democratic discourse: chat
   interventions can improve online political conversations at scale. **PNAS**,
   v. 120, n. 41, e2311627120, 2023.
5. BOBBIO, N. **Direita e esquerda**: razões e significados de uma distinção
   política. São Paulo: Editora UNESP, 1995 [1994].
6. CHUANG, Y.-S. et al. Simulating opinion dynamics with networks of LLM-based
   agents. arXiv:2311.09618, 2023.
7. FELDMAN, S.; JOHNSTON, C. D. Understanding the determinants of political
   ideology: implications of structural complexity. **Political Psychology**,
   v. 35, n. 3, p. 337–358, 2014.
8. JOST, J. T. et al. Political conservatism as motivated social cognition.
   **Psychological Bulletin**, v. 129, n. 3, p. 339–375, 2003.
9. KATSAROS, M.; YANG, K.; FRATAMICO, L. Reconsidering tweets: intervening
   during tweet creation decreases offensive content. In: **ICWSM**, v. 16, 2022.
10. LI, X. et al. **MatrAIx Persona 1M**: a million structured synthetic
    personas. arXiv:2608.04205, 2026.
11. MOURA, G. P. C.; BRANDI, C. **From hostility to deliberation**: a
    sociotechnical model for mitigating unproductive debates in AI-mediated
    social media. In: **CHIRA**, 2026.
12. PIURKO, Y.; SCHWARTZ, S. H.; DAVIDOV, E. Basic personal values and the
    meaning of left-right political orientations in 20 countries. **Political
    Psychology**, v. 32, n. 4, p. 537–561, 2011.
13. TESSLER, M. H.; BAKKER, M. A. et al. AI can help humans find common ground
    in democratic deliberation. **Science**, v. 386, 2024.

---

## ⚠ Metadados a completar antes da entrega final

| Referência | O que falta |
|---|---|
| Moura & Brandi (2026) | Páginas, editora dos proceedings, DOI, cidade do evento |
| Li et al. (2026) — MatrAIx | Lista completa de autores; título exato do preprint |
| Katsaros et al. (2022) | Páginas nos proceedings |
| Tessler et al. (2024) | Lista completa de autores, número da edição, DOI |
| Chuang et al. (2023) | Lista completa de autores; venue de publicação, se houver |

Para a apresentação de resultados preliminares essas lacunas são aceitáveis —
os slides citam autor e ano. Para a submissão, completar todas.
