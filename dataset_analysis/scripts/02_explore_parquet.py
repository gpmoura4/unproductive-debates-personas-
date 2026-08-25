"""Download de 2 shards Parquet e exploração de distribuições (Fase 1).

Responde: "Existem personas no coreset com valores contrastantes nas dimensões
politicamente relevantes, e qual é a distribuição e cobertura desses atributos?"

Pré-requisitos:
- outputs/phase0_political_dimensions.json (gerado por 01_inspect_schema.py)
- HuggingFace autenticado, se o dataset for gated
"""

import json
import sys
from pathlib import Path

import pandas as pd

HF_REPO_ID = "MatrAIx2026/MatrAIx_Persona_1M_Public_Release"
DATA_DIR = Path("data/persona-1m")
OUT_DIR = Path("outputs")
PHASE0_JSON = OUT_DIR / "phase0_political_dimensions.json"
OUT_SCHEMA_RAW = OUT_DIR / "phase1_parquet_schema_raw.txt"
OUT_REPORT_MD = OUT_DIR / "phase1_parquet_report.md"
OUT_CANDIDATES_JSON = OUT_DIR / "phase1_candidate_personas.json"

DIRECT_MATCH_TERMS = [
    "political", "ideolog", "worldview", "belief",
    "religion", "trust", "value", "moral", "leaning",
]


def check_prerequisite() -> dict:
    if not PHASE0_JSON.exists():
        print(f"[ERRO] {PHASE0_JSON} não encontrado.")
        print("Execute primeiro: uv run python scripts/01_inspect_schema.py")
        sys.exit(1)
    try:
        return json.loads(PHASE0_JSON.read_text())
    except json.JSONDecodeError as e:
        print(f"[ERRO] {PHASE0_JSON} não é JSON válido: {e}")
        sys.exit(1)


def df_to_markdown(df: pd.DataFrame) -> str:
    """Renderiza um DataFrame como tabela Markdown sem depender de `tabulate`."""
    if df.empty:
        return "_(sem dados)_"
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(str(h) for h in headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row.tolist()) + " |")
    return "\n".join(lines)


def auth_error_message():
    print("[ERRO] Autenticação necessária.")
    print("Execute: uv run huggingface-cli login")
    print("Depois rode novamente: uv run python scripts/02_explore_parquet.py")


def download_shards() -> list[Path]:
    from huggingface_hub import list_repo_files, hf_hub_download

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        all_files = list(list_repo_files(repo_id=HF_REPO_ID, repo_type="dataset"))
    except Exception as e:
        msg = str(e)
        if "401" in msg or "403" in msg or "Unauthorized" in msg or "Forbidden" in msg or "gated" in msg.lower():
            auth_error_message()
            sys.exit(1)
        print(f"[ERRO] Falha ao listar arquivos do repositório: {e}")
        sys.exit(1)

    parquet_files = sorted(f for f in all_files if f.endswith(".parquet"))
    print(f"Parquets disponíveis ({len(parquet_files)} total): {parquet_files[:5]}")

    if not parquet_files:
        print("[ERRO] Nenhum arquivo .parquet encontrado no repositório.")
        sys.exit(1)

    shards_to_download = parquet_files[:2]

    for shard in shards_to_download:
        dest = DATA_DIR / Path(shard).name
        if dest.exists():
            print(f"[SKIP] {dest.name} já existe")
            continue
        print(f"[DOWNLOAD] {shard} ...")
        try:
            downloaded_path = Path(hf_hub_download(
                repo_id=HF_REPO_ID,
                filename=shard,
                repo_type="dataset",
                local_dir=str(DATA_DIR),
            ))
        except Exception as e:
            msg = str(e)
            if "401" in msg or "403" in msg or "Unauthorized" in msg or "Forbidden" in msg or "gated" in msg.lower():
                auth_error_message()
                sys.exit(1)
            print(f"[ERRO] Falha ao baixar {shard}: {e}")
            sys.exit(1)

        # hf_hub_download preserva o caminho relativo do repo (ex.: "data/persona-1m-0000.parquet")
        # dentro de local_dir. Achatamos para DATA_DIR/<nome> para manter os shards num único nível.
        if downloaded_path.resolve() != dest.resolve():
            dest.parent.mkdir(parents=True, exist_ok=True)
            downloaded_path.replace(dest)

    return sorted(DATA_DIR.glob("*.parquet"))


def inspect_parquet_schema(parquet_files_local: list[Path]) -> None:
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(parquet_files_local[0])

    inspection_lines = []
    inspection_lines.append("=== Schema Parquet ===")
    inspection_lines.append(str(pf.schema))
    inspection_lines.append("\n=== Metadata ===")
    inspection_lines.append(str(pf.metadata))

    try:
        sample_df = pf.read_row_group(0).to_pandas().head(5)
    except Exception as e:
        print(f"[AVISO] Falha ao ler row group 0: {e}. Tentando pandas.read_parquet direto.")
        sample_df = pd.read_parquet(parquet_files_local[0]).head(5)

    inspection_lines.append(f"\n=== Colunas ({len(sample_df.columns)}) ===")
    inspection_lines.append(str(list(sample_df.columns)))
    inspection_lines.append("\n=== Tipos ===")
    inspection_lines.append(str(sample_df.dtypes))
    inspection_lines.append("\n=== Primeiras 2 linhas ===")
    inspection_lines.append(sample_df.head(2).to_string())

    raw_output = "\n".join(inspection_lines)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_SCHEMA_RAW.write_text(raw_output)
    print(raw_output)


def main() -> int:
    phase0 = check_prerequisite()

    parquet_files_local = download_shards()
    if not parquet_files_local:
        print("[ERRO] Nenhum shard Parquet disponível localmente após download.")
        return 1

    inspect_parquet_schema(parquet_files_local)

    import duckdb

    conn = duckdb.connect()
    try:
        conn.execute(f"""
            CREATE VIEW personas AS
            SELECT * FROM read_parquet('{DATA_DIR}/*.parquet')
        """)
        total = conn.execute("SELECT COUNT(*) FROM personas").fetchone()[0]
        cols_df = conn.execute("DESCRIBE personas").fetchdf()
        print(f"Total de registros nos 2 shards: {total:,}")
        print(cols_df.to_string())
    except Exception as e:
        print(f"[ERRO] Falha ao carregar Parquet via DuckDB: {e}")
        print("[FALLBACK] Tentando pandas.read_parquet diretamente.")
        dfs = [pd.read_parquet(p) for p in parquet_files_local]
        combined = pd.concat(dfs, ignore_index=True)
        conn = duckdb.connect()
        conn.register("personas", combined)
        total = len(combined)
        cols_df = pd.DataFrame({
            "column_name": combined.columns,
            "column_type": [str(t) for t in combined.dtypes],
        })
        print(f"Total de registros (via fallback pandas): {total:,}")

    all_columns = list(cols_df["column_name"])

    candidate_ids = {d["id"].lower() for d in phase0.get("all_candidates", []) if d.get("id")}
    candidate_labels = {d["label"].lower() for d in phase0.get("all_candidates", []) if d.get("label")}

    matched_cols = [
        c for c in all_columns
        if c.lower() in candidate_ids
        or c.lower() in candidate_labels
        or any(term in c.lower() for term in DIRECT_MATCH_TERMS)
    ]
    print(f"Colunas com semântica política encontradas: {matched_cols}")

    binary_cols = []
    text_col_candidates = []
    for c in all_columns:
        col_type = str(cols_df[cols_df["column_name"] == c]["column_type"].values[0]).upper()
        if col_type in ("BLOB", "BINARY", "VARBINARY"):
            binary_cols.append(c)
        elif col_type in ("VARCHAR", "TEXT", "STRING"):
            text_col_candidates.append(c)

    if binary_cols:
        print(f"[INFO] Colunas binárias detectadas: {binary_cols}")
        print("[INFO] O schema usa vetor compactado. Decodificação requer persona_codes.schema.json.")

    distributions_md = []
    if matched_cols:
        for col in matched_cols:
            try:
                dist = conn.execute(f"""
                    SELECT
                        "{col}" AS valor,
                        COUNT(*) AS n,
                        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
                    FROM personas
                    WHERE "{col}" IS NOT NULL
                    GROUP BY "{col}"
                    ORDER BY n DESC
                    LIMIT 20
                """).fetchdf()
                print(f"\n--- {col} ---")
                print(dist.to_string(index=False))
                distributions_md.append(f"### {col}\n")
                distributions_md.append(df_to_markdown(dist))
                distributions_md.append("")
            except Exception as e:
                print(f"[ERRO] Query falhou para coluna '{col}': {e}")
                distributions_md.append(f"### {col}\n\n_Query falhou: {e}_\n")
    elif text_col_candidates:
        desc_col = text_col_candidates[0]
        sample_text = conn.execute(f"""
            SELECT "{desc_col}" FROM personas
            WHERE "{desc_col}" IS NOT NULL LIMIT 3
        """).fetchdf()
        print(f"[INFO] Campo de descrição textual: '{desc_col}'")
        print(sample_text.to_string())

    # Tarefa 3.6 — Identificação de perfis contrastantes
    pol_col = next((c for c in matched_cols if "leaning" in c.lower() or "political" in c.lower()), None)
    left_profiles = None
    right_profiles = None
    abordagem_usada = "C"
    proximos_passos = ""

    if pol_col:
        abordagem_usada = "A"
        try:
            valores = conn.execute(
                f'SELECT DISTINCT "{pol_col}" FROM personas WHERE "{pol_col}" IS NOT NULL'
            ).fetchdf()
            print(f"Valores únicos em '{pol_col}':", valores[pol_col].tolist())

            left_profiles = conn.execute(f"""
                SELECT * FROM personas
                WHERE "{pol_col}" ILIKE ANY (['%progressive%', '%left%', '%liberal%'])
                LIMIT 5
            """).fetchdf()

            right_profiles = conn.execute(f"""
                SELECT * FROM personas
                WHERE "{pol_col}" ILIKE ANY (['%conservative%', '%right%', '%traditional%'])
                LIMIT 5
            """).fetchdf()
        except Exception as e:
            print(f"[ERRO] Abordagem A falhou: {e}")
            left_profiles = right_profiles = None

    def _is_empty(df) -> bool:
        return df is None or df.empty

    if (_is_empty(left_profiles) or _is_empty(right_profiles)) and text_col_candidates:
        abordagem_usada = "B"
        desc_col = text_col_candidates[0]
        try:
            left_profiles = conn.execute(f"""
                SELECT * FROM personas
                WHERE "{desc_col}" ILIKE '%progressive%'
                   OR "{desc_col}" ILIKE '%left-leaning%'
                   OR "{desc_col}" ILIKE '%liberal%'
                LIMIT 5
            """).fetchdf()

            right_profiles = conn.execute(f"""
                SELECT * FROM personas
                WHERE "{desc_col}" ILIKE '%conservative%'
                   OR "{desc_col}" ILIKE '%right-leaning%'
                   OR "{desc_col}" ILIKE '%traditional%'
                LIMIT 5
            """).fetchdf()
        except Exception as e:
            print(f"[ERRO] Abordagem B falhou: {e}")
            left_profiles = right_profiles = None

    if _is_empty(left_profiles) or _is_empty(right_profiles):
        abordagem_usada = "C"
        left_profiles = right_profiles = None
        proximos_passos = (
            "O dataset usa vetor binário compactado (645 bytes / 1.290 atributos x 4 bits). "
            "Para decodificar, é necessário:\n"
            "1. Usar persona_codes.schema.json para mapear índice -> valores categóricos\n"
            "2. Implementar desempacotamento nibble-by-nibble\n"
            "3. Script de decodificação será implementado na Fase 2 deste projeto"
        )

    # Cobertura
    coverage_pct = 0.0
    records_with_political_attrs = 0
    if matched_cols:
        try:
            not_null_conditions = " OR ".join(f'"{c}" IS NOT NULL' for c in matched_cols)
            records_with_political_attrs = conn.execute(f"""
                SELECT COUNT(*) FROM personas WHERE {not_null_conditions}
            """).fetchone()[0]
            coverage_pct = round(records_with_political_attrs * 100.0 / total, 2) if total else 0.0
        except Exception as e:
            print(f"[ERRO] Falha ao calcular cobertura: {e}")

    # Outputs
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    report_lines = []
    report_lines.append("# Fase 1 — Relatório de Exploração do Dataset Parquet\n")

    report_lines.append("## 1. Schema real do Parquet\n")
    report_lines.append(f"- Registros nos 2 shards: {total:,}")
    report_lines.append(f"- Total de colunas: {len(all_columns)}")
    report_lines.append("\n| Coluna | Tipo |")
    report_lines.append("|---|---|")
    for _, row in cols_df.iterrows():
        report_lines.append(f"| {row['column_name']} | {row['column_type']} |")
    report_lines.append("")

    report_lines.append("## 2. Colunas politicamente relevantes\n")
    if matched_cols:
        report_lines.append(f"Encontradas {len(matched_cols)} colunas: {', '.join(matched_cols)}\n")
    else:
        report_lines.append(
            "Nenhuma coluna com nome diretamente reconhecível como política foi encontrada.\n"
        )
        if binary_cols:
            report_lines.append(
                f"O schema parece usar vetor(es) binário(s) compactado(s): {', '.join(binary_cols)}. "
                "A decodificação requer o arquivo `persona_codes.schema.json` (ver seção 7).\n"
            )
    report_lines.append("")

    report_lines.append("## 3. Distribuições de valores\n")
    if distributions_md:
        report_lines.extend(distributions_md)
    else:
        report_lines.append("_Sem colunas categóricas diretas para tabular distribuições._\n")

    report_lines.append("## 4. Exemplos de perfis — Polo A (progressista/esquerda)\n")
    report_lines.append("```json")
    if left_profiles is not None and not left_profiles.empty:
        report_lines.append(left_profiles.head(3).to_json(orient="records", indent=2, force_ascii=False))
    else:
        report_lines.append("[]")
    report_lines.append("```\n")

    report_lines.append("## 5. Exemplos de perfis — Polo B (conservador/direita)\n")
    report_lines.append("```json")
    if right_profiles is not None and not right_profiles.empty:
        report_lines.append(right_profiles.head(3).to_json(orient="records", indent=2, force_ascii=False))
    else:
        report_lines.append("[]")
    report_lines.append("```\n")

    report_lines.append("## 6. Cobertura\n")
    report_lines.append(
        f"- Registros com atributos políticos não-nulos: {records_with_political_attrs:,} / {total:,} "
        f"({coverage_pct}%)\n"
    )

    report_lines.append("## 7. Conclusão e próximos passos\n")
    report_lines.append(f"Abordagem usada para identificar perfis contrastantes: **{abordagem_usada}**\n")
    if proximos_passos:
        report_lines.append(proximos_passos)
    else:
        report_lines.append(
            "Colunas política/ideologicamente relevantes foram identificadas diretamente no Parquet. "
            "Próximo passo sugerido: expandir a amostra de shards e validar a distribuição frente aos "
            "benchmarks GSS/Latinobarometro citados na documentação do dataset."
        )
    report_lines.append("")

    OUT_REPORT_MD.write_text("\n".join(report_lines))
    print(f"[OK] Relatório Markdown salvo em {OUT_REPORT_MD}")

    candidates_output = {
        "polo_progressista": json.loads(left_profiles.to_json(orient="records", force_ascii=False))
        if left_profiles is not None and not left_profiles.empty else [],
        "polo_conservador": json.loads(right_profiles.to_json(orient="records", force_ascii=False))
        if right_profiles is not None and not right_profiles.empty else [],
        "coverage_stats": {
            "total_records_sampled": total,
            "records_with_political_attrs": records_with_political_attrs,
            "coverage_pct": coverage_pct,
        },
        "abordagem_usada": abordagem_usada,
        "proximos_passos": proximos_passos,
    }
    OUT_CANDIDATES_JSON.write_text(json.dumps(candidates_output, indent=2, ensure_ascii=False))
    print(f"[OK] JSON de candidatos salvo em {OUT_CANDIDATES_JSON}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
