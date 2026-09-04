# Prompt — geração dos slides de resultados preliminares

Este arquivo contém o prompt a ser entregue a um agente para produzir a
apresentação de **resultados preliminares** (2026-09-03).

**Diferença em relação à versão anterior deste arquivo:** o prompt antigo foi
escrito antes da execução do experimento, para uma reunião de acompanhamento
com o orientador, e pedia a saída como Artifact HTML. Este pede a edição de um
`.pptx` a partir do modelo do PESC e cobre os resultados já obtidos.

---

## Como usar

1. Reúna numa pasta única os arquivos listados na seção "Arquivos necessários"
   do prompt abaixo, preservando os caminhos relativos.
2. Coloque nessa pasta o `.pptx` do modelo do PESC.
3. Entregue a pasta ao agente junto com o prompt.

---

## Prompt

````
Você vai produzir uma apresentação de slides de **resultados preliminares** de
uma pesquisa de mestrado (PESC/COPPE/UFRJ, área de CSCW).

## Contexto da apresentação

- Duração: **15 a 20 minutos**. Estime ~1 minuto por slide e dimensione o
  conjunto de acordo (algo entre 18 e 24 slides, incluindo capa).
- Audiência: banca/turma de pós-graduação em Ciência da Computação, com
  interesse em CSCW/HCI. Não conhecem o trabalho em detalhe.
- Natureza: **resultados preliminares e trabalho em andamento**. A entrega
  final é em alguns dias, e há ajustes previstos até lá. A apresentação deve
  deixar isso explícito, sem apresentar o trabalho como concluído.
- Idioma: **português do Brasil**. Os temas dos debates e os textos das
  mensagens estão em inglês — mantenha-os no original e comente em português.
- Tom: técnico, direto, honesto. As limitações são parte do resultado, não
  algo a minimizar.

## Formato de saída

Edite o arquivo `.pptx` do modelo de apresentação do PESC que está na pasta.

REGRAS DO MODELO — siga à risca:
- **NÃO** altere o cabeçalho, rodapé, logotipos ou elementos de layout do
  modelo.
- **NÃO** preencha nome do autor, título institucional, data ou numeração de
  páginas. Deixe esses campos como estão no modelo, crus.
- Concentre-se **exclusivamente** no conteúdo do trabalho: títulos de slide,
  bullets, tabelas e inserção das figuras.
- Use os espaços de conteúdo do modelo. Não crie um design próprio nem
  substitua a identidade visual.

As figuras a inserir já existem como PNG a 300 dpi — insira os arquivos, não
recrie os gráficos.

## Arquivos necessários

Leia todos antes de escrever qualquer slide.

### Contexto geral e fundamentação
- `docs/deliverables/estado_atual_do_trabalho.md` — documento-base do trabalho:
  pergunta de pesquisa, fundamentação teórica (Angenot), dataset, pipeline,
  regra de classificação esquerda/direita, arquitetura de prompts, limitações,
  trabalhos futuros.
  **ATENÇÃO:** este documento foi escrito ANTES da execução do experimento. As
  Seções 7 e 8 ("o que já está produzido" / "próximos passos") estão
  desatualizadas — o que ali é descrito como pendente já foi executado. Use-o
  para contexto, teoria e decisões de projeto; para o estado atual e os
  resultados, use os arquivos das seções seguintes.
- `docs/deliverables/referencias.md` — todas as referências do trabalho em ABNT,
  agrupadas por função (fundamentação, classificação política, dataset,
  trabalho relacionado) e com uma lista consolidada para um slide único de
  bibliografia. **Use este arquivo para toda citação:** não reformate as
  referências a partir dos outros documentos nem invente metadados. Quatro
  entradas estão marcadas com ⚠ por terem metadados incompletos — cite-as como
  autor e ano, sem preencher o que falta.

### Construção das personas
- `dataset_analysis/docs/left right categories/regras_categorizacao_esquerda_direita.md`
  — a regra de classificação política e sua fundamentação teórica.
- `dataset_analysis/outputs/phase2_polarization_rule_review.md` — validação da
  regra em exemplos concretos.
- `debate_simulation/docs/persona_prompt_design_decisions.md` — decisões de
  construção dos prompts de persona.
- `debate_simulation/outputs/prompts/personas/polo_esquerda/persona_00.txt` e
  `.../polo_direita/persona_00.txt` — dois exemplos de persona pronta, para
  ilustrar o resultado da pipeline.

### Prompts do experimento
- `debate_simulation/prompts/debate behavior/debate behavior.txt`
- `debate_simulation/prompts/debate moderator D5/debate moderator D5.txt`
- `debate_simulation/prompts/debate judge/debate judge.txt`
- `debate_simulation/docs/debate_behavior_design_decisions.md` — decisões sobre
  o comportamento dos debatedores, incluindo a calibragem da escalada.
- `debate_simulation/docs/moderator_design_decisions.md` — decisões sobre o
  moderador, incluindo as falhas encontradas e corrigidas.

### Execução
- `debate_simulation/docs/local_models_decision.md` — por que o experimento
  migrou para modelos locais; as três falhas do free tier da OpenRouter e o
  viés de disponibilidade que elas introduziam.

### Resultados (a fonte dos números)
- `debate_simulation/analysis/runs/metrics_balanced/report.md` — relatório
  completo: corpus, resultado principal, as quatro tabelas com legenda e as
  quatro ressalvas metodológicas.
- `debate_simulation/analysis/runs/metrics_balanced/metrics.json` — todos os
  números em formato estruturado.
- `debate_simulation/analysis/runs/metrics_full/report.md` — os mesmos cálculos
  sobre o corpus completo (verificação de robustez).
- `debate_simulation/analysis/runs/metrics_balanced/examples/exemplo.md` — o
  exemplo trabalhado em forma de tabela, com as mensagens de cada turno.

### Figuras a inserir (PNG, 300 dpi)
Agregadas, em `debate_simulation/analysis/runs/metrics_balanced/figures/`:
- `g1_efeito_principal.png` + legenda em `g1_efeito_principal.txt`
- `g2_trajetoria_turnos.png` + `g2_trajetoria_turnos.txt`
- `g3_distribuicao_notas.png` + `g3_distribuicao_notas.txt`
- `g4_delta_por_celula.png` + `g4_delta_por_celula.txt`

Exemplo trabalhado, em `.../metrics_balanced/examples/` (páginas 16:9, na
ordem `p01` a `p10`): capa, mensagens do controle, mensagens do tratamento,
candidato × reformulação, e a comparação final.

### Pendências e limitações
- `debate_simulation/docs/metrics_pending.md` — o que NÃO foi calculado, por
  que, e o custo de fechar cada lacuna. **Fonte principal do slide de
  limitações.**

## Regra sobre os dados

Não invente números, resultados ou referências. Todo número apresentado deve
vir dos arquivos de resultados acima. Se algo parecer faltar, sinalize em vez
de preencher.

Atenção a duas leituras equivocadas que os dados permitem:
- A "preservação argumentativa" de 100% é **autodeclarada pelo moderador**, na
  mesma chamada que produziu a reformulação. Não é evidência de que a posição
  sobreviveu. Apresente sempre como declarada.
- A unanimidade de 100% do juiz mede estabilidade do decoding (temperatura 0),
  **não** robustez da rubrica. A consistência inter-juiz é que testaria isso, e
  está pendente.

## Conteúdo a cobrir

Cobrir toda a cadeia, do dataset ao resultado. Sugestão de estrutura — funda
ou desdobre slides se melhorar a clareza, mas mantenha a cobertura:

**Abertura (2 slides)**
1. Capa — título do trabalho (sem preencher os campos institucionais do modelo)
2. Pergunta de pesquisa e o recorte: o que a simulação responde e o que não
   responde

**Fundamentação (2–3 slides)**
3. As três patologias de Angenot — a tabela das três categorias com as
   referências (Angenot 2006/2008/2010)
4. Por que a dimensão D5 (Moderação Participativa) e por que simular: D5 atua
   antes da postagem, e só a simulação permite testá-la prospectivamente
5. Continuidade com o trabalho anterior (Moura e Brandi, 2026)

**Dados e personas (3–4 slides)**
6. O dataset MatrAIx Persona 1M e o funil de seleção (mostre os números)
7. A regra de classificação esquerda/direita e sua fundamentação (Bobbio 1994;
   Jost et al. 2003; Piurko et al. 2011; Feldman & Johnston 2014)
8. Um exemplo concreto de persona resultante, dos dois polos
9. Arquitetura de dois prompts: Camada 1 (identidade) + Camada 2
   (comportamento), com o mapeamento para as categorias de Angenot

**Desenho experimental (3–4 slides)**
10. O desenho: 2 temas × 6 pares de personas × 2 condições; 8 turnos por
    debate; juiz pontuando cada mensagem 3× (mediana)
11. Os três papéis (debatedor, moderador, juiz) e os modelos locais usados —
    e por que locais (o viés de disponibilidade do free tier)
12. O loop de moderação: candidato → avaliação → reformulação → publicação.
    Registre que a reformulação **substitui automaticamente** a candidata, sem
    aceite do autor, e que isso é deliberado: estima o efeito sob compliance
    total, ou seja, um **limite superior**
13. O corpus efetivamente analisado e os critérios de seleção (por que alguns
    debates foram descartados)

**Resultados (4–5 slides)**
14. Resultado principal — a redução de hostilidade, com a Figura 1
15. Trajetória ao longo dos turnos — Figura 2. **Este é o slide mais
    interessante:** mostra que a moderação não impede a escalada, apenas a
    atrasa; sob tratamento, o turno 8 está no nível que o controle atingiu no
    turno 3
16. Distribuição das pontuações — Figura 3 (o deslocamento da massa de 3–4
    para 1–2)
17. Consistência do efeito entre células — Figura 4
18. Acionamento do D5: taxa de intervenção e de reformulação

**Exemplo trabalhado (2–3 slides)**
19. Um debate concreto: as mensagens escalando sem moderação
20. O mesmo par com moderação, e o par candidato × reformulação lado a lado
    (as páginas `p08`/`p09` são as mais ilustrativas — mostram o mecanismo,
    não a média)

**Fechamento (3–4 slides)**
21. Limitações — as quatro ressalvas do relatório, com destaque para os
    históricos divergentes (a partir do turno 2 as condições não compartilham
    mais o mesmo histórico, e o desenho não separa efeito direto de desescalada
    indireta) e para a preservação autodeclarada
22. O que ainda falta até a entrega final — as métricas pendentes de
    `metrics_pending.md`, com o custo de cada uma
23. Trabalhos futuros — a incorporação da agência do autor sobre a
    reformulação (aceitar/editar/rejeitar), a taxa de aceitação como métrica, e
    a separação entre efeito direto e desescalada indireta via uma terceira
    condição
24. Referências — a lista consolidada de `referencias.md`. Se não couber num
    slide legível, divida em dois

## Diretrizes de conteúdo

- **Densidade:** slide de apresentação oral, não de leitura. Bullets curtos,
  nunca parágrafos corridos. O detalhe vai na sua fala, não na tela.
- **Sempre que houver número, mostre o número.** Os números são o argumento.
- **Sempre que houver decisão, mostre a motivação junto.**
- **Preserve as referências bibliográficas** nos slides de fundamentação,
  copiando-as de `referencias.md`. Nos slides, cite em formato curto (autor e
  ano); reserve a forma completa para o slide final de bibliografia.
- Nos slides de "antes e depois" (prompt, candidato × reformulação), mostre os
  dois lado a lado — o contraste é autoexplicativo.
- Trate as limitações como resultado. O trabalho é mais forte por declará-las.

## Entrega

Devolva o `.pptx` editado e, em texto, um resumo de até 5 linhas do que a
apresentação cobre, mais qualquer ponto onde faltou informação nos arquivos
fornecidos.
````

---

## Notas de uso

- As fontes de verdade dos resultados são os diretórios
  `debate_simulation/analysis/runs/metrics_balanced/` e `metrics_full/`. Eles
  são **derivados** e regeneráveis: se o corpus mudar, rode
  `scripts/compute_metrics.py` e `scripts/build_showcase.py` antes de regerar
  os slides.
- `estado_atual_do_trabalho.md` está desatualizado nas Seções 7 e 8. O prompt
  avisa o agente sobre isso, mas o ideal é atualizá-lo antes da entrega final.
- Os resultados apresentados usam o **corpus balanceado** (10 células, 20
  debates) como principal, com o completo (21 réplicas, 42 debates) como
  verificação de robustez. As duas análises concordam.
- A hipótese de que mais turnos aumentariam o efeito **não se sustenta nos
  dados**: o Δ por turno atinge o pico no turno 6 e encolhe depois, porque o
  controle satura no teto da escala enquanto o tratamento continua subindo. Se
  a apresentação mencionar turnos adicionais, deve ser como pergunta em aberto
  (o tratamento também satura?), não como previsão de efeito maior.
