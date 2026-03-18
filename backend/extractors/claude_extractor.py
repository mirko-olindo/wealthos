"""
Estrazione automatica dati da documenti finanziari tramite Claude API.
Supporta: PDF, Excel, CSV, immagini di statement.
"""
import os
import base64
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

import anthropic
import pdfplumber
import pandas as pd

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

EXTRACTION_PROMPT = """Sei un esperto analista finanziario. Analizza questo documento finanziario ed estrai le informazioni strutturate.

Restituisci SOLO un oggetto JSON valido con questa struttura (usa null per campi non trovati):

{
  "doc_category": "nav_statement|capital_call|distribution|report|statement|other",
  "doc_date": "YYYY-MM-DD o null",
  "vehicle_name": "nome del fondo/veicolo o null",
  "manager": "nome del gestore/manager o null",
  "asset_class": "Private Equity|Real Estate|Hedge Fund|Bond|Equity|Cash|Other o null",
  "currency": "EUR|USD|GBP|CHF o null",
  
  "nav": {
    "value": numero o null,
    "date": "YYYY-MM-DD o null",
    "per_unit": numero o null,
    "units": numero o null
  },
  
  "distribution": {
    "amount": numero o null,
    "payment_date": "YYYY-MM-DD o null",
    "type": "income|return_of_capital|capital_gain|other o null"
  },
  
  "capital_call": {
    "amount": numero o null,
    "call_date": "YYYY-MM-DD o null",
    "due_date": "YYYY-MM-DD o null",
    "call_number": numero o null,
    "purpose": "stringa o null"
  },
  
  "position": {
    "invested_capital": numero o null,
    "current_value": numero o null,
    "tvpi": numero o null,
    "dpi": numero o null,
    "irr": numero o null
  },
  
  "summary": "breve descrizione del documento in italiano (max 100 caratteri)"
}

Non aggiungere testo fuori dal JSON. Non usare markdown. Solo JSON puro."""


def extract_text_from_pdf(file_path: str) -> str:
    """Estrae testo da PDF usando pdfplumber."""
    text_parts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages[:10]):  # max 10 pagine
                text = page.extract_text()
                if text:
                    text_parts.append(f"--- Pagina {i+1} ---\n{text}")
                # Estrai anche tabelle
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        rows = [" | ".join(str(c) if c else "" for c in row) for row in table if row]
                        text_parts.append("TABELLA:\n" + "\n".join(rows))
    except Exception as e:
        return f"Errore estrazione PDF: {e}"
    return "\n\n".join(text_parts)[:15000]  # limite contesto


def extract_text_from_excel(file_path: str) -> str:
    """Estrae testo da Excel/CSV."""
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path, nrows=200)
        else:
            xl = pd.ExcelFile(file_path)
            sheets = []
            for sheet in xl.sheet_names[:5]:
                df = pd.read_excel(file_path, sheet_name=sheet, nrows=100)
                sheets.append(f"=== Foglio: {sheet} ===\n{df.to_string(index=False)}")
            return "\n\n".join(sheets)[:15000]
        return df.to_string(index=False)[:15000]
    except Exception as e:
        return f"Errore estrazione Excel: {e}"


def encode_image_base64(file_path: str) -> tuple[str, str]:
    """Codifica immagine in base64."""
    ext = Path(file_path).suffix.lower()
    media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    media_type = media_types.get(ext, "image/jpeg")
    with open(file_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def parse_extraction_result(raw_text: str) -> dict:
    """Pulisce e parsa il JSON restituito da Claude."""
    # Rimuovi eventuali backtick markdown
    text = re.sub(r"```json\s*", "", raw_text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Prova a trovare il primo oggetto JSON valido
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"error": "Impossibile parsare il JSON", "raw": raw_text[:500]}


async def extract_from_document(file_path: str, file_type: str) -> dict:
    """
    Funzione principale: estrae dati strutturati da un documento finanziario.
    Ritorna un dizionario con i dati estratti.
    """
    file_type = file_type.lower()
    
    try:
        # ── Immagini: invio diretto a Claude Vision ───────────────────────────
        if file_type in ["jpg", "jpeg", "png", "webp"]:
            image_data, media_type = encode_image_base64(file_path)
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                        {"type": "text", "text": EXTRACTION_PROMPT}
                    ]
                }]
            )
        
        # ── PDF e Excel: estrai testo poi invia a Claude ──────────────────────
        else:
            if file_type == "pdf":
                text_content = extract_text_from_pdf(file_path)
            elif file_type in ["xlsx", "xls", "csv"]:
                text_content = extract_text_from_excel(file_path)
            else:
                text_content = f"Tipo file non supportato per estrazione automatica: {file_type}"

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": f"{EXTRACTION_PROMPT}\n\n=== CONTENUTO DOCUMENTO ===\n{text_content}"
                }]
            )

        raw_response = message.content[0].text
        return parse_extraction_result(raw_response)

    except anthropic.APIError as e:
        return {"error": f"Claude API error: {str(e)}"}
    except Exception as e:
        return {"error": f"Errore estrazione: {str(e)}"}
