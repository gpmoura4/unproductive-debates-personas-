# Regras de categorização de personas em polo Esquerda / polo Direita

**Contexto:** seleção de personas do dataset MatrAIx Persona 1M (amostra decodificada na Fase 2) para o experimento de simulação de debate improdutivo com moderador D5 (Moura e Brandi, 2026).

**Objetivo:** definir uma regra objetiva, reprodutível e teoricamente fundamentada que classifique um registro como pertencente ao **polo Esquerda** ou ao **polo Direita**, usando exclusivamente os campos e valores já decodificados, e que rejeite perfis internamente contraditórios.

**Escopo deliberado:** apenas a dicotomia ampla clássica esquerda × direita. Subtipos (liberal, libertário, social-democrata, nacional-conservador etc.) estão fora do escopo.

---

## 1. Fundamentação teórica

### 1.1 Obras selecionadas (três principais)

| # | Obra | Contribuição para a regra |
|---|---|---|
| **[B]** | BOBBIO, Norberto. *Destra e sinistra: ragioni e significati di una distinzione politica*. Roma: Donzelli, 1994. Ed. inglesa: *Left and Right: The Significance of a Political Distinction*. Cambridge: Polity, 1996 (trad. Allan Cameron). Ed. brasileira: *Direita e esquerda: razões e significados de uma distinção política*. São Paulo: Editora UNESP, 1995. | Critério definidor único e clássico: a **atitude frente à igualdade**. Esquerda = concepção horizontal/igualitária da sociedade, vê a desigualdade como socialmente produzida e removível; Direita = concepção vertical/hierárquica, vê a desigualdade como natural ou inevitável. O "centro" é tratado como *terzo incluso* (meio incluído), não como polo. Fundamenta a **âncora** (`political_lean`) e os **indicadores nucleares** do eixo econômico. |
| **[J]** | JOST, J. T.; GLASER, J.; KRUGLANSKI, A. W.; SULLOWAY, F. J. Political conservatism as motivated social cognition. *Psychological Bulletin*, v. 129, n. 3, p. 339–375, 2003. DOI: 10.1037/0033-2909.129.3.339 | Meta-análise (88 amostras, 12 países, 22.818 casos). Define o núcleo do conservadorismo (direita) como **resistência à mudança** + **justificação da desigualdade**, e adota explicitamente o critério de Bobbio (via Giddens, 1998) para a atitude frente à igualdade. Fundamenta os **indicadores periféricos do eixo social** (imigração, armas, pena capital) como expressões de gestão de ameaça/ordem, e a religiosidade como correlato periférico. |
| **[P]** | PIURKO, Y.; SCHWARTZ, S. H.; DAVIDOV, E. Basic personal values and the meaning of left-right political orientations in 20 countries. *Political Psychology*, v. 32, n. 4, p. 537–561, 2011. DOI: 10.1111/j.1467-9221.2011.00828.x | Com 20 amostras nacionais do European Social Survey e a teoria de valores de Schwartz, mostra que **universalismo e benevolência** predizem orientação de esquerda e **conformidade e tradição** predizem orientação de direita (em países liberais e tradicionais). Usa o **autoposicionamento esquerda-direita** como variável dependente. Fundamenta o mapeamento do campo `values_priority` e o uso do autoposicionamento como âncora. |

### 1.2 Obra de apoio (justificativa da estrutura em dois eixos)

- **[F]** FELDMAN, S.; JOHNSTON, C. D. Understanding the determinants of political ideology: implications of structural complexity. *Political Psychology*, v. 35, n. 3, p. 337–358, 2014. DOI: 10.1111/pops.12055 — demonstra que duas dimensões, **econômica** e **social**, são o mínimo necessário para explicar preferências de política doméstica. Justifica separar os indicadores do dataset em um eixo econômico (nuclear) e um eixo social (periférico), em vez de somar tudo em uma única escala.

### 1.3 Síntese operacional

Combinando [B], [J] e [P], o polo **Direita** é caracterizado por: (i) aceitação/justificação da hierarquia e da desigualdade, expressa economicamente em favorecer o mercado e rejeitar regulação e organização coletiva do trabalho [B][J]; (ii) resistência à mudança e prioridade a ordem e segurança, expressa socialmente em ceticismo à imigração, apoio a armas e a punição severa [J]; (iii) valores de tradição, conformidade e segurança [P]. O polo **Esquerda** é o inverso: prioridade à igualdade, expressa em ceticismo ao mercado e apoio a regulação e sindicatos [B][J]; abertura à mudança e a grupos externos [J]; valores de universalismo e benevolência (comunidade) [P].

---

## 2. Mapeamento dos campos do dataset

Escala das atitudes no dataset: `Opposed` < `Skeptical` < `Neutral` < `Positive` < `Enthusiast`.

### 2.1 Âncora (obrigatória)

| Campo | Polo Esquerda | Polo Direita | Excluído dos polos | Base |
|---|---|---|---|---|
| `political_lean` | `Left`, `Center-left` | `Right`, `Center-right` | `Center`, `Apolitical`, nulo | [B] (centro como meio incluído), [P] (autoposicionamento como medida padrão) |

### 2.2 Indicadores nucleares — eixo econômico (igualdade × hierarquia)

| Campo | Sinal Esquerda (−1) | Sinal Direita (+1) | Neutro (0) | Base |
|---|---|---|---|---|
| `att_free_markets` | `Skeptical`, `Opposed` | `Positive`, `Enthusiast` | `Neutral`, nulo | [B][J][F] |
| `att_government_regulation` | `Positive`, `Enthusiast` | `Skeptical`, `Opposed` | `Neutral`, nulo | [B][J][F] |
| `att_labor_unions` | `Positive`, `Enthusiast` | `Skeptical`, `Opposed` | `Neutral`, nulo | [B][F] |

### 2.3 Indicadores periféricos — eixo social e valores

| Campo | Sinal Esquerda (−1) | Sinal Direita (+1) | Neutro (0) | Base |
|---|---|---|---|---|
| `att_immigration` | `Positive`, `Enthusiast` | `Skeptical`, `Opposed` | `Neutral`, nulo | [J] (abertura vs. ameaça a grupo externo) [F] |
| `att_gun_ownership` | `Skeptical`, `Opposed` | `Positive`, `Enthusiast` | `Neutral`, nulo | [J] (ordem/segurança) [F] |
| `att_capital_punishment` | `Skeptical`, `Opposed` | `Positive`, `Enthusiast` | `Neutral`, nulo | [J] (punitividade/ordem) [F] |
| `values_priority` | `Community` (≈ universalismo/benevolência), `Autonomy` e `Novelty` (≈ autodireção/estimulação, abertura à mudança) | `Tradition` (≈ tradição/conformidade), `Security` (≈ segurança) | `Achievement`, nulo | [P]; abertura à experiência em [J] |
| `religiosity` | `Secular` | `Devout`, `Observant` | `Spiritual`, `Prefer not to say`, nulo | [P] (tradição/conformidade), [J] |

### 2.4 Campos deliberadamente não discriminantes

| Campo / valor | Motivo |
|---|---|
| `trust_level` | O dataset não especifica **em quais** instituições a confiança se refere. Confiança institucional muda de sinal conforme o grupo que controla as instituições (system justification em [J] é sensível ao contexto). Usá-lo como discriminante produz exatamente a incoerência do tipo "conservador com alta confiança em instituições progressistas". Fica reservado como eixo secundário de *contraste de estilo* entre personas do mesmo polo, nunca como critério de polo. |
| `values_priority = Achievement` | Cobre ~72% da amostra decodificada (1436/2000); sem poder discriminante. Na teoria de Schwartz, realização/poder (autopromoção) tem associação com direita apenas em alguns contextos nacionais em [P], não de forma estável. Tratado como neutro. |
| `values_priority = Autonomy` / `Novelty` | Mantidos como sinal de esquerda, porém **fraco** (peso 0,5 no escore): em [P] os valores de abertura à mudança tiveram poder explicativo menor e menos consistente que universalismo/benevolência. |
| `religiosity = Spiritual` | Ambíguo (não implica tradição/conformidade). Neutro. |

---

## 3. Regras de categorização

### 3.1 Definições

- **Sinal** de um indicador: `−1` (esquerda), `+1` (direita), `0` (neutro ou nulo), conforme as tabelas 2.2 e 2.3. Para `values_priority ∈ {Autonomy, Novelty}` o sinal é `−0,5`.
- **Concordante** com o polo-âncora: indicador com sinal do mesmo lado da âncora (negativo para Esquerda, positivo para Direita).
- **Contraditório**: indicador com sinal do lado oposto ao da âncora.
- `n_core_concord`, `n_core_contra`: contagens sobre os indicadores nucleares (2.2).
- `n_per_concord`, `n_per_contra`: contagens sobre os indicadores periféricos (2.3).
- `score` = soma dos sinais de todos os indicadores (nucleares e periféricos).

### 3.2 Regra POLO ESQUERDA

Um registro é classificado como **Esquerda** se, e somente se:

1. **Âncora:** `political_lean ∈ {Left, Center-left}`; **e**
2. **Sem contradição nuclear:** `n_core_contra = 0` (nenhum de `att_free_markets`, `att_government_regulation`, `att_labor_unions` aponta para a direita); **e**
3. **Evidência mínima de coerência:** `n_core_concord + n_per_concord ≥ 1` (pelo menos um indicador não nulo concorda com a âncora); **e**
4. **Tolerância periférica (depende do modo):**
   - modo `strict`: `n_per_contra = 0`;
   - modo `lenient`: `n_per_contra ≤ 1` **e** `(n_core_concord + n_per_concord) > n_per_contra`.

### 3.3 Regra POLO DIREITA

Um registro é classificado como **Direita** se, e somente se:

1. **Âncora:** `political_lean ∈ {Right, Center-right}`; **e**
2. **Sem contradição nuclear:** `n_core_contra = 0` (nenhum dos três indicadores econômicos aponta para a esquerda); **e**
3. **Evidência mínima de coerência:** `n_core_concord + n_per_concord ≥ 1`; **e**
4. **Tolerância periférica (depende do modo):**
   - modo `strict`: `n_per_contra = 0`;
   - modo `lenient`: `n_per_contra ≤ 1` **e** `(n_core_concord + n_per_concord) > n_per_contra`.

### 3.4 Registros excluídos (nem Esquerda nem Direita)

- `political_lean ∈ {Center, Apolitical}` ou nulo (meio incluído, [B]);
- qualquer contradição nuclear (`n_core_contra ≥ 1`);
- ausência total de indicadores secundários não nulos (`n_core_concord + n_per_concord + n_per_contra = 0`) — a âncora sozinha não basta para garantir coerência;
- violação da tolerância periférica do modo escolhido.

### 3.5 Modo recomendado e ordenação para seleção

- **Modo padrão para o experimento:** `strict`. Como o desenho precisa de apenas **duas** personas (uma por polo), não há custo em ser restritivo, e o ganho em coerência interna é o que blinda a validade da simulação.
- **Fallback:** `lenient`, caso o `strict` produza menos candidatos do que o necessário em um shard.
- **Ordenação dos candidatos elegíveis** (para escolher as personas mais "ricas" e prototípicas): ordenar por `|score|` decrescente, desempatando por `n_core_concord` decrescente e depois por número total de campos não nulos. Isto prioriza personas com mais evidência convergente, no espírito do passo 2 do relatório da Fase 2 ("personas mais ricas e internamente consistentes").

### 3.6 Modo experimental (âncora ausente) — não recomendado para o experimento principal

Para registros com `political_lean` nulo (≈80% da amostra), pode-se **inferir** o polo apenas quando `n_core_concord ≥ 1`, `n_core_contra = 0`, `n_per_contra = 0` e o total de concordantes for `≥ 3`. Registros assim classificados devem receber a flag `inferred = true` e ser reportados separadamente, pois não têm o autoposicionamento que fundamenta [P] e [B].

---

## 4. Verificação com os exemplos da Fase 2

| `source_record_id` | `political_lean` | Indicadores | Resultado (strict) |
|---|---|---|---|
| Q2142140 | Left | religiosity=Observant (+1, periférico); values=Achievement (0) | **Excluído** em `strict` (contradição periférica, zero concordantes). Excluído também em `lenient` (0 concordantes > 1 contraditório é falso). |
| Q6290862 | Center-left | values=Autonomy (−0,5); att_labor_unions=Positive (−1, nuclear); religiosity=Secular (−1) | **Esquerda** (3 concordantes, 0 contradições; score −2,5). |
| Q3104406 | Left | values=Community (−1); att_labor_unions=Positive (−1, nuclear); religiosity=Secular (−1) | **Esquerda** (3 concordantes; score −3). Candidata prototípica. |
| Q4079391 | Right | religiosity=Observant (+1); values=Security (+1); att_immigration=Neutral (0); trust=Verifying (ignorado) | **Direita** (2 concordantes, 0 contradições; score +2). Sem indicador nuclear, portanto menos prioritária na ordenação. |
| Q50318212 | Right | religiosity=Observant (+1); values=Achievement (0); free_markets=Enthusiast (+1); **gov_regulation=Enthusiast (−1, nuclear)**; unions=Enthusiast (−1, nuclear); guns=Enthusiast (+1); capital_punishment=Enthusiast (+1) | **Excluído**: duas contradições nucleares. Perfil internamente inconsistente ("entusiasta de tudo"). |
| Q5361378 | Center-right | values=Achievement (0); demais nulos | **Excluído**: nenhum indicador secundário não nulo. |

O resultado ilustra o comportamento desejado: a regra retém perfis coerentes (Q3104406, Q6290862, Q4079391) e rejeita tanto o perfil "esparso demais" (Q5361378) quanto o perfil "contraditório" (Q50318212), que uma filtragem apenas por `political_lean` aceitaria.

---

## 5. Limitações declaradas

1. **Origem euro-americana das evidências.** [J] e [P] baseiam-se majoritariamente em amostras da América do Norte e Europa; [P] observa que os valores têm pouco poder explicativo em países pós-comunistas, o que mostra que o significado de esquerda/direita é sensível ao contexto nacional. A transposição para personas de debate brasileiro é uma aproximação; os indicadores `att_gun_ownership` e `att_capital_punishment`, em particular, são temas de saliência historicamente norte-americana, embora tenham ganhado centralidade no debate brasileiro recente.
2. **Personas de fonte `wiki`.** A amostra decodificada contém apenas registros derivados de biografias; a cobertura de `political_lean` é de ~20%. A regra deve ser reavaliada quando os shards com registros *human-grounded* (GSS/Latinobarómetro) forem incluídos.
3. **Sinais binarizados.** A regra converte escalas ordinais de cinco pontos em sinais {−1, 0, +1}, descartando intensidade. Isso é intencional (objetividade e transparência), mas `Enthusiast` e `Positive` são tratados igualmente.
4. **Autoposicionamento como âncora.** Assume-se que `political_lean` reflete o que, nos surveys de origem, seria o autoposicionamento esquerda-direita. Para personas sintéticas derivadas de texto, trata-se de uma atribuição do processo de geração do dataset, não de uma resposta de survey.

---

## 6. Referências

BOBBIO, N. *Destra e sinistra: ragioni e significati di una distinzione politica*. Roma: Donzelli, 1994. [Ed. inglesa: *Left and Right: The Significance of a Political Distinction*. Cambridge: Polity Press, 1996. Ed. brasileira: *Direita e esquerda: razões e significados de uma distinção política*. São Paulo: Editora UNESP, 1995.]

FELDMAN, S.; JOHNSTON, C. D. Understanding the determinants of political ideology: implications of structural complexity. *Political Psychology*, v. 35, n. 3, p. 337–358, 2014. https://doi.org/10.1111/pops.12055

JOST, J. T.; GLASER, J.; KRUGLANSKI, A. W.; SULLOWAY, F. J. Political conservatism as motivated social cognition. *Psychological Bulletin*, v. 129, n. 3, p. 339–375, 2003. https://doi.org/10.1037/0033-2909.129.3.339

PIURKO, Y.; SCHWARTZ, S. H.; DAVIDOV, E. Basic personal values and the meaning of left-right political orientations in 20 countries. *Political Psychology*, v. 32, n. 4, p. 537–561, 2011. https://doi.org/10.1111/j.1467-9221.2011.00828.x

Arquivo complementar: `regras_categorizacao_esquerda_direita.json` (especificação executável das regras).
