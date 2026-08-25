# Fase 1 — Relatório de Exploração do Dataset Parquet

## 1. Schema real do Parquet

- Registros nos 2 shards: 200,000
- Total de colunas: 12

| Coluna | Tipo |
|---|---|
| source | VARCHAR |
| source_row_index | UBIGINT |
| source_record_id | VARCHAR |
| attributes | BLOB |
| null_bitmap | BLOB |
| attribute_overrides | STRUCT(field_index USMALLINT, "value" VARCHAR)[] |
| has_description | BOOLEAN |
| descriptions | STRUCT(field_index USMALLINT, "text" VARCHAR)[] |
| grounding | STRUCT(field_index USMALLINT, evidence VARCHAR, confidence FLOAT, assignment_type VARCHAR)[] |
| metadata_json | VARCHAR |
| populated_attribute_count | USMALLINT |
| description_count | USMALLINT |

## 2. Colunas politicamente relevantes

Nenhuma coluna com nome diretamente reconhecível como política foi encontrada.

O schema parece usar vetor(es) binário(s) compactado(s): attributes, null_bitmap. A decodificação requer o arquivo `persona_codes.schema.json` (ver seção 7).


## 3. Distribuições de valores

_Sem colunas categóricas diretas para tabular distribuições._

## 4. Exemplos de perfis — Polo A (progressista/esquerda)

```json
[]
```

## 5. Exemplos de perfis — Polo B (conservador/direita)

```json
[]
```

## 6. Cobertura

- Registros com atributos políticos não-nulos: 0 / 200,000 (0.0%)

## 7. Conclusão e próximos passos

Abordagem usada para identificar perfis contrastantes: **C**

O dataset usa vetor binário compactado (645 bytes / 1.290 atributos x 4 bits). Para decodificar, é necessário:
1. Usar persona_codes.schema.json para mapear índice -> valores categóricos
2. Implementar desempacotamento nibble-by-nibble
3. Script de decodificação será implementado na Fase 2 deste projeto
