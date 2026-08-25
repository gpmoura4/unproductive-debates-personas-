# Fase 2 — Relatório de Decodificação de Atributos

## 1. Metodologia

- Amostra decodificada: 2,000 personas de 200,000 disponíveis nos shards baixados (amostragem com seed fixa = 42, reprodutível entre execuções).
- Dimensões decodificadas: lista curada manualmente de 10 dimensões que efetivamente norteiam a categorização de viés político (não o resultado bruto de term-match da Fase 0, que identificou 155 candidatas — 145 delas descartadas por não serem diretamente relevantes ao eixo esquerda/direita).
- Convenção de decode validada empiricamente — ver `outputs/phase2_decode_validation.md`.

### Dimensões curadas para esta fase

`political_lean`, `religiosity`, `trust_level`, `values_priority`, `att_free_markets`, `att_government_regulation`, `att_labor_unions`, `att_immigration`, `att_gun_ownership`, `att_capital_punishment`

### Distribuição por `source` nos 2 shards baixados

| source | contagem |
|---|---|
| wiki | 200,000 |

**Aviso de representatividade**: os 2 primeiros shards contêm exclusivamente personas da fonte `wiki`. Isso pode não ser representativo da mistura completa do coreset (que inclui registros human-grounded via GSS/Latinobarometro, conforme a documentação do dataset). Os percentuais de cobertura e distribuições abaixo refletem apenas esta fonte — expandir para mais shards antes de tirar conclusões definitivas sobre a Fase 2.

## 2. Cobertura por dimensão

| dimensão | não-nulos | cobertura % |
|---|---|---|
| political_lean | 399 | 19.95% |
| religiosity | 823 | 41.15% |
| trust_level | 141 | 7.05% |
| values_priority | 1778 | 88.9% |
| att_free_markets | 218 | 10.9% |
| att_government_regulation | 230 | 11.5% |
| att_labor_unions | 193 | 9.65% |
| att_immigration | 127 | 6.35% |
| att_gun_ownership | 185 | 9.25% |
| att_capital_punishment | 169 | 8.45% |

## 3. Distribuições — dimensões curadas

### political_lean

| valor | contagem |
|---|---|
| Center-right | 112 |
| Center-left | 101 |
| Right | 70 |
| Left | 68 |
| Center | 46 |
| Apolitical | 2 |

### religiosity

| valor | contagem |
|---|---|
| Secular | 604 |
| Observant | 101 |
| Devout | 91 |
| Prefer not to say | 18 |
| Spiritual | 9 |

### trust_level

| valor | contagem |
|---|---|
| Verifying | 68 |
| Skeptical | 40 |
| Trusting | 31 |
| Hostile | 2 |

### values_priority

| valor | contagem |
|---|---|
| Achievement | 1436 |
| Community | 160 |
| Novelty | 71 |
| Tradition | 67 |
| Security | 31 |
| Autonomy | 13 |

### att_free_markets

| valor | contagem |
|---|---|
| Neutral | 97 |
| Positive | 75 |
| Enthusiast | 37 |
| Skeptical | 7 |
| Opposed | 2 |

### att_government_regulation

| valor | contagem |
|---|---|
| Neutral | 88 |
| Positive | 70 |
| Skeptical | 44 |
| Enthusiast | 27 |
| Opposed | 1 |

### att_labor_unions

| valor | contagem |
|---|---|
| Neutral | 103 |
| Positive | 40 |
| Enthusiast | 38 |
| Skeptical | 12 |

### att_immigration

| valor | contagem |
|---|---|
| Neutral | 50 |
| Enthusiast | 48 |
| Positive | 26 |
| Skeptical | 3 |

### att_gun_ownership

| valor | contagem |
|---|---|
| Neutral | 116 |
| Enthusiast | 38 |
| Positive | 28 |
| Skeptical | 3 |

### att_capital_punishment

| valor | contagem |
|---|---|
| Neutral | 118 |
| Enthusiast | 32 |
| Skeptical | 15 |
| Positive | 4 |

## 4. Perfis contrastantes (political_lean)

- Polo esquerda (Left/Center-left): 169 personas na amostra

- Polo direita (Right/Center-right): 182 personas na amostra

### Exemplos — polo esquerda

```json
[
  {
    "source": "wiki",
    "source_row_index": 714660,
    "source_record_id": "Q2142140",
    "political_attributes": {
      "political_lean": "Left",
      "religiosity": "Observant",
      "trust_level": null,
      "values_priority": "Achievement",
      "att_free_markets": null,
      "att_government_regulation": null,
      "att_labor_unions": null,
      "att_immigration": null,
      "att_gun_ownership": null,
      "att_capital_punishment": null
    }
  },
  {
    "source": "wiki",
    "source_row_index": 344385,
    "source_record_id": "Q6290862",
    "political_attributes": {
      "political_lean": "Center-left",
      "religiosity": "Secular",
      "trust_level": null,
      "values_priority": "Autonomy",
      "att_free_markets": null,
      "att_government_regulation": null,
      "att_labor_unions": "Positive",
      "att_immigration": null,
      "att_gun_ownership": null,
      "att_capital_punishment": null
    }
  },
  {
    "source": "wiki",
    "source_row_index": 559464,
    "source_record_id": "Q3104406",
    "political_attributes": {
      "political_lean": "Left",
      "religiosity": "Secular",
      "trust_level": null,
      "values_priority": "Community",
      "att_free_markets": null,
      "att_government_regulation": null,
      "att_labor_unions": "Positive",
      "att_immigration": null,
      "att_gun_ownership": null,
      "att_capital_punishment": null
    }
  }
]
```

### Exemplos — polo direita

```json
[
  {
    "source": "wiki",
    "source_row_index": 245739,
    "source_record_id": "Q4079391",
    "political_attributes": {
      "political_lean": "Right",
      "religiosity": "Observant",
      "trust_level": "Verifying",
      "values_priority": "Security",
      "att_free_markets": null,
      "att_government_regulation": null,
      "att_labor_unions": null,
      "att_immigration": "Neutral",
      "att_gun_ownership": null,
      "att_capital_punishment": null
    }
  },
  {
    "source": "wiki",
    "source_row_index": 1164239,
    "source_record_id": "Q50318212",
    "political_attributes": {
      "political_lean": "Right",
      "religiosity": "Observant",
      "trust_level": "Trusting",
      "values_priority": "Achievement",
      "att_free_markets": "Enthusiast",
      "att_government_regulation": "Enthusiast",
      "att_labor_unions": "Enthusiast",
      "att_immigration": null,
      "att_gun_ownership": "Enthusiast",
      "att_capital_punishment": "Enthusiast"
    }
  },
  {
    "source": "wiki",
    "source_row_index": 158382,
    "source_record_id": "Q5361378",
    "political_attributes": {
      "political_lean": "Center-right",
      "religiosity": null,
      "trust_level": null,
      "values_priority": "Achievement",
      "att_free_markets": null,
      "att_government_regulation": null,
      "att_labor_unions": null,
      "att_immigration": null,
      "att_gun_ownership": null,
      "att_capital_punishment": null
    }
  }
]
```

## 5. Conclusão e próximos passos

A decodificação do vetor binário `attributes` foi validada contra o texto livre gerado para as mesmas personas (`descriptions`) e está pronta para uso na seleção de personas de debate. Próximos passos sugeridos:
1. Expandir a decodificação para o coreset completo (1M personas, 11 shards) fora desta fase exploratória.
2. Cruzar `political_lean` com `religiosity` e `values_priority` para construir personas mais ricas e internamente consistentes para os dois polos do debate.
3. Usar os eixos `att_free_markets`, `att_government_regulation`, `att_labor_unions`, `att_immigration`, `att_gun_ownership` e `att_capital_punishment` como sinais econômicos/sociais secundários de contraste, junto com `trust_level` como eixo de confiança institucional.
