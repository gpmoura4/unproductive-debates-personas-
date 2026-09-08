"""Baixa os arquivos de schema necessários para a inspeção offline (Fase 0).

Não baixa os arquivos Parquet do dataset — apenas os dois JSONs de schema:
- data/schema/dimensions.json (taxonomia completa, GitHub)
- data/schema/persona_codes.schema.json (mapeamento código -> valores, HuggingFace)
"""

import json
import sys
from pathlib import Path

import requests

DIMENSIONS_URL = "https://raw.githubusercontent.com/MatrAIx-ai/MatrAIx-Persona-8B/main/persona/schema/dimensions.json"
DIMENSIONS_DEST = Path("data/schema/dimensions.json")

HF_REPO_ID = "MatrAIx2026/MatrAIx_Persona_1M_Public_Release"
HF_FILENAME = "persona_codes.schema.json"
HF_SCHEMA_DIR = Path("data/schema/")


def is_valid_json(path: Path) -> bool:
    try:
        json.loads(path.read_text())
        return True
    except (json.JSONDecodeError, OSError):
        return False


def download_dimensions_json() -> bool:
    if DIMENSIONS_DEST.exists() and is_valid_json(DIMENSIONS_DEST):
        print("[SKIP] dimensions.json já existe")
        return True

    DIMENSIONS_DEST.parent.mkdir(parents=True, exist_ok=True)
    print(f"[DOWNLOAD] {DIMENSIONS_URL} ...")
    try:
        resp = requests.get(DIMENSIONS_URL, timeout=30)
        resp.raise_for_status()
        DIMENSIONS_DEST.write_bytes(resp.content)
        if not is_valid_json(DIMENSIONS_DEST):
            print("[ERRO] dimensions.json baixado, mas não é JSON válido.")
            print(f"Primeiros 500 chars: {DIMENSIONS_DEST.read_text()[:500]}")
            return False
        print(f"[OK] dimensions.json salvo em {DIMENSIONS_DEST}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao baixar dimensions.json: {e}")
        return False


def download_hf_schema() -> bool:
    dest_file = HF_SCHEMA_DIR / HF_FILENAME
    if dest_file.exists() and is_valid_json(dest_file):
        print(f"[SKIP] {HF_FILENAME} já existe")
        return True

    HF_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[DOWNLOAD] {HF_FILENAME} de {HF_REPO_ID} (HuggingFace) ...")
    try:
        from huggingface_hub import hf_hub_download

        hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=HF_FILENAME,
            repo_type="dataset",
            local_dir=str(HF_SCHEMA_DIR),
        )
        if not dest_file.exists() or not is_valid_json(dest_file):
            print(f"[ERRO] {HF_FILENAME} baixado, mas não é JSON válido ou não foi encontrado.")
            return False
        print(f"[OK] {HF_FILENAME} salvo em {dest_file}")
        return True
    except Exception as e:
        msg = str(e)
        if "401" in msg or "403" in msg or "Unauthorized" in msg or "Forbidden" in msg or "gated" in msg.lower():
            print("[ERRO] Autenticação necessária.")
            print("Execute: uv run huggingface-cli login")
            print("Depois rode novamente: uv run python scripts/00_download_schema.py")
        else:
            print(f"[ERRO] Falha ao baixar {HF_FILENAME}: {e}")
        return False


def main() -> int:
    ok_dimensions = download_dimensions_json()
    ok_hf_schema = download_hf_schema()

    print("\n--- Validação final ---")
    all_ok = True
    for path in (DIMENSIONS_DEST, HF_SCHEMA_DIR / HF_FILENAME):
        if path.exists() and is_valid_json(path):
            size = path.stat().st_size
            print(f"[OK] {path} ({size:,} bytes)")
        else:
            print(f"[FALTANDO] {path}")
            all_ok = False

    if not (ok_dimensions and ok_hf_schema and all_ok):
        print("\n[FALHA] Um ou mais arquivos de schema não foram baixados corretamente.")
        return 1

    print("\n[SUCESSO] Todos os arquivos de schema estão prontos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
