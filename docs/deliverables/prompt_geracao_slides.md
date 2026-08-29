# Prompt — geração dos slides de acompanhamento com o orientador

Este arquivo contém o prompt a ser entregue a um agente para produzir a
apresentação. O conteúdo-fonte é
[`estado_atual_do_trabalho.md`](estado_atual_do_trabalho.md).

---

## Prompt

```
Você vai produzir uma apresentação de slides para uma reunião de
acompanhamento de mestrado (PESC/COPPE/UFRJ) entre o aluno e seu orientador.

## Fonte de conteúdo

Use EXCLUSIVAMENTE o arquivo `docs/deliverables/estado_atual_do_trabalho.md`
como fonte. Ele já contém todo o conteúdo necessário: contexto, fundamentação
teórica, dataset, pipeline, decisões de design, entregáveis, próximos passos,
pontos de alinhamento e limitações.

Não invente dados, números, referências bibliográficas ou resultados que não
estejam nesse arquivo. Se algo parecer faltar, sinalize em vez de preencher.

## Objetivo da apresentação

Mostrar ao orientador, de forma didática e objetiva, tudo que já foi feito
desde o dataset até a fase atual — passando por cada escolha, sua motivação,
as regras construídas e seus fundamentos teóricos — e o que vem a seguir.

A apresentação deve permitir que o orientador:
1. Entenda o fluxo completo sem ter lido o código
2. Avalie se as decisões metodológicas são defensáveis para o artigo
3. Se posicione sobre os pontos de alinhamento em aberto (Seção 9 da fonte)

## Público e tom

- Público: um orientador de mestrado, pesquisador de CSCW/HCI. Conhece o
  trabalho anterior (Moura e Brandi, 2026) e o referencial de Angenot.
- Tom: técnico, direto, honesto. Sem marketing, sem "vendas".
- Idioma: **português do Brasil**.
- Trate escolhas discutíveis como discutíveis: os trade-offs assumidos e os
  pontos em aberto são parte do que se quer discutir na reunião, não algo a
  esconder.

## Estrutura sugerida (~19–23 slides)

1. **Capa** — título provisório do trabalho, continuidade de Moura e Brandi (2026)
2. **Onde estamos** — cronograma de 4 semanas, posição atual (início da Semana 1), o que está pronto vs. pendente
3. **Pergunta de pesquisa** — a pergunta central e o recorte declarado (o que a simulação NÃO responde)
4. **Por que D5 e por que simular** — D5 atua antes da postagem; só a simulação permite testá-la na forma prospectiva; por que não D2
5. **Fundamentação: as três patologias de Angenot** — tabela das três categorias, com referências
6. **O dataset MatrAIx Persona 1M** — o que é, o que é relevante, o desafio da decodificação do BLOB
7. **Pipeline construído** — o diagrama de fases (Fase 0 → 3) e o funil de números (1M → 200k → 2k → 20)
8. **Problema encontrado no filtro ingênuo** — os casos Q55759875 e Q50318212 como evidência concreta
9. **A regra de classificação — fundamentação** — as três obras (Bobbio, Jost et al., Piurko et al.) e o que cada uma fundamenta
10. **A regra de classificação — estrutura** — âncora + indicadores nucleares/periféricos + critérios de inclusão
11. **Campos deliberadamente excluídos** — sobretudo `trust_level` e por quê (é um bom slide: mostra rigor)
12. **Validação da regra** — a tabela dos 6 exemplos de trabalho conferidos
13. **Resultado do filtro** — elegíveis vs. excluídos por motivo; o antes/depois de um prompt
14. **Arquitetura de dois prompts** — Camada 1 (identidade) + Camada 2 (comportamento), e o mapeamento Rule Sets ↔ Angenot
15. **Decisões de design da Camada 2** — remoção dos frames por tema; manutenção do guardrail identitário (com as razões)
16. **O que já está produzido** — lista de entregáveis
17. **Próximos passos** — rodada de teste inicial (smoke test: 1 tema, 1 par, poucos turnos) → rodada piloto → execução completa; desenho experimental com a tabela de papéis A/B/C
18. **Execução resiliente** — o requisito de persistência e retomada (Seção 8.3 da fonte): progresso gravado incrementalmente, retomada no nível do turno, idempotência. Justifique pelo volume (~1.080 chamadas de API no total)
19. **Métricas** — as candidatas atuais, **deixando explícito que o conjunto final ainda não está definido** e que as métricas são independentes entre si por construção (remover uma não afeta as outras)
20. **Divergências resolvidas** — as 3 divergências entre o plano de monografia e a implementação, com a decisão tomada em cada uma (Seção 9.1 da fonte). Mencione que o plano foi atualizado para a v6
21. **Pontos em aberto** — os 3 itens da Seção 9.2 da fonte. **Este é o slide mais importante da reunião**
22. **Limitações mapeadas** — tabela resumida

Você pode fundir ou desdobrar slides se melhorar a clareza, mas mantenha a
cobertura completa e preserve o slide de pontos de alinhamento.

## Diretrizes de conteúdo

- **Densidade:** slides de reunião de acompanhamento, não de congresso. Podem
  ter mais texto que um slide de palestra, mas nunca parágrafos corridos —
  use bullets, tabelas e blocos de código curtos.
- **Sempre que houver número, mostre o número.** 200.000 → 2.000 → 399 →
  101/20 → 10+10; scores −6,0; 72% de `Achievement`; 19,95% de cobertura de
  `political_lean`. Os números são o argumento.
- **Sempre que houver decisão, mostre a motivação junto.** Nenhuma escolha
  deve aparecer sem o porquê ao lado.
- **Use os exemplos concretos de persona** (Q55759875, Q50318212, Q56224097)
  — eles tornam o problema tangível muito mais rápido que uma descrição
  abstrata.
- **Preserve as referências bibliográficas** nos slides de fundamentação
  (Angenot 2006/2008/2010; Bobbio 1994; Jost et al. 2003; Piurko et al. 2011;
  Feldman & Johnston 2014).
- Nos slides de "antes e depois" de prompt, mostre os dois lado a lado — o
  contraste é autoexplicativo.
- **No slide de métricas, não as apresente como fechadas.** Elas são
  candidatas; o conjunto final será decidido após o piloto. Deixe visível o
  princípio de independência entre elas — é uma decisão de arquitetura
  deliberada (dados brutos persistidos de forma neutra, cada métrica derivada
  em passo separado), não uma indefinição por descuido.

## Formato de saída

Publique como um **Artifact** (página HTML de slides), com:
- Navegação por teclado (setas ou espaço) entre slides
- Um slide por tela, legível a distância em projetor
- Indicador de progresso (ex.: "12 / 19")
- Tipografia sóbria e alto contraste; funcionar bem em tema claro e escuro
- Tabelas legíveis; blocos de código em monoespaçada com destaque discreto

Antes de escrever o HTML, carregue a skill `artifact-design` para calibrar o
nível de investimento em design.

Ao final, entregue o link do Artifact e um resumo de 3 linhas do que a
apresentação cobre.
```

---

## Notas de uso

- O conteúdo-fonte (`estado_atual_do_trabalho.md`) é a fonte de verdade. Se o
  trabalho avançar, atualize-o **antes** de regerar os slides.
- A Seção 9.1 da fonte registra três divergências entre o plano de monografia
  e a implementação que **já foram decididas**: prevalece a implementação
  (ordenação por score de coerência), a contextualização brasileira não será
  implementada nesta etapa, e a composição da amostra fica fora de escopo. O
  plano foi atualizado para `Plano_Monografia_CSCW_v6.docx` refletindo essas
  decisões — a v5 permanece no repositório como histórico.
- A Seção 9.2 lista o que continua em aberto (desequilíbrio entre polos,
  escolha dos modelos A/B/C, conjunto final de métricas). Esses pontos existem
  para serem discutidos na reunião, não para serem suavizados.
