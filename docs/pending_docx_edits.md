# Edições pendentes em `Plano_Monografia_CSCW_v6.docx`

O plano de monografia está em `.docx` e **não foi editado** nesta tarefa
(edição direta fora do escopo). As alterações abaixo replicam, no plano, o
reenquadramento já aplicado a
[`deliverables/estado_atual_do_trabalho.md`](deliverables/estado_atual_do_trabalho.md):
a substituição automática da candidata pela reformulação do D5 passa a ser
declarada como estimativa sob *compliance* total — um **limite superior**
(*upper bound*) — com a limitação correspondente e o trabalho futuro.

Arquivo: [`support materials/papers/Plano_Monografia_CSCW_v6.docx`](support%20materials/papers/Plano_Monografia_CSCW_v6.docx)

Referências de localização apuradas por leitura do `word/document.xml`
(numeração de parágrafo não vazio, contando a partir de 0).

---

## Edição 1 — Seção 4 "Fluxo em alto nível: como o D5 opera no loop"

**Onde:** logo após o parágrafo "**Intervenção D5 (só no tratamento)**"
(¶79) e antes de "**Alternância**" (¶80).

**Ação:** inserir novo parágrafo.

> **Substituição automática e o que ela significa.** Nesta simulação, a
> reformulação produzida pelo moderador D5 substitui automaticamente a mensagem
> candidata da persona, sem etapa de aceite pelo autor. Trata-se de uma decisão
> metodológica deliberada: o desenho estima o efeito do D5 sob compliance total
> — um cenário de limite superior (*upper bound*) — isolando a pergunta "a
> reformulação, quando aplicada, preserva o argumento e reduz a hostilidade da
> trajetória do debate?" da pergunta comportamental "os autores aceitariam a
> reformulação?". A segunda pergunta é investigada empiricamente com
> participantes humanos: no desenho de Argyle et al. (2023), o autor pode
> aceitar, editar ou ignorar as sugestões de reformulação; nos experimentos de
> campo de Katsaros et al. (2022) no Twitter, a maioria das mensagens
> sinalizadas foi publicada sem revisão, com cerca de 9% canceladas e 22%
> revisadas. O presente experimento responde à primeira pergunta em ambiente
> simulado; seus resultados devem, portanto, ser interpretados como estimativa
> do efeito máximo da intervenção, e não do efeito esperado em uma implantação
> com usuários reais.

---

## Edição 2 — Seção 7 "Limitações já esperadas"

**Onde:** ao final da lista de limitações, após "**Gap do contexto
brasileiro**" (¶115) e antes de "Ativos reutilizáveis na dissertação" (¶116).

**Ação:** inserir nova limitação, seguindo a formatação das existentes
(título em negrito seguido de ponto final e texto corrido).

> **Ausência de agência do autor sobre a reformulação.** O desenho não modela a
> decisão do autor de aceitar, editar ou rejeitar a reformulação do moderador —
> etapa presente nos paradigmas empíricos de moderação prospectiva assistida
> (Argyle et al., 2023; Katsaros et al., 2022) e em abordagens de mediação
> deliberativa com IA (Tessler et al., 2024). A opção pela substituição
> automática decorre de uma restrição de validade: a decisão de aceite, se
> simulada por um agente LLM, careceria de âncora empírica e estaria sujeita ao
> viés de consenso e polidez documentado em agentes LLM (Chuang et al., 2023), o
> que tenderia a produzir taxas de aceitação artificialmente altas e,
> consequentemente, a superestimar o efeito do D5. Em decorrência dessa escolha,
> os resultados representam um limite superior do efeito da intervenção sob
> compliance total, e a taxa de aceitação — variável de resultado central nos
> estudos com humanos — não é observável neste desenho.

---

## Edição 3 — Trabalhos futuros

**Onde:** o plano **não tem seção própria de trabalhos futuros**. O parágrafo
"Ativos reutilizáveis na dissertação" (¶116) é o que mais se aproxima, e a
Seção 7 já remete a trabalho futuro em duas limitações ("A referência humana
completa fica como trabalho futuro"; calibração brasileira).

**Duas opções — decisão do autor:**

- **(a)** Criar seção "8. Trabalhos futuros" após a Seção 7, com o texto abaixo.
- **(b)** Inserir o texto como parágrafo final da Seção 7, na esteira das
  demais remissões a trabalho futuro já existentes ali.

> **Incorporação da agência do autor sobre a reformulação.** Estender o desenho
> com um braço experimental em que a persona debatedora recebe a mensagem
> original e a reformulação do D5 e decide aceitá-la, editá-la ou rejeitá-la,
> espelhando o fluxo de Argyle et al. (2023), com a taxa de aceitação como nova
> métrica de resultado. Para mitigar o viés de consenso de agentes LLM (Chuang
> et al., 2023), duas estratégias devem ser consideradas: (i) parametrizar a
> decisão de aceite com taxas empíricas da literatura (e.g., Katsaros et al.,
> 2022), em vez de delegá-la ao agente; e (ii) validação com humanos no loop, em
> que participantes reais tomam ou avaliam a decisão de aceite sobre
> reformulações geradas na simulação.

---

## Edição 4 — Bibliografia

Acrescentar as quatro referências, no estilo bibliográfico do plano:

- ARGYLE, L. P.; BAIL, C. A.; BUSBY, E. C.; GUBLER, J. R.; HOWE, T.; RYTTING,
  C.; SORENSEN, T.; WINGATE, D. *Leveraging AI for democratic discourse: chat
  interventions can improve online political conversations at scale.*
  Proceedings of the National Academy of Sciences (PNAS), v. 120, n. 41,
  e2311627120 (2023). DOI: 10.1073/pnas.2311627120
- KATSAROS, M.; YANG, K.; FRATAMICO, L. *Reconsidering Tweets: intervening
  during Tweet creation decreases offensive content.* In: Proceedings of the
  International AAAI Conference on Web and Social Media (ICWSM), v. 16 (2022).
  arXiv:2112.00773
- TESSLER, M. H.; BAKKER, M. A. et al. *AI can help humans find common ground in
  democratic deliberation.* Science, v. 386 (2024)
- CHUANG, Y.-S. et al. *Simulating opinion dynamics with networks of LLM-based
  agents.* arXiv:2311.09618 (2023)

**Antes de inserir**, conferir os metadados pendentes listados em
[`PENDENCIAS_REVISAO.md`](PENDENCIAS_REVISAO.md) (seção 1) — três das quatro
referências têm campos a verificar no PDF original.

---

## Observação sobre versionamento

A v5 foi preservada como histórico quando a v6 foi gerada. Se estas edições
forem aplicadas, considere gerar uma **v7** pelo mesmo critério, preservando a
v6.
