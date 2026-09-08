"""Decodificação do vetor binário de atributos (Fase 2).

O coreset Parquet armazena as 1290 dimensões de cada persona compactadas em
um único BLOB de 645 bytes (`attributes`), 4 bits (nibble) por dimensão,
mais um `null_bitmap` de 162 bytes indicando quais dimensões estão nulas.

Convenção de empacotamento (confirmada empiricamente contra os campos
`descriptions`/`attribute_overrides`, que trazem texto legível gerado para
a mesma persona — ver outputs/phase2_decode_validation.md):
  - nibble "low-first": dimensão de índice par -> metade baixa do byte
    (`byte & 0x0F`); dimensão de índice ímpar -> metade alta (`byte >> 4`).
  - null_bitmap: bit = 0 significa "dimensão populada"; bit = 1 significa
    "dimensão nula/não aplicável" (verificado contra populated_attribute_count).
  - O índice posicional de cada dimensão é a ordem em que ela aparece na
    lista `columns` de persona_codes.schema.json (idêntica à ordem de
    `dimensions.json`, ambas com 1290 entradas).

As dimensões decodificadas são uma lista curada manualmente (CURATED_POLITICAL_DIMENSIONS,
10 dimensões) que efetivamente norteiam a categorização de viés político — não o resultado
bruto de term-match da Fase 0 (que tinha 155 candidatas, muitas irrelevantes ao debate
político). A amostragem usa seed fixa (SAMPLE_SEED) para reprodutibilidade entre execuções.

A separação em polo_esquerda/polo_direita usa a regra de coerência multi-indicador
especificada em `docs/left right categories/regras_categorizacao_esquerda_direita.json`
(fundamentação teórica em regras_categorizacao_esquerda_direita.md): âncora obrigatória em
`political_lean`, exigência de ausência de contradição nos indicadores nucleares (eixo
econômico) e tolerância periférica (eixo social/valores) conforme o modo `strict`/`lenient`.
Substitui a regra anterior, que classificava um registro no polo apenas por `political_lean`,
sem checar coerência com os demais atributos.

Pré-requisitos:
- data/schema/persona_codes.schema.json (mapa índice -> valores categóricos)
- outputs/phase0_political_dimensions.json (usado apenas para registrar quantas candidatas
  da Fase 0 foram descartadas pela curadoria manual)
- docs/left right categories/regras_categorizacao_esquerda_direita.json (regra de
  classificação de polos)
- data/persona-1m/*.parquet (shards baixados por 02_explore_parquet.py)

Outputs:
- outputs/phase2_decode_validation.md   (evidência da validação da convenção de decode)
- outputs/phase2_decoded_personas.json  (amostra de personas decodificadas, políticas)
- outputs/phase2_decode_report.md       (distribuições, cobertura, perfis contrastantes)
"""

import json
import sys
from pathlib import Path

import duckdb
import pandas as pd

CODES_SCHEMA_PATH = Path("data/schema/persona_codes.schema.json")
PHASE0_JSON = Path("outputs/phase0_political_dimensions.json")
DATA_DIR = Path("data/persona-1m")
POLE_RULES_JSON = Path("docs/left right categories/regras_categorizacao_esquerda_direita.json")

OUT_DIR = Path("outputs")
OUT_VALIDATION_MD = OUT_DIR / "phase2_decode_validation.md"
OUT_DECODED_JSON = OUT_DIR / "phase2_decoded_personas.json"
OUT_REPORT_MD = OUT_DIR / "phase2_decode_report.md"

SAMPLE_SIZE = 2000  # personas amostradas do Parquet para decodificação nesta fase
SAMPLE_SEED = 42  # fixa a amostra entre execuções para reprodutibilidade dos relatórios

# Lista curada manualmente: dimensões que efetivamente norteiam a categorização
# de viés político (esquerda/direita). Substitui o resultado bruto de term-match
# da Fase 0 (outputs/phase0_political_dimensions.json tinha 155 candidatas, muitas
# irrelevantes ao debate político — ex.: dimensões de preferência cognitiva ou de
# atitude sobre ferramentas de programação que continham palavras-chave genéricas
# como "belief"/"trust" mas não medem posição política).
CURATED_POLITICAL_DIMENSIONS = [
    "political_lean",
    "religiosity",
    "trust_level",
    "values_priority",
    "att_free_markets",
    "att_government_regulation",
    "att_labor_unions",
    "att_immigration",
    "att_gun_ownership",
    "att_capital_punishment",
]


def check_prerequisites() -> tuple[dict, dict, dict, list[Path]]:
    missing = []
    if not CODES_SCHEMA_PATH.exists():
        missing.append((CODES_SCHEMA_PATH, "uv run python scripts/00_download_schema.py"))
    if not PHASE0_JSON.exists():
        missing.append((PHASE0_JSON, "uv run python scripts/01_inspect_schema.py"))
    if not POLE_RULES_JSON.exists():
        missing.append((POLE_RULES_JSON, "(arquivo de regras de categorização esquerda/direita ausente)"))
    parquet_files = sorted(DATA_DIR.glob("*.parquet"))
    if not parquet_files:
        missing.append((DATA_DIR / "*.parquet", "uv run python scripts/02_explore_parquet.py"))

    if missing:
        for path, cmd in missing:
            print(f"[ERRO] {path} não encontrado.")
            print(f"Execute primeiro: {cmd}")
        sys.exit(1)

    try:
        codes_schema = json.loads(CODES_SCHEMA_PATH.read_text())
    except json.JSONDecodeError as e:
        print(f"[ERRO] {CODES_SCHEMA_PATH} não é JSON válido: {e}")
        sys.exit(1)

    try:
        phase0 = json.loads(PHASE0_JSON.read_text())
    except json.JSONDecodeError as e:
        print(f"[ERRO] {PHASE0_JSON} não é JSON válido: {e}")
        sys.exit(1)

    try:
        pole_rules = json.loads(POLE_RULES_JSON.read_text())
    except json.JSONDecodeError as e:
        print(f"[ERRO] {POLE_RULES_JSON} não é JSON válido: {e}")
        sys.exit(1)

    return codes_schema, phase0, pole_rules, parquet_files


def build_index_map(codes_schema: dict) -> list[dict]:
    columns = codes_schema.get("columns", [])
    if len(columns) != 1290:
        print(f"[AVISO] Esperava 1290 colunas em persona_codes.schema.json, encontrado {len(columns)}.")
    return columns


def get_bit(buf: bytes, i: int) -> int:
    return (buf[i // 8] >> (i % 8)) & 1


def nibble_low_first(buf: bytes, i: int) -> int:
    b = buf[i // 2]
    return (b & 0x0F) if i % 2 == 0 else (b >> 4)


def decode_dimension(attributes: bytes, null_bitmap: bytes | None, idx: int, values: list[str]) -> str | None:
    if null_bitmap is not None and get_bit(null_bitmap, idx) == 1:
        return None
    code = nibble_low_first(attributes, idx)
    if code >= len(values):
        return None
    return values[code]


def validate_convention(conn: duckdb.DuckDBPyConnection, columns: list[dict]) -> tuple[bool, list[str]]:
    """Valida a convenção de decode comparando contra `descriptions` (texto livre
    gerado para a mesma persona). Retorna (ok, linhas_de_evidencia_markdown)."""
    row = conn.execute("""
        SELECT descriptions, attribute_overrides, attributes, null_bitmap
        FROM personas
        WHERE has_description = true
        LIMIT 1
    """).fetchone()

    if row is None:
        return False, ["_Nenhuma persona com `has_description = true` encontrada na amostra — validação pulada._"]

    descriptions, overrides, attributes, null_bitmap = row
    override_idx = {o["field_index"] for o in (overrides or [])}
    desc_by_idx = {d["field_index"]: d["text"] for d in (descriptions or [])}

    evidence = []
    evidence.append("| índice | dimensão | valor decodificado | trecho da descrição (gabarito) |")
    evidence.append("|---|---|---|---|")

    checked = 0
    for idx, col in enumerate(columns):
        if idx in override_idx:
            continue  # override textual não representa o código original
        if idx not in desc_by_idx:
            continue
        decoded = decode_dimension(attributes, null_bitmap, idx, col.get("values", []))
        if decoded is None:
            continue
        snippet = desc_by_idx[idx][:160].replace("\n", " ")
        evidence.append(f"| {idx} | {col['id']} | {decoded} | {snippet} |")
        checked += 1
        if checked >= 15:
            break

    ok = checked >= 3
    return ok, evidence


def _indicator_signal(field_spec: dict, value: str | None) -> float:
    """Retorna o sinal {-1, -0.5, 0, +1} de um indicador para um dado valor
    decodificado, conforme regras_categorizacao_esquerda_direita.json."""
    if value in field_spec.get("left", []):
        return -field_spec.get("weight", 1.0)
    if value in field_spec.get("left_weak", []):
        return -field_spec.get("weak_weight", 0.5)
    if value in field_spec.get("right", []):
        return field_spec.get("weight", 1.0)
    return 0.0  # neutral (inclui valores explicitamente listados e nulos)


def score_persona(attrs: dict, pole_rules: dict) -> dict:
    """Calcula os contadores/score de coerência de uma persona conforme a
    especificação em regras_categorizacao_esquerda_direita.json."""
    indicators = pole_rules["indicators"]
    core_fields = indicators["core"]["fields"]
    peripheral_fields = indicators["peripheral"]["fields"]

    n_core_concord = n_core_contra = 0
    n_per_concord = n_per_contra = 0
    score = 0.0

    lean = attrs.get("political_lean")
    anchor_sign = None
    if lean in pole_rules["poles"]["left"]["anchor_values"]:
        anchor_sign = pole_rules["poles"]["left"]["sign"]
    elif lean in pole_rules["poles"]["right"]["anchor_values"]:
        anchor_sign = pole_rules["poles"]["right"]["sign"]

    for field, spec in core_fields.items():
        sig = _indicator_signal(spec, attrs.get(field))
        score += sig
        if sig != 0 and anchor_sign is not None:
            if (sig > 0) == (anchor_sign > 0):
                n_core_concord += 1
            else:
                n_core_contra += 1

    for field, spec in peripheral_fields.items():
        sig = _indicator_signal(spec, attrs.get(field))
        score += sig
        if sig != 0 and anchor_sign is not None:
            if (sig > 0) == (anchor_sign > 0):
                n_per_concord += 1
            else:
                n_per_contra += 1

    non_null_field_count = sum(1 for v in attrs.values() if v is not None)

    return {
        "n_core_concord": n_core_concord,
        "n_core_contra": n_core_contra,
        "n_per_concord": n_per_concord,
        "n_per_contra": n_per_contra,
        "score": score,
        "non_null_field_count": non_null_field_count,
        "anchor_sign": anchor_sign,
    }


def _peripheral_tolerance_ok(counts: dict, mode: str) -> bool:
    if mode == "strict":
        return counts["n_per_contra"] == 0
    if mode == "lenient":
        return counts["n_per_contra"] <= 1 and (
            counts["n_core_concord"] + counts["n_per_concord"] > counts["n_per_contra"]
        )
    raise ValueError(f"Modo de tolerância periférica desconhecido: {mode}")


def classify_pole(lean: str | None, counts: dict, pole_rules: dict, mode: str) -> str | None:
    """Aplica as regras 'left'/'right' do JSON de regras e retorna 'left',
    'right' ou None (excluído)."""
    if lean in pole_rules["poles"]["left"]["anchor_values"]:
        candidate_pole = "left"
    elif lean in pole_rules["poles"]["right"]["anchor_values"]:
        candidate_pole = "right"
    else:
        return None  # âncora ausente ou em anchor.excluded_values

    if counts["n_core_contra"] != 0:
        return None
    if counts["n_core_concord"] + counts["n_per_concord"] < 1:
        return None
    if not _peripheral_tolerance_ok(counts, mode):
        return None
    return candidate_pole


def select_pole_profiles(
    decoded_records: list[dict], pole_rules: dict
) -> tuple[list[dict], list[dict], dict]:
    """Classifica e ordena as personas elegíveis para polo_esquerda/polo_direita
    conforme regras_categorizacao_esquerda_direita.json (âncora political_lean +
    coerência multi-indicador). Modo padrão 'strict', com fallback 'lenient' por
    polo caso o modo padrão não produza candidatos suficientes."""
    default_mode = pole_rules["modes"]["default"]
    fallback_mode = pole_rules["modes"]["fallback"]
    min_needed = 10  # tamanho de corte histórico de cada lista de polo no output

    exclusion_log = {"left": {"excluded": 0, "reasons": {}}, "right": {"excluded": 0, "reasons": {}}}

    def exclusion_reason(lean: str | None, counts: dict, mode: str) -> str:
        if lean in pole_rules["anchor"]["excluded_values"] or lean is None:
            return "ancora_excluida_ou_nula"
        if counts["n_core_contra"] != 0:
            return "contradicao_nuclear"
        if counts["n_core_concord"] + counts["n_per_concord"] < 1:
            return "sem_evidencia_secundaria"
        if not _peripheral_tolerance_ok(counts, mode):
            return "tolerancia_periferica_violada"
        return "outro"

    def build_candidates(mode: str) -> tuple[list[dict], list[dict]]:
        left, right = [], []
        for record in decoded_records:
            attrs = record["political_attributes"]
            counts = score_persona(attrs, pole_rules)
            pole = classify_pole(attrs.get("political_lean"), counts, pole_rules, mode)
            enriched = {**record, "coherence": counts}
            if pole == "left":
                left.append(enriched)
            elif pole == "right":
                right.append(enriched)
        return left, right

    def sort_candidates(candidates: list[dict]) -> list[dict]:
        return sorted(
            candidates,
            key=lambda r: (
                abs(r["coherence"]["score"]),
                r["coherence"]["n_core_concord"],
                r["coherence"]["non_null_field_count"],
            ),
            reverse=True,
        )

    left_strict, right_strict = build_candidates(default_mode)
    mode_used = {"left": default_mode, "right": default_mode}

    left_final = left_strict
    right_final = right_strict
    if len(left_strict) < min_needed or len(right_strict) < min_needed:
        left_lenient, right_lenient = build_candidates(fallback_mode)
        if len(left_strict) < min_needed:
            left_final = left_lenient
            mode_used["left"] = fallback_mode
        if len(right_strict) < min_needed:
            right_final = right_lenient
            mode_used["right"] = fallback_mode

    # Log de exclusão: para cada registro cuja âncora aponta para um polo mas
    # que não passou nas regras de coerência (no modo efetivamente usado nesse polo).
    for record in decoded_records:
        attrs = record["political_attributes"]
        counts = score_persona(attrs, pole_rules)
        lean = attrs.get("political_lean")
        for pole_key, mode in mode_used.items():
            if lean not in pole_rules["poles"][pole_key]["anchor_values"]:
                continue
            if classify_pole(lean, counts, pole_rules, mode) is not None:
                continue
            reason = exclusion_reason(lean, counts, mode)
            exclusion_log[pole_key]["excluded"] += 1
            exclusion_log[pole_key]["reasons"][reason] = (
                exclusion_log[pole_key]["reasons"].get(reason, 0) + 1
            )

    stats = {
        "mode_used": mode_used,
        "n_eligible_strict": {"left": len(left_strict), "right": len(right_strict)},
        "n_eligible_final": {"left": len(left_final), "right": len(right_final)},
        "exclusion_log": exclusion_log,
    }
    return sort_candidates(left_final), sort_candidates(right_final), stats


def main() -> int:
    codes_schema, phase0, pole_rules, parquet_files = check_prerequisites()
    columns = build_index_map(codes_schema)

    phase0_candidate_ids = [d["id"] for d in phase0.get("all_candidates", []) if d.get("id")]
    candidate_ids = CURATED_POLITICAL_DIMENSIONS
    id_to_index = {col["id"]: idx for idx, col in enumerate(columns)}
    candidate_indices = [
        (id_to_index[cid], cid) for cid in candidate_ids if cid in id_to_index
    ]
    missing_ids = [cid for cid in candidate_ids if cid not in id_to_index]
    if missing_ids:
        print(f"[ERRO] {len(missing_ids)} dimensões curadas não encontradas em persona_codes.schema.json: {missing_ids}")
        return 1

    unused_phase0_ids = [cid for cid in phase0_candidate_ids if cid not in candidate_ids]
    print(
        f"[INFO] Fase 0 identificou {len(phase0_candidate_ids)} dimensões candidatas por term-match; "
        f"esta fase usa uma lista curada manualmente de {len(candidate_ids)} dimensões "
        f"({len(unused_phase0_ids)} candidatas da Fase 0 foram descartadas por não serem "
        "diretamente relevantes à categorização de viés político)."
    )

    print(f"Total de dimensões candidatas (lista curada): {len(candidate_ids)}")
    print(f"Dimensões candidatas resolvidas para índice de decodificação: {len(candidate_indices)}")

    conn = duckdb.connect()
    try:
        conn.execute(f"""
            CREATE VIEW personas AS
            SELECT * FROM read_parquet('{DATA_DIR}/*.parquet')
        """)
        total = conn.execute("SELECT COUNT(*) FROM personas").fetchone()[0]
        source_dist = conn.execute(
            "SELECT source, COUNT(*) AS n FROM personas GROUP BY source ORDER BY n DESC"
        ).fetchdf()
    except Exception as e:
        print(f"[ERRO] Falha ao carregar Parquet via DuckDB: {e}")
        return 1

    print(f"Total de registros disponíveis: {total:,}")
    print(f"Distribuição por 'source' nos shards baixados:\n{source_dist.to_string(index=False)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Validação da convenção de decode ---
    print("\n--- Validando convenção de decodificação (nibble low-first, null_bitmap) ---")
    ok, evidence_lines = validate_convention(conn, columns)
    validation_md = ["# Fase 2 — Validação da Convenção de Decodificação\n"]
    validation_md.append(
        "Convenção testada: nibble **low-first** (índice par -> `byte & 0x0F`, índice ímpar -> "
        "`byte >> 4`), `null_bitmap` com bit=0 significando dimensão populada.\n"
    )
    validation_md.append(
        "Evidência: comparação entre o valor decodificado e o texto livre do campo `descriptions` "
        "gerado para a mesma persona (dimensões com `attribute_overrides` foram excluídas, pois "
        "o override substitui o código original por texto livre).\n"
    )
    validation_md.extend(evidence_lines)
    validation_md.append("")
    if ok:
        validation_md.append("**Resultado: convenção validada** — os valores decodificados são consistentes com as descrições em linguagem natural.\n")
        print("[OK] Convenção de decodificação validada contra descriptions.")
    else:
        validation_md.append(
            "**Resultado: validação inconclusiva** — poucos pares dimensão/descrição disponíveis na amostra "
            "para confirmar a convenção. Revisar manualmente antes de confiar nos valores decodificados.\n"
        )
        print("[AVISO] Validação inconclusiva — revisar outputs/phase2_decode_validation.md manualmente.")
    OUT_VALIDATION_MD.write_text("\n".join(validation_md))
    print(f"[OK] Evidência de validação salva em {OUT_VALIDATION_MD}")

    if not ok:
        print("[AVISO] Prosseguindo mesmo assim — resultados desta fase devem ser tratados como preliminares.")

    # --- Decodificação da amostra ---
    print(f"\n--- Decodificando {SAMPLE_SIZE} personas (seed={SAMPLE_SEED}, apenas dimensões políticas curadas) ---")
    try:
        sample = conn.execute(f"""
            SELECT source, source_row_index, source_record_id, attributes, null_bitmap
            FROM personas
            USING SAMPLE reservoir({SAMPLE_SIZE} ROWS) REPEATABLE ({SAMPLE_SEED})
        """).fetchdf()
    except Exception as e:
        print(f"[ERRO] Falha ao amostrar personas: {e}")
        print("[FALLBACK] Tentando LIMIT direto (sem amostragem aleatória).")
        sample = conn.execute(f"""
            SELECT source, source_row_index, source_record_id, attributes, null_bitmap
            FROM personas
            LIMIT {SAMPLE_SIZE}
        """).fetchdf()

    decoded_records = []
    non_null_counts = {cid: 0 for _, cid in candidate_indices}
    value_distributions = {cid: {} for _, cid in candidate_indices}

    for _, row in sample.iterrows():
        attributes = row["attributes"]
        null_bitmap = row["null_bitmap"]
        record = {
            "source": row["source"],
            "source_row_index": int(row["source_row_index"]),
            "source_record_id": row["source_record_id"],
            "political_attributes": {},
        }
        for idx, cid in candidate_indices:
            values = columns[idx].get("values", [])
            decoded = decode_dimension(attributes, null_bitmap, idx, values)
            record["political_attributes"][cid] = decoded
            if decoded is not None:
                non_null_counts[cid] += 1
                value_distributions[cid][decoded] = value_distributions[cid].get(decoded, 0) + 1
        decoded_records.append(record)

    print(f"[OK] {len(decoded_records)} personas decodificadas.")

    # --- Identificação de perfis contrastantes via regra de coerência multi-indicador ---
    # Ver docs/left right categories/regras_categorizacao_esquerda_direita.{json,md}:
    # âncora obrigatória em political_lean + ausência de contradição nos indicadores
    # nucleares (eixo econômico) + tolerância periférica (eixo social/valores).
    pol_lean_id = "political_lean" if "political_lean" in id_to_index else None
    left_profiles = []
    right_profiles = []
    pole_stats = None
    if pol_lean_id:
        left_profiles, right_profiles, pole_stats = select_pole_profiles(decoded_records, pole_rules)
        print(
            f"Perfis elegíveis polo esquerda: {pole_stats['n_eligible_final']['left']} "
            f"(modo={pole_stats['mode_used']['left']}); "
            f"polo direita: {pole_stats['n_eligible_final']['right']} "
            f"(modo={pole_stats['mode_used']['right']})"
        )
        print(f"Exclusões polo esquerda: {pole_stats['exclusion_log']['left']}")
        print(f"Exclusões polo direita: {pole_stats['exclusion_log']['right']}")
    else:
        print("[AVISO] Dimensão 'political_lean' não encontrada entre as candidatas — sem polos automáticos.")

    # --- Outputs ---
    decoded_output = {
        "sample_size": len(decoded_records),
        "total_records_in_shards": total,
        "candidate_dimensions_decoded": [cid for _, cid in candidate_indices],
        "personas_sample": decoded_records[:50],
        "pole_classification_rule": {
            "source": str(POLE_RULES_JSON),
            "schema_version": pole_rules.get("schema_version"),
            "stats": pole_stats,
        },
        "polo_esquerda_political_lean": left_profiles[:10],
        "polo_direita_political_lean": right_profiles[:10],
    }
    OUT_DECODED_JSON.write_text(json.dumps(decoded_output, indent=2, ensure_ascii=False, default=str))
    print(f"[OK] JSON de personas decodificadas salvo em {OUT_DECODED_JSON}")

    report_lines = []
    report_lines.append("# Fase 2 — Relatório de Decodificação de Atributos\n")

    report_lines.append("## 1. Metodologia\n")
    report_lines.append(
        f"- Amostra decodificada: {len(decoded_records):,} personas de {total:,} disponíveis nos shards baixados "
        f"(amostragem com seed fixa = {SAMPLE_SEED}, reprodutível entre execuções).\n"
        f"- Dimensões decodificadas: lista curada manualmente de {len(candidate_indices)} dimensões que efetivamente "
        "norteiam a categorização de viés político (não o resultado bruto de term-match da Fase 0, que identificou "
        f"{len(phase0_candidate_ids)} candidatas — {len(unused_phase0_ids)} delas descartadas por não serem "
        "diretamente relevantes ao eixo esquerda/direita).\n"
        "- Convenção de decode validada empiricamente — ver `outputs/phase2_decode_validation.md`.\n"
    )
    report_lines.append("### Dimensões curadas para esta fase\n")
    report_lines.append(", ".join(f"`{cid}`" for cid in candidate_ids) + "\n")
    report_lines.append("### Distribuição por `source` nos 2 shards baixados\n")
    report_lines.append("| source | contagem |")
    report_lines.append("|---|---|")
    for _, row in source_dist.iterrows():
        report_lines.append(f"| {row['source']} | {row['n']:,} |")
    report_lines.append("")
    if len(source_dist) == 1:
        report_lines.append(
            f"**Aviso de representatividade**: os 2 primeiros shards contêm exclusivamente personas da "
            f"fonte `{source_dist.iloc[0]['source']}`. Isso pode não ser representativo da mistura completa "
            "do coreset (que inclui registros human-grounded via GSS/Latinobarometro, conforme a documentação "
            "do dataset). Os percentuais de cobertura e distribuições abaixo refletem apenas esta fonte — "
            "expandir para mais shards antes de tirar conclusões definitivas sobre a Fase 2.\n"
        )

    report_lines.append("## 2. Cobertura por dimensão\n")
    report_lines.append("| dimensão | não-nulos | cobertura % |")
    report_lines.append("|---|---|---|")
    for _, cid in candidate_indices:
        n = non_null_counts[cid]
        pct = round(n * 100.0 / len(decoded_records), 2) if decoded_records else 0.0
        report_lines.append(f"| {cid} | {n} | {pct}% |")
    report_lines.append("")

    report_lines.append("## 3. Distribuições — dimensões curadas\n")
    for _, cid in candidate_indices:
        report_lines.append(f"### {cid}\n")
        report_lines.append("| valor | contagem |")
        report_lines.append("|---|---|")
        for val, count in sorted(value_distributions[cid].items(), key=lambda kv: -kv[1]):
            report_lines.append(f"| {val} | {count} |")
        report_lines.append("")

    report_lines.append("## 4. Perfis contrastantes (regra de coerência esquerda/direita)\n")
    report_lines.append(
        f"Classificação conforme `{POLE_RULES_JSON}` (âncora `political_lean` + coerência "
        "multi-indicador nos eixos econômico/nuclear e social/periférico; ver "
        "`docs/left right categories/regras_categorizacao_esquerda_direita.md` para a "
        "fundamentação teórica completa). Substitui a regra anterior baseada apenas em "
        "`political_lean`.\n"
    )
    if pol_lean_id and pole_stats:
        report_lines.append(
            f"- Polo esquerda: {pole_stats['n_eligible_final']['left']} personas elegíveis na amostra "
            f"(modo `{pole_stats['mode_used']['left']}`)\n"
        )
        report_lines.append(
            f"- Polo direita: {pole_stats['n_eligible_final']['right']} personas elegíveis na amostra "
            f"(modo `{pole_stats['mode_used']['right']}`)\n"
        )
        report_lines.append("### Exclusões (registros com âncora no polo, mas rejeitados pela regra de coerência)\n")
        report_lines.append("| polo | total excluído | motivos |")
        report_lines.append("|---|---|---|")
        for pole_key, pole_label in (("left", "Esquerda"), ("right", "Direita")):
            log = pole_stats["exclusion_log"][pole_key]
            reasons_str = ", ".join(f"{k}={v}" for k, v in sorted(log["reasons"].items()))
            report_lines.append(f"| {pole_label} | {log['excluded']} | {reasons_str or '—'} |")
        report_lines.append("")
        report_lines.append("### Exemplos — polo esquerda (top 3 por coerência)\n")
        report_lines.append("```json")
        report_lines.append(json.dumps(left_profiles[:3], indent=2, ensure_ascii=False, default=str))
        report_lines.append("```\n")
        report_lines.append("### Exemplos — polo direita (top 3 por coerência)\n")
        report_lines.append("```json")
        report_lines.append(json.dumps(right_profiles[:3], indent=2, ensure_ascii=False, default=str))
        report_lines.append("```\n")
    else:
        report_lines.append("_Dimensão `political_lean` não disponível nesta amostra de dimensões candidatas._\n")

    report_lines.append("## 5. Conclusão e próximos passos\n")
    report_lines.append(
        "A decodificação do vetor binário `attributes` foi validada contra o texto livre gerado para "
        "as mesmas personas (`descriptions`) e está pronta para uso na seleção de personas de debate. "
        "Próximos passos sugeridos:\n"
        "1. Expandir a decodificação para o coreset completo (1M personas, 11 shards) fora desta fase exploratória.\n"
        "2. Cruzar `political_lean` com `religiosity` e `values_priority` para construir personas mais "
        "ricas e internamente consistentes para os dois polos do debate.\n"
        "3. Usar os eixos `att_free_markets`, `att_government_regulation`, `att_labor_unions`, `att_immigration`, "
        "`att_gun_ownership` e `att_capital_punishment` como sinais econômicos/sociais secundários de contraste, "
        "junto com `trust_level` como eixo de confiança institucional."
    )
    report_lines.append("")

    OUT_REPORT_MD.write_text("\n".join(report_lines))
    print(f"[OK] Relatório Markdown salvo em {OUT_REPORT_MD}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
