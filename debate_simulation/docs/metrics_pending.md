# Métricas pendentes

Registro do que **não** foi calculado nos resultados preliminares, por que não,
e quanto custa fechar cada lacuna. Complementa `analysis/runs/*/report.md`, que
traz apenas o que os dados em disco sustentam hoje.

Data: 2026-09-02.

---

## 1. Preservação argumentativa verificada

**Status:** pendente. Existe apenas a versão **autodeclarada**.

O moderador preenche o campo `argument_preserved` na mesma chamada em que
produz a reformulação. Nos 42 debates do corpus completo esse campo foi
preenchido em 100% das reformulações — o que mede cobertura do campo, não
sobrevivência da posição.

O piloto documentado em `moderator_design_decisions.md` §2 registra o problema
concreto: em 2 de 3 casos analisados o moderador declarou preservação enquanto
carregava o ataque para o texto publicado, e num deles acrescentou "people like
you are part of the problem", violando a instrução de não adicionar conteúdo.

**Como fechar:** um avaliador independente (prompt e modelo distintos do
moderador) recebendo o par candidato/reformulação e respondendo se a posição
substantiva sobreviveu. São ~160 pares no corpus balanceado, ~330 no completo.

**Custo:** novo prompt, novo módulo de avaliação, ~2–4 h de execução local.

**Como reportar até lá:** "preservação declarada pelo moderador", nunca
"preservação verificada".

---

## 2. Reformulação efetiva

**Status:** pendente na forma rigorosa.

A pergunta que separa "o D5 não funciona" de "este moderador não executou o D5":
em que fração das intervenções a nota do juiz **de fato cai** em relação ao
candidato original?

**Obstáculo:** o juiz nunca pontuou os candidatos. Por desenho, ele avalia
apenas o texto publicado (`judge/schema.py` documenta a escolha: moderador e
juiz são medições independentes, e confundi-las compararia uma mensagem com sua
própria substituta). No controle candidato e publicado coincidem; no tratamento
o candidato só foi visto pelo moderador.

**Substituto disponível, com ressalva:** comparar a nota do *moderador* para o
candidato com a nota do *juiz* para o publicado. São avaliadores diferentes sob
prompts diferentes, então a diferença mistura o efeito da reformulação com a
discordância entre dois modelos. Utilizável como indicativo, não como
resultado principal.

**Como fechar:** rodar o juiz sobre os candidatos das mensagens reformuladas,
com o mesmo prompt e as mesmas 3 execuções. ~160 mensagens no corpus
balanceado.

**Custo:** ~1,5 h de execução local; o módulo de julgamento já existe e
aceitaria os candidatos sem alteração estrutural.

---

## 3. Consistência inter-juiz

**Status:** pendente. A intra-juiz está calculada (unanimidade em 100% das
mensagens, amplitude 0 em todas).

O desenho (§8.4) prevê a inter-juiz como opcional: modelos A e B avaliando o
mesmo corpus que C avaliou, para verificar se a escala é lida de modo
semelhante por famílias distintas.

**Observação:** a unanimidade perfeita da intra-juiz é menos informativa do que
parece — o juiz roda a temperatura 0, então as três execuções são quase
determinísticas. Ela confirma estabilidade do decoding, não robustez da rubrica.
A inter-juiz é que testaria a rubrica.

**Custo:** ~330 mensagens × 2 modelos × 3 execuções, várias horas locais.

---

## 4. Auditoria humana (30 pares)

**Status:** insumo pronto, anotação pendente — é trabalho humano, não de código.

`analysis/runs/metrics_balanced/amostra_auditoria.csv` traz 30 pares
candidato/reformulação sorteados com semente fixa (42), reprodutíveis a partir
do mesmo corpus. O arquivo já inclui as colunas a preencher:

- `posicao_preservada` — a posição substantiva sobreviveu?
- `hostilidade_reduzida` — a reformulação de fato moderou?
- `observacoes`

Serve simultaneamente como validação humana das métricas 1 e 2.

---

## 5. Separação entre efeito direto e desescalada indireta

**Status:** não endereçável no desenho atual.

A partir do turno 2 as duas condições deixam de compartilhar histórico: sob
tratamento, os debatedores respondem a mensagens já reformuladas. O Δ observado
soma dois mecanismos:

1. **efeito direto** — a mensagem hostil foi reescrita antes de publicar;
2. **desescalada indireta** — o interlocutor, recebendo texto mais brando,
   responde com menos hostilidade.

Separá-los exigiria uma terceira condição em que o moderador avalia e registra
mas **não** substitui o texto publicado. Isso dobra o custo de execução e é
proposta para o próximo ciclo, não correção do atual.

A ressalva já consta em `report.md` e na legenda da Figura 2.

---

## Resumo

| Métrica | Status | Custo estimado |
|---|---|---|
| Efeito principal | **calculado** | — |
| Acionamento do D5 | **calculado** | — |
| Consistência intra-juiz | **calculado** | — |
| Preservação declarada | **calculado** (autodeclarada) | — |
| Preservação verificada | pendente | 2–4 h + novo prompt |
| Reformulação efetiva | pendente | ~1,5 h |
| Consistência inter-juiz | pendente | várias horas |
| Auditoria humana | amostra pronta | trabalho manual |
| Efeito direto vs. indireto | requer nova condição | próximo ciclo |
