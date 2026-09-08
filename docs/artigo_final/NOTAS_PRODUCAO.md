# Notas de Produção do Artigo Final

## Metadados

| Item | Valor |
|---|---|
| Data de geração | 08/09/2026 |
| Predecessor | `docs/support materials/templates/latex/gc alternative plataforms.tex` |
| Template/classe LaTeX | `IEEEtran`, opção `[conference]` |
| Estilo bibliográfico | `IEEEtran` (BibTeX puro, via `\usepackage{cite}`) |
| Idioma | pt-BR (`babel[brazil]`) |
| Extensão | 7.941 palavras de prosa (predecessor: 9.896) — **−19,8%**, dentro do limite de ±20% |
| Tabelas | 5 |
| Figuras | 5 (PNG a 300 dpi, copiadas de `analysis/runs/metrics_balanced/`) |
| Referências | 22 entradas, todas citadas |

---

## Problema encontrado no predecessor

**O `references.bib` do predecessor está vazio (0 bytes).** As 32 chaves
citadas no `.tex` não possuem entradas correspondentes em nenhum arquivo do
repositório.

Consequência: a regra de "copiar entradas verbatim do predecessor" não pôde ser
aplicada — não havia o que copiar. Reconstruir essas entradas violaria a regra
anti-alucinação, já que os metadados não existem em nenhuma fonte disponível.

**Decisão tomada (aprovada pelo pesquisador):** citar do predecessor apenas o
que é fundamentável a partir da documentação atual. Das 32 chaves originais,
três se referem a obras de Angenot já presentes em `referencias.md`
(`angenot2006divergent`, `angenot2008dialogues`, `angenot2010discurso`) e foram
mantidas. O predecessor como um todo é citado por meio de `moura2026hostility`.
As 29 chaves restantes — Nonaka, Pimentel, Schneider, Kietzmann, entre outras —
**não foram incluídas**.

**Ação recomendada:** se o `.bib` correto existir em outro local (por exemplo,
no Overleaf do artigo anterior), vale reintroduzir as referências pertinentes,
sobretudo nas Seções I e III-B, onde a discussão do modelo de cinco dimensões
se beneficiaria de citação mais granular.

---

## Referências pendentes de verificação

Todas marcadas com `note = {[VERIFICAR ...]}` no `references.bib`.

| Chave BibTeX | Campo(s) a verificar | Origem |
|---|---|---|
| `moura2026hostility` | Páginas, editora dos proceedings, DOI, cidade | `referencias.md` |
| `li2026matraix` | Lista completa de autores; título exato do preprint | `referencias.md` |
| `katsaros2022reconsidering` | Páginas nos proceedings | `referencias.md` |
| `tessler2024ai` | Lista completa de autores, número da edição, DOI | `referencias.md` |
| `chuang2023simulating` | Lista completa de autores; venue de publicação | `referencias.md` |
| `bentivegna2022searching` | Páginas no PDF | `fundamentacao_escala_hostilidade.md` |
| `coe2014online` | DOI exato no PDF | `fundamentacao_escala_hostilidade.md` |
| `kennedy2020constructing` | Se publicado em venue além do arXiv | `fundamentacao_escala_hostilidade.md` |
| `kenski2020perceptions` | Páginas no PDF | `fundamentacao_escala_hostilidade.md` |
| `mutz2005new` | DOI exato no PDF | `fundamentacao_escala_hostilidade.md` |
| `rains2017incivility` | Páginas no PDF | `fundamentacao_escala_hostilidade.md` |
| `krippendorff2011computing` | Se há versão em periódico; a canônica pode ser Krippendorff (2004), *Content Analysis*, 2. ed., Sage | `referencias.md` |

**Nenhum campo foi inferido ou completado por estimativa.** O registro
detalhado está em `docs/PENDENCIAS_REVISAO.md`.

---

## Lacunas de conteúdo

| Seção | Situação | Ação necessária |
|---|---|---|
| V. Resultados | **Sem lacuna** — dados reais disponíveis | Nenhuma |
| Todas as demais | Material de apoio suficiente | Nenhuma |

Diferentemente do previsto no prompt de produção, os experimentos já haviam
sido executados e os resultados estavam disponíveis em
`docs/artigo_base/09_resultados_e_dados/`. A Seção V reporta dados reais, não
protocolo esperado.

**Divergência de nome de coautor.** O predecessor registra **Luiz Filipe
Brandi** (`brandi@cos.ufrj.br`); o arquivo `referencias.md` registra
`BRANDI, C.`. Adotou-se a grafia do predecessor no bloco de autores e no
`.bib`. Conferir qual está correta antes da submissão.

---

## Decisões de redação

**Estrutura.** Nove seções, contra onze do predecessor. A diferença decorre da
natureza do trabalho: o predecessor é comparativo-documental e dedica cinco
seções à análise de plataformas; este é experimental e concentra o detalhamento
em Metodologia (oito subseções) e Resultados (cinco subseções).

**Voz e registro.** Mantidos os do predecessor: impessoal ("este trabalho",
"observa-se", "adotou-se"), sem primeira pessoa.

**Condensação.** Os documentos de apoio somam dezenas de milhares de palavras em
registro discursivo. A redução mais significativa foi na regra de classificação
política, cujo documento de fundamentação tem mais de 15 KB e foi condensado em
quatro parágrafos, preservando as quatro obras que a sustentam, os três campos
excluídos e os números do funil.

**Números do funil de seleção.** Incorporados na Seção IV-B (200.000 registros →
2.000 decodificados → 399 com atributo político → 101 e 20 elegíveis → 20
selecionadas), por serem argumento e não apenas contexto.

**Escala de hostilidade como tabela.** Conforme exigido, em `table*` de largura
dupla, com as quatro colunas (Nível, Definição operacional, Ancoragem
conceitual, Referências), cada nível ancorado em duas ou três referências.

**Limitações consolidadas.** Sete limitações unificadas a partir de três fontes
(`estado_atual_do_trabalho.md` §10, `fundamentacao_escala_hostilidade.md` §6,
`metrics_pending.md`), sem duplicação, cada uma com o que falta, por que falta e
o impacto interpretativo.

**Trabalhos futuros consolidados.** Seis frentes a partir das mesmas fontes,
ordenadas por dependência: validação da escala precede a calibração do juiz, que
por sua vez viabiliza a verificação de preservação argumentativa.

**Duas leituras equivocadas prevenidas explicitamente.** A Seção VI-D foi
acrescentada para tratar dos dois números que aparentam robustez sem tê-la: a
unanimidade de 100% do juiz (que decorre de temperatura zero) e a preservação
argumentativa de 100% (que é autodeclarada). Sem essa seção, ambos seriam
naturalmente lidos como validação forte dos instrumentos.

**Hipótese de turnos adicionais.** A Seção V-B registra que a diferença por
turno *diminui* após o sexto turno, contrariando a expectativa de que debates
mais longos ampliariam o efeito. A formulação adotada trata o comportamento do
tratamento em debates longos como questão em aberto, não como previsão.

---

## Verificações já realizadas

- [x] Toda `\cite{}` tem entrada no `.bib` — 22 citadas, 22 entradas, zero órfãs
      em ambos os sentidos
- [x] Todo `\ref{}` tem `\label{}` correspondente — 10 e 10, coincidentes
- [x] Todas as figuras referenciadas existem em `figures/`
- [x] Nenhum campo bibliográfico inventado; incompletos marcados `[VERIFICAR]`
- [x] Preâmbulo idêntico ao do predecessor (classe, pacotes, `arraystretch`,
      `newcolumntype`)
- [x] Extensão dentro de ±20% do predecessor
- [x] Encoding UTF-8 com acentuação preservada
- [x] Nenhum arquivo original do repositório alterado

## Verificações pendentes

- [ ] **Compilar com `pdflatex` + `bibtex` + `pdflatex` ×2** — não foi possível
      verificar localmente: não há distribuição LaTeX instalada nesta máquina
      (`pdflatex` e `bibtex` ausentes). Compilar antes de qualquer submissão.
- [ ] Conferir os 12 campos `[VERIFICAR]` contra os PDFs originais
- [ ] Confirmar a grafia do nome do coautor (Brandi, C. vs. Luiz Filipe Brandi)
- [ ] Decidir sobre a reintrodução das 29 referências órfãs do predecessor
- [ ] Revisar o posicionamento das figuras após a primeira compilação — o
      `IEEEtran` em duas colunas pode deslocá-las em relação ao texto
- [ ] Verificar se a `table*` da escala de hostilidade cabe na largura da página
      sem estouro
