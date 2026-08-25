"""Inspeção estrutural do schema MatrAIx (Fase 0).

Responde: "Quais das 1.290 dimensões têm semântica política ou ideológica
relevante para polarização política brasileira?"

Pré-requisito: data/schema/dimensions.json (gerado por 00_download_schema.py)
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()

SCHEMA_PATH = Path("data/schema/dimensions.json")
OUT_DIR = Path("outputs")
OUT_REPORT_MD = OUT_DIR / "phase0_schema_report.md"
OUT_JSON = OUT_DIR / "phase0_political_dimensions.json"
OUT_RAW_SAMPLE = OUT_DIR / "phase0_raw_schema_sample.txt"

POLITICAL_TERMS = [
    # Orientação política direta
    "political", "ideology", "leaning", "party", "voting",
    "conservative", "liberal", "progressive", "left", "right",
    # Valores e crenças (Psychology > Worldview > Beliefs)
    "worldview", "belief", "value", "moral", "ethics",
    # Religiosidade (correlacionada com conservadorismo no Brasil)
    "religion", "religious", "faith", "church", "spiritual",
    # Confiança em instituições (marcador de polarização)
    "trust", "institution", "government", "authority",
    # Dimensões WVS / Latinobarometro relevantes ao contexto BR
    "democracy", "authoritarian", "traditional", "secular",
    "nationalism", "globalism", "immigration", "inequality",
    # Motivação e valores (Psychology > Values & Motivation)
    "motivation", "agency", "autonomy",
]

WORLDVIEW_BELIEFS_TERMS = ["psychology", "worldview", "beliefs", "values", "motivation"]


def check_prerequisite() -> dict | list:
    if not SCHEMA_PATH.exists():
        print(f"[ERRO] {SCHEMA_PATH} não encontrado.")
        print("Execute primeiro: uv run python scripts/00_download_schema.py")
        sys.exit(1)

    raw_text = SCHEMA_PATH.read_text()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"[ERRO] {SCHEMA_PATH} não é JSON válido: {e}")
        print(f"Primeiros 500 chars: {raw_text[:500]}")
        sys.exit(1)


def inspect_raw_structure(data: Any) -> None:
    console.rule("Inspeção da estrutura bruta")
    print(f"Tipo raiz: {type(data)}")
    if isinstance(data, dict):
        keys = list(data.keys())
        print(f"Chaves de primeiro nível ({len(keys)}): {keys[:20]}")
    elif isinstance(data, list):
        print(f"Total de itens na lista: {len(data)}")
        if data:
            print(f"Tipo do primeiro item: {type(data[0])}")
            if isinstance(data[0], dict):
                print(f"Chaves do primeiro item: {list(data[0].keys())}")


def find_dimension_list(data: Any) -> list[dict] | None:
    """Tenta localizar a lista de dimensões dentro da estrutura, sem assumir nomes fixos."""
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data

    if isinstance(data, dict):
        # Procurar por uma chave de topo que contenha uma lista de dicts "dimension-like"
        candidate_keys = ["dimensions", "items", "fields", "attributes", "schema"]
        for key in candidate_keys:
            if key in data and isinstance(data[key], list) and data[key] and isinstance(data[key][0], dict):
                return data[key]
        # Fallback: qualquer valor que seja lista de dicts
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
        # Fallback: dict de dict (id -> dimension)
        values = list(data.values())
        if values and isinstance(values[0], dict):
            flattened = []
            for k, v in data.items():
                if isinstance(v, dict):
                    entry = dict(v)
                    entry.setdefault("id", k)
                    flattened.append(entry)
            if flattened:
                return flattened

    return None


# Campos que são templates/metadados de formatação, não conteúdo semântico
# (ex.: "phrase": "aged {value}" faria "value" dar match em toda dimensão).
TEXT_SEARCH_EXCLUDE_FIELDS = {"phrase", "index", "defaultValue"}


def collect_text_fields(dimension: dict) -> str:
    """Concatena os campos de texto semânticos (não-template) de uma dimensão para busca."""
    parts = []
    for key, value in dimension.items():
        if key in TEXT_SEARCH_EXCLUDE_FIELDS:
            continue
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    for v in item.values():
                        if isinstance(v, str):
                            parts.append(v)
    return " ".join(parts).lower()


def get_field(dimension: dict, *candidates: str, default=None):
    for c in candidates:
        if c in dimension:
            return dimension[c]
    # case-insensitive fallback
    lower_map = {k.lower(): k for k in dimension.keys()}
    for c in candidates:
        if c.lower() in lower_map:
            return dimension[lower_map[c.lower()]]
    return default


def extract_values_list(dimension: dict) -> list:
    values = get_field(dimension, "values", "allowed_values", "options", "categories", default=[])
    if isinstance(values, dict):
        return list(values.keys())
    if isinstance(values, list):
        return values
    return []


def main() -> int:
    data = check_prerequisite()
    inspect_raw_structure(data)

    dimensions = find_dimension_list(data)

    if not dimensions:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        sample = json.dumps(data, indent=2, ensure_ascii=False)[:3000]
        OUT_RAW_SAMPLE.write_text(sample)
        print("[AVISO] Estrutura inesperada — não foi possível localizar lista de dimensões.")
        print(f"Ver: {OUT_RAW_SAMPLE}")
        return 0

    console.rule("Inventário geral")
    total_dims = len(dimensions)
    print(f"Total de dimensões encontradas: {total_dims}")

    all_field_names: Counter = Counter()
    for d in dimensions:
        all_field_names.update(d.keys())
    print(f"Campos disponíveis por dimensão (com frequência): {dict(all_field_names)}")

    # No schema real do MatrAIx (dimensions.json), o campo "category" combina
    # grupo e subgrupo em um único texto (ex.: "Worldview: Beliefs").
    # Tentamos campos separados primeiro, com "category" como fallback para grupo.
    group_field_candidates = ("group", "Group", "category_group", "top_group", "category", "Category")
    subgroup_field_candidates = ("subgroup", "sub_group", "Subgroup")
    category_field_candidates = ("category", "Category")
    id_field_candidates = ("id", "code", "dimension_id", "key")
    label_field_candidates = ("label", "name", "title", "dimension_name")

    group_counter: Counter = Counter()
    value_counts = []
    for d in dimensions:
        group = get_field(d, *group_field_candidates, default="(sem grupo)")
        group_counter[str(group)] += 1
        values = extract_values_list(d)
        value_counts.append(len(values))

    avg_values = sum(value_counts) / len(value_counts) if value_counts else 0

    table = Table(title="Dimensões por grupo")
    table.add_column("Grupo")
    table.add_column("Contagem", justify="right")
    for group, count in group_counter.most_common():
        table.add_row(group, str(count))
    console.print(table)
    print(f"Número médio de valores categóricos por dimensão: {avg_values:.2f}")

    # Tarefa 2.2 — Busca por termos políticos
    console.rule("Busca por termos politicamente relevantes")
    all_candidates = []
    for d in dimensions:
        text_blob = collect_text_fields(d)
        matched = [term for term in POLITICAL_TERMS if term in text_blob]
        if matched:
            all_candidates.append({
                "id": str(get_field(d, *id_field_candidates, default="")),
                "label": str(get_field(d, *label_field_candidates, default="")),
                "group": str(get_field(d, *group_field_candidates, default="")),
                "subgroup": str(get_field(d, *subgroup_field_candidates, default="")),
                "category": str(get_field(d, *category_field_candidates, default="")),
                "values": extract_values_list(d),
                "matched_terms": matched,
            })
    print(f"Total de dimensões com match de termos políticos: {len(all_candidates)}")

    # Tarefa 2.3 — Psychology/Worldview/Beliefs específico
    console.rule("Psychology / Worldview / Beliefs / Values / Motivation")
    worldview_dims = []
    for d in dimensions:
        group = str(get_field(d, *group_field_candidates, default="")).lower()
        subgroup = str(get_field(d, *subgroup_field_candidates, default="")).lower()
        category = str(get_field(d, *category_field_candidates, default="")).lower()
        combined = f"{group} {subgroup} {category}"
        if any(term in combined for term in WORLDVIEW_BELIEFS_TERMS):
            worldview_dims.append({
                "id": str(get_field(d, *id_field_candidates, default="")),
                "label": str(get_field(d, *label_field_candidates, default="")),
                "group": str(get_field(d, *group_field_candidates, default="")),
                "subgroup": str(get_field(d, *subgroup_field_candidates, default="")),
                "category": str(get_field(d, *category_field_candidates, default="")),
                "values": extract_values_list(d),
            })
    print(f"Total de dimensões em Psychology/Worldview/Beliefs/Values/Motivation: {len(worldview_dims)}")

    # Outputs
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    output_json = {
        "total_dimensions_in_schema": total_dims,
        "total_matched": len(all_candidates),
        "psychology_worldview_beliefs_count": len(worldview_dims),
        "all_candidates": all_candidates,
        "psychology_worldview_beliefs": worldview_dims,
    }
    OUT_JSON.write_text(json.dumps(output_json, indent=2, ensure_ascii=False))
    print(f"[OK] JSON salvo em {OUT_JSON}")

    # Markdown report
    lines = []
    lines.append("# Fase 0 — Relatório de Inspeção do Schema MatrAIx\n")

    lines.append("## 1. Sumário geral do schema\n")
    lines.append(f"- Total de dimensões: {total_dims}")
    lines.append(f"- Número médio de valores categóricos por dimensão: {avg_values:.2f}\n")
    lines.append("| Grupo | Contagem |")
    lines.append("|---|---|")
    for group, count in group_counter.most_common():
        lines.append(f"| {group} | {count} |")
    lines.append("")

    lines.append("## 2. Dimensões em Psychology/Worldview/Beliefs\n")
    if worldview_dims:
        lines.append("| id | label | valores |")
        lines.append("|---|---|---|")
        for d in worldview_dims:
            values_str = ", ".join(str(v) for v in d["values"][:10])
            if len(d["values"]) > 10:
                values_str += ", ..."
            lines.append(f"| {d['id']} | {d['label']} | {values_str} |")
    else:
        lines.append("_Nenhuma dimensão encontrada nesta categoria._")
    lines.append("")

    lines.append("## 3. Dimensões candidatas por term-match\n")
    if all_candidates:
        lines.append("| id | label | grupo | termos matched |")
        lines.append("|---|---|---|---|")
        for d in all_candidates:
            lines.append(f"| {d['id']} | {d['label']} | {d['group']} | {', '.join(d['matched_terms'])} |")
    else:
        lines.append("_Nenhuma dimensão candidata encontrada por term-match._")
    lines.append("")

    lines.append("## 4. Dimensões prioritárias para Fase 1\n")
    priority_terms = {"political", "leaning", "ideology", "religio", "belief", "worldview", "trust"}
    priority = [
        d for d in all_candidates
        if any(pt in " ".join(d["matched_terms"]) for pt in priority_terms)
    ]
    if priority:
        for d in priority:
            lines.append(f"- **{d['id']}** — {d['label']} (grupo: {d['group']}, termos: {', '.join(d['matched_terms'])})")
    else:
        lines.append("_Nenhuma dimensão prioritária identificada automaticamente — revisar seção 3 manualmente._")
    lines.append("")

    OUT_REPORT_MD.write_text("\n".join(lines))
    print(f"[OK] Relatório Markdown salvo em {OUT_REPORT_MD}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
