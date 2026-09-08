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

## 4. Perfis contrastantes (regra de coerência esquerda/direita)

Classificação conforme `docs/left right categories/regras_categorizacao_esquerda_direita.json` (âncora `political_lean` + coerência multi-indicador nos eixos econômico/nuclear e social/periférico; ver `docs/left right categories/regras_categorizacao_esquerda_direita.md` para a fundamentação teórica completa). Substitui a regra anterior baseada apenas em `political_lean`.

- Polo esquerda: 101 personas elegíveis na amostra (modo `strict`)

- Polo direita: 20 personas elegíveis na amostra (modo `strict`)

### Exclusões (registros com âncora no polo, mas rejeitados pela regra de coerência)

| polo | total excluído | motivos |
|---|---|---|
| Esquerda | 68 | contradicao_nuclear=32, sem_evidencia_secundaria=28, tolerancia_periferica_violada=8 |
| Direita | 162 | contradicao_nuclear=40, sem_evidencia_secundaria=87, tolerancia_periferica_violada=35 |

### Exemplos — polo esquerda (top 3 por coerência)

```json
[
  {
    "source": "wiki",
    "source_row_index": 1202331,
    "source_record_id": "Q56224097",
    "political_attributes": {
      "political_lean": "Left",
      "religiosity": "Secular",
      "trust_level": "Verifying",
      "values_priority": "Community",
      "att_free_markets": "Neutral",
      "att_government_regulation": "Positive",
      "att_labor_unions": "Positive",
      "att_immigration": "Positive",
      "att_gun_ownership": "Neutral",
      "att_capital_punishment": "Skeptical"
    },
    "coherence": {
      "n_core_concord": 2,
      "n_core_contra": 0,
      "n_per_concord": 4,
      "n_per_contra": 0,
      "score": -6.0,
      "non_null_field_count": 10,
      "anchor_sign": -1
    }
  },
  {
    "source": "wiki",
    "source_row_index": 1202243,
    "source_record_id": "Q12407556",
    "political_attributes": {
      "political_lean": "Center-left",
      "religiosity": "Secular",
      "trust_level": "Verifying",
      "values_priority": "Achievement",
      "att_free_markets": "Skeptical",
      "att_government_regulation": "Positive",
      "att_labor_unions": "Positive",
      "att_immigration": "Positive",
      "att_gun_ownership": "Neutral",
      "att_capital_punishment": "Neutral"
    },
    "coherence": {
      "n_core_concord": 3,
      "n_core_contra": 0,
      "n_per_concord": 2,
      "n_per_contra": 0,
      "score": -5.0,
      "non_null_field_count": 10,
      "anchor_sign": -1
    }
  },
  {
    "source": "wiki",
    "source_row_index": 1116626,
    "source_record_id": "Q13116977",
    "political_attributes": {
      "political_lean": "Left",
      "religiosity": "Secular",
      "trust_level": null,
      "values_priority": "Community",
      "att_free_markets": "Opposed",
      "att_government_regulation": "Positive",
      "att_labor_unions": "Enthusiast",
      "att_immigration": null,
      "att_gun_ownership": null,
      "att_capital_punishment": null
    },
    "coherence": {
      "n_core_concord": 3,
      "n_core_contra": 0,
      "n_per_concord": 2,
      "n_per_contra": 0,
      "score": -5.0,
      "non_null_field_count": 6,
      "anchor_sign": -1
    }
  }
]
```

### Exemplos — polo direita (top 3 por coerência)

```json
[
  {
    "source": "wiki",
    "source_row_index": 213902,
    "source_record_id": "Q888061",
    "political_attributes": {
      "political_lean": "Right",
      "religiosity": "Observant",
      "trust_level": "Verifying",
      "values_priority": "Achievement",
      "att_free_markets": "Positive",
      "att_government_regulation": "Skeptical",
      "att_labor_unions": "Skeptical",
      "att_immigration": null,
      "att_gun_ownership": "Positive",
      "att_capital_punishment": "Neutral"
    },
    "coherence": {
      "n_core_concord": 3,
      "n_core_contra": 0,
      "n_per_concord": 2,
      "n_per_contra": 0,
      "score": 5.0,
      "non_null_field_count": 9,
      "anchor_sign": 1
    }
  },
  {
    "source": "wiki",
    "source_row_index": 283558,
    "source_record_id": "Q7693479",
    "political_attributes": {
      "political_lean": "Center-right",
      "religiosity": "Observant",
      "trust_level": null,
      "values_priority": "Achievement",
      "att_free_markets": "Positive",
      "att_government_regulation": "Skeptical",
      "att_labor_unions": "Skeptical",
      "att_immigration": null,
      "att_gun_ownership": null,
      "att_capital_punishment": null
    },
    "coherence": {
      "n_core_concord": 3,
      "n_core_contra": 0,
      "n_per_concord": 1,
      "n_per_contra": 0,
      "score": 4.0,
      "non_null_field_count": 6,
      "anchor_sign": 1
    }
  },
  {
    "source": "wiki",
    "source_row_index": 610937,
    "source_record_id": "Q2487377",
    "political_attributes": {
      "political_lean": "Right",
      "religiosity": "Devout",
      "trust_level": "Skeptical",
      "values_priority": "Tradition",
      "att_free_markets": "Neutral",
      "att_government_regulation": "Skeptical",
      "att_labor_unions": "Neutral",
      "att_immigration": "Neutral",
      "att_gun_ownership": "Positive",
      "att_capital_punishment": "Neutral"
    },
    "coherence": {
      "n_core_concord": 1,
      "n_core_contra": 0,
      "n_per_concord": 3,
      "n_per_contra": 0,
      "score": 4.0,
      "non_null_field_count": 10,
      "anchor_sign": 1
    }
  }
]
```

## 5. Conclusão e próximos passos

A decodificação do vetor binário `attributes` foi validada contra o texto livre gerado para as mesmas personas (`descriptions`) e está pronta para uso na seleção de personas de debate. Próximos passos sugeridos:
1. Expandir a decodificação para o coreset completo (1M personas, 11 shards) fora desta fase exploratória.
2. Cruzar `political_lean` com `religiosity` e `values_priority` para construir personas mais ricas e internamente consistentes para os dois polos do debate.
3. Usar os eixos `att_free_markets`, `att_government_regulation`, `att_labor_unions`, `att_immigration`, `att_gun_ownership` e `att_capital_punishment` como sinais econômicos/sociais secundários de contraste, junto com `trust_level` como eixo de confiança institucional.
