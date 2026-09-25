# Notas de Produção — Position Paper ISMSIT 2026

## Conferência

| Item | Valor |
|---|---|
| Evento | 10th ISMSIT, 13–15/11/2026, Antalya (híbrido), patrocínio técnico IEEE |
| Submissão | **25/09/2026** (prazo prorrogado), via SETCMS: https://www.set-science.com/org/ismsit2026/ |
| Notificação | 15/10/2026 |
| Template | IEEE conference |
| Idiomas aceitos | Inglês ou turco |
| Revisão | Duplo-cega, ao menos 3 revisores |
| Similaridade máxima | 20% sem referências / 30% com referências |
| Limite de páginas | Não informado no site; alvo adotado: 4–6 páginas |

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `ismsit2026_position_paper.tex` | Fonte LaTeX (IEEEtran `conference`; pdflatex → bibtex → pdflatex ×2) |
| `references.bib` | 18 entradas: 17 do `docs/artigo_final/references.bib` + Brandi et al. (2026) |
| `ismsit2026_position_paper.docx` | Mesmo conteúdo, no padrão do template IEEE para Word (Letter, 2 colunas, Times 10pt), para abrir no Google Docs |
| `ismsit2026_position_paper_preview.pdf` | Prévia compilada do `.tex`: 6 páginas (recompilada em 2026-09-25) |
| `figures/pipeline_ismsit.{tex,pdf,png}` | Diagrama conceitual do pipeline (Fig. 1). A fonte é TikZ e compila com pdflatex ou xelatex; o PDF é incluído no `.tex` e o PNG (300 dpi) no `.docx` |
| `figures/pipeline_ismsit.drawio` | O mesmo diagrama em formato editável do draw.io (diagrams.net) |

## Figura 1 — pipeline conceitual (24/09/2026)

- Citada na Seção IV-A e inserida como `figure*` (largura dupla) com 92% da largura do texto. Na largura total, o paper ia para 6 páginas, com só o fim das referências na última; a 92%, volta a 5.
- Segue o padrão visual do diagrama de referência (`docs/support materials/images/diagram example multi llm wbs agent.png`): faixas com rótulo vertical, painéis com aba de título, cartões, ícones por papel e setas coloridas por tipo de dado, com legenda.
- Conteúdo restrito ao que o paper já afirma (Seções II-B, III e IV). Não aparecem escala 0–4, valor do limiar, regra de classificação, modelos, temperaturas, número de turnos, temas nem resultados. A fronteira do moderador aparece só como "argumento → pessoa".
- No `.docx`, a figura fica numa seção contínua de uma coluna entre duas seções de duas colunas (padrão do template IEEE para Word).
- O artigo completo tem um diagrama próprio, operacional e em português: `docs/artigo_final/figures/pipeline_cscw.*`.
- **Correções de layout em 24/09/2026:**
  - a seta vermelha para "Observable in simulation" nascia dentro do cartão "Records" e cruzava o texto; agora sai da base do cartão;
  - o texto do passo 1 do moderador encostava na borda do painel; a largura foi reduzida;
  - o passo 2 foi afastado do rótulo da fronteira.

  PDF, PNG, `.docx` e prévia foram regenerados. O `.docx` passou a incluir o ajuste do autor no parágrafo de Mutz & Reeves (II-A).
- **Versão editável (`pipeline_ismsit.drawio`).**
  - Onde abrir: https://app.diagrams.net, a extensão "Draw.io Integration" do VS Code ou o Google Drive (Abrir com → diagrams.net).
  - Como foi feita: gerada a partir da geometria do TikZ, com o mesmo conteúdo, as mesmas cores e os mesmos ícones Font Awesome (SVG embutido). Os cartões são contêineres, e o texto do corpo acompanha o cartão. As setas principais estão ligadas às caixas.
  - Diferenças em relação ao TikZ: o navegador não hifeniza, então algumas caixas ficaram um pouco mais altas.
  - Para usar uma versão editada no paper: File → Export as → PDF, com "Crop" marcado, substituindo `pipeline_ismsit.pdf`. Para o `.docx`, exportar PNG com zoom de 300%, substituindo `pipeline_ismsit.png`.
  - A partir daí, a fonte TikZ deixa de refletir a figura.

## Decisões

- **Idioma: inglês**, porque a conferência não aceita português.
- **Versão anonimizada.** O autor aparece como "Anonymous Author(s)". O bloco com os quatro autores reais está comentado no `.tex`, pronto para a camera-ready. O `.docx` e o PDF não trazem autor nos metadados. O trabalho predecessor é citado em terceira pessoa (Moura & Brandi [2]).
- **Gênero: position paper.** Sem resultados, números do experimento ou detalhes do pipeline. O texto declara que o protocolo e os achados serão reportados separadamente.
- **Título:** *Moderating Before Publication: A Position on LLM-Assisted Prospective Moderation of Unproductive Debates* (alterado em 2026-09-25; antes: *Moderating What Is Never Published: …*).
- **Anotações deixadas no `main.tex` foram respeitadas:**
  - o problema é tratado como inerente ao diálogo (Angenot) e amplificado pela arquitetura das plataformas;
  - "participatory" aparece uma única vez, ao nomear D5 no modelo; no restante do texto usa-se *prospective moderation*;
  - a RQ3 foi removida (o paper não tem RQs);
  - o parágrafo marcado (REVISAR) foi reescrito como Seção IV-A.
- **Terminologia em inglês** alinhada ao paper CHIRA: D1 *Interactional Deceleration* … D5 *Participatory Moderation*; *discursive incommensurability*, *rhetoric of incomprehension*, *illusion of rationality*. Nenhuma frase do CHIRA foi reaproveitada, por causa do limite de similaridade.

## Mapa original → derivado

| `main.tex` | Position paper |
|---|---|
| I. Introdução | I. Introdução, reescrita como posição e sem RQs |
| II-A. Incivilidade | II-A |
| II-B. Moderação prospectiva | II-B e IV-A (a Tabela I sintetiza o contraste entre as duas lentes) |
| II-C. Simulação e personas | II-B, último parágrafo |
| III-A. Patologias de Angenot | III-A |
| III-B. Dimensão D5 | III-B |
| IV-D. Justificativa da escala e do limiar | III-C, sem a escala 0–4 e sem o valor do limiar |
| IV-B/C/E. Personas, prompts e juiz | IV-B, só os princípios, em quatro condições |
| VI-C, VI-D, VII e VIII | V, quatro questões abertas |
| IX. Conclusão | VI |

## Retido deliberadamente (reservado para o artigo completo)

- Todos os resultados (médias, Δ, trajetória por turno, distribuição das notas, taxa de reformulação, unanimidade do juiz) e todas as figuras.
- A escala 0–4 com descritores e ancoragens, e o limiar ≥ 2.
- A regra de classificação política das personas (âncora, eixos econômico e social, condições, score, exemplo, funil) e as obras que a sustentam: Bobbio, Jost et al., Piurko et al., Feldman & Johnston.
- A arquitetura de dois prompts, os modelos, as temperaturas, a infraestrutura local, os filtros do corpus, os temas e os parâmetros do desenho.
- Os protocolos detalhados de trabalhos futuros: anotadores, α de Krippendorff, *leave-one-rater-out*, condição sem reescrita, limiar ≥ 3.
- O achado "retarda, não suprime" aparece apenas como pergunta aberta (Seção V, *Time and composition*).

## Referências

- 17 das 18 citadas vêm do `.bib` aprovado.
- **Adição em 24/09/2026, a pedido do autor:** `brandi2026nudge`, citada como [14] na Seção II-B. É o position paper de Brandi, Correia, Xexéo e Schneider sobre *nudge-based text detoxification*. Os metadados foram tirados do PDF em `docs/support materials/papers/`, que não informa o evento, só o rodapé IEEE com o ISBN 979-8-3315-8150-3 (2026). Uma busca pelo ISBN também não identificou o evento. Por isso a entrada está como `@misc` ("Position paper, 2026"), marcada `VERIFICAR`. As citações seguintes foram renumeradas: Chuang [15], Li [16], Angenot 2010 [17], Krippendorff [18].
- Brandi e Schneider são coautores desta submissão. A citação está em terceira pessoa, o que é compatível com a revisão duplo-cega.
- As notas `[VERIFICAR]` viraram comentários, porque o IEEEtran imprime o campo `note`.
- Siglas e nomes próprios foram protegidos com chaves: `{AI}`, `{LLM}`, `{MatrAIx Persona 1M}`, `{Internet}`, `{Rasch}`, `{Krippendorff}`, `{Patterns}`. O IEEEtran.bst passa os títulos para caixa baixa. **O mesmo problema existe em `docs/artigo_final/references.bib`, que não foi alterado.**

## Verificações

- [x] Compilado com Tectonic (XeTeX, com TeX Gyre Termes no lugar da Times): 5 páginas Letter, sem erros, sem citações nem referências cruzadas indefinidas.
- [x] `.docx` validado contra os schemas OOXML. Estrutura conferida contra o PDF: seções, citações [1]–[17], "Section II-A", Tabela I.
- [x] Nenhuma primeira pessoa no texto.
- [ ] Compilar com pdflatex (Overleaf) e conferir a paginação final.
- [ ] Abrir o `.docx` no Google Docs e conferir as duas colunas. Se a importação falhar, ajustar em Formatar → Colunas.
- [ ] Conferir os campos `[VERIFICAR]` das referências usadas: moura2026hostility, coe, rains, kenski, bentivegna, mutz, kennedy, krippendorff, katsaros, tessler, chuang, li.
- [ ] Completar `brandi2026nudge`: evento, páginas e DOI. Depois, trocar o tipo para `inproceedings` e atualizar a entrada correspondente em `REFS` do conversor do `.docx` (ou editar o texto da referência direto no Google Docs).
- [ ] Rodar verificação de similaridade antes de submeter (limites de 20% e 30%).
- [ ] Camera-ready: restaurar os autores (a grafia do coautor Brandi segue pendente) e inserir a nota de copyright IEEE.
