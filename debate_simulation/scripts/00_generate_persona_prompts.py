"""Geração de prompts de persona a partir das personas decodificadas (Fase 3).

Lê outputs/phase2_decoded_personas.json (gerado pelo subprojeto dataset_analysis/)
e transforma cada persona dos polos esquerda/direita em um prompt de sistema em
linguagem natural, pronto para ser usado como persona de um agente debatedor.

Este script NÃO faz nenhuma chamada de API/LLM — só gera texto a partir dos
atributos categóricos já decodificados. A integração com um motor de LLM
específico (para gerar as falas do debate, moderação e julgamento) é um passo
posterior, ainda em aberto.

Pré-requisito:
- ../dataset_analysis/outputs/phase2_decoded_personas.json

Outputs:
- outputs/phase3_persona_prompts.json  (prompts estruturados, por polo)
- prompts/polo_esquerda/persona_NN.txt (um arquivo de prompt por persona)
- prompts/polo_direita/persona_NN.txt
"""

import json
import sys
from pathlib import Path

DECODED_PERSONAS_PATH = Path("../dataset_analysis/outputs/phase2_decoded_personas.json")

OUT_DIR = Path("outputs")
OUT_PROMPTS_JSON = OUT_DIR / "phase3_persona_prompts.json"
PROMPTS_DIR = Path("prompts")

# Rótulos em português para cada valor categórico, usados para compor o prompt
# em linguagem natural. Dimensões/valores fora deste mapa aparecem com o texto
# bruto do dataset (em inglês) como fallback.
ATTRIBUTE_LABELS = {
    "political_lean": "orientação política",
    "religiosity": "religiosidade",
    "trust_level": "nível de confiança institucional",
    "values_priority": "valor central",
    "att_free_markets": "posição sobre livre mercado",
    "att_government_regulation": "posição sobre regulação governamental",
    "att_labor_unions": "posição sobre sindicatos",
    "att_immigration": "posição sobre imigração",
    "att_gun_ownership": "posição sobre posse de armas",
    "att_capital_punishment": "posição sobre pena de morte",
}

POLE_LABELS = {
    "polo_esquerda_political_lean": "polo_esquerda",
    "polo_direita_political_lean": "polo_direita",
}


def check_prerequisite() -> dict:
    if not DECODED_PERSONAS_PATH.exists():
        print(f"[ERRO] {DECODED_PERSONAS_PATH} não encontrado.")
        print("Execute primeiro (a partir de dataset_analysis/):")
        print("  cd ../dataset_analysis && uv run python scripts/03_decode_attributes.py")
        sys.exit(1)
    try:
        return json.loads(DECODED_PERSONAS_PATH.read_text())
    except json.JSONDecodeError as e:
        print(f"[ERRO] {DECODED_PERSONAS_PATH} não é JSON válido: {e}")
        sys.exit(1)


def build_prompt_text(persona: dict, pole_name: str, index: int) -> str:
    attrs = persona.get("political_attributes", {})
    non_null_attrs = {k: v for k, v in attrs.items() if v is not None}

    lines = [
        f"Você é uma persona de debate ({pole_name.replace('_', ' ')}), "
        f"construída a partir de atributos ideológicos reais do dataset MatrAIx Persona 1M "
        f"(fonte: {persona.get('source', 'desconhecida')}, id {persona.get('source_record_id', 'N/A')}).",
        "",
        "Atributos que definem seu posicionamento:",
    ]

    if not non_null_attrs:
        lines.append("- (nenhum atributo político preenchido para esta persona — usar com cautela)")
    else:
        for attr_id, value in non_null_attrs.items():
            label = ATTRIBUTE_LABELS.get(attr_id, attr_id)
            lines.append(f"- {label}: {value}")

    lines.append("")
    lines.append(
        "Debata de acordo com esses atributos, mantendo consistência de posicionamento "
        "ao longo de toda a conversa. Não invente atributos que não foram listados acima."
    )

    return "\n".join(lines)


def main() -> int:
    decoded = check_prerequisite()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    output = {"poles": {}}
    total_generated = 0

    for json_key, pole_name in POLE_LABELS.items():
        personas = decoded.get(json_key, [])
        if not personas:
            print(f"[AVISO] Nenhuma persona encontrada em '{json_key}'.")
            output["poles"][pole_name] = []
            continue

        pole_dir = PROMPTS_DIR / pole_name
        pole_dir.mkdir(parents=True, exist_ok=True)

        pole_entries = []
        for i, persona in enumerate(personas):
            prompt_text = build_prompt_text(persona, pole_name, i)
            filename = f"persona_{i:02d}.txt"
            (pole_dir / filename).write_text(prompt_text)

            pole_entries.append({
                "index": i,
                "source_record_id": persona.get("source_record_id"),
                "political_attributes": persona.get("political_attributes", {}),
                "prompt_file": str(pole_dir / filename),
                "prompt_text": prompt_text,
            })
            total_generated += 1

        output["poles"][pole_name] = pole_entries
        print(f"[OK] {len(pole_entries)} prompts gerados para '{pole_name}' em {pole_dir}/")

    OUT_PROMPTS_JSON.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"[OK] Total de {total_generated} prompts gerados.")
    print(f"[OK] JSON estruturado salvo em {OUT_PROMPTS_JSON}")

    if total_generated == 0:
        print("[ERRO] Nenhum prompt foi gerado — verifique outputs/phase2_decoded_personas.json.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
