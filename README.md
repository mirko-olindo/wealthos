# WealthOS — Portfolio Intelligence Platform

Piattaforma per la gestione e visualizzazione aggregata di un portafoglio di investimenti.

## Funzionalità

- **Repository documenti**: carica PDF, Excel, CSV, immagini di statement finanziari
- **Estrazione automatica**: Claude AI estrae NAV, capital call, distribuzioni, metriche dai documenti
- **Dashboard**: NAV totale, allocazione per asset class, cash flow, performance per veicolo
- **Storico**: grafici NAV nel tempo, cash flow annuale, distribuzioni vs capital calls
- **Tracciabilità**: ogni dato è collegato al documento originale da cui è stato estratto

---

## Setup in 5 minuti

### 1. Prerequisiti

```bash
python 3.11+
pip
```

### 2. Clona e installa dipendenze

```bash
cd wealthos
pip install -r requirements.txt
```

### 3. Configura le variabili d'ambiente

```bash
cp .env.example .env
# Apri .env e inserisci la tua ANTHROPIC_API_KEY
```

Ottieni la tua API key su: https://console.anthropic.com

### 4. (Opzionale) Carica dati di esempio

```bash
python seed.py
```

Questo inserisce 5 veicoli di investimento con storico NAV, distribuzioni e capital calls.

### 5. Avvia il server

```bash
python main.py
```

Oppure con uvicorn direttamente:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Apri nel browser

- **App**: http://localhost:8000
- **API docs** (Swagger): http://localhost:8000/docs
- **Frontend standalone**: apri direttamente `frontend/index.html` nel browser

---

## Struttura del progetto

```
wealthos/
├── main.py                          # Entry point FastAPI
├── requirements.txt
├── seed.py                          # Dati di esempio
├── .env.example                     # Template variabili ambiente
│
├── backend/
│   ├── models/
│   │   ├── db.py                    # Modelli SQLAlchemy (tabelle DB)
│   │   ├── schemas.py               # Schemi Pydantic (API request/response)
│   │   └── database.py              # Connessione DB
│   │
│   ├── extractors/
│   │   └── claude_extractor.py      # Estrazione dati da documenti con Claude AI
│   │
│   ├── services/
│   │   ├── normalizer.py            # Normalizzazione dati estratti → DB
│   │   └── aggregator.py            # Aggregazioni per dashboard
│   │
│   └── routers/
│       ├── vehicles.py              # CRUD veicoli + NAV/distribuzioni/capital calls
│       ├── documents.py             # Upload, lista, estrazione documenti
│       └── dashboard.py             # KPI, allocazione, cash flow, NAV history
│
├── frontend/
│   └── index.html                   # Frontend React single-page (no build required)
│
├── uploads/                         # File caricati (creata automaticamente)
└── data/
    └── wealthos.db                  # Database SQLite (creato automaticamente)
```

---

## API principali

### Dashboard
```
GET /api/dashboard/kpi              → KPI: NAV totale, capitale, distribuzioni, TVPI
GET /api/dashboard/allocation       → Allocazione per asset class
GET /api/dashboard/cashflow         → Cash flow annuale
GET /api/dashboard/nav-history      → Storico NAV (tutti o per veicolo)
GET /api/dashboard/vehicles-summary → Riepilogo performance per veicolo
```

### Veicoli
```
GET    /api/vehicles/                    → Lista veicoli
POST   /api/vehicles/                    → Crea veicolo
GET    /api/vehicles/{id}                → Dettaglio veicolo
PUT    /api/vehicles/{id}                → Aggiorna veicolo
DELETE /api/vehicles/{id}                → Elimina veicolo

POST /api/vehicles/{id}/nav              → Aggiungi NAV statement
GET  /api/vehicles/{id}/nav              → Lista NAV statements
POST /api/vehicles/{id}/distributions    → Aggiungi distribuzione
GET  /api/vehicles/{id}/distributions    → Lista distribuzioni
POST /api/vehicles/{id}/capital-calls    → Aggiungi capital call
GET  /api/vehicles/{id}/capital-calls    → Lista capital calls
POST /api/vehicles/{id}/positions        → Aggiungi posizione/snapshot
GET  /api/vehicles/{id}/positions        → Lista posizioni
```

### Documenti
```
POST   /api/documents/upload         → Carica documento (multipart/form-data)
GET    /api/documents/               → Lista documenti (filtri: vehicle_id, doc_category, status)
GET    /api/documents/{id}           → Dettaglio documento + dati estratti
POST   /api/documents/{id}/extract   → Ri-avvia estrazione
DELETE /api/documents/{id}           → Elimina documento
```

---

## Come funziona l'estrazione automatica

1. Carichi un PDF/Excel/immagine tramite il frontend o l'API
2. Il backend salva il file e crea un record `Document` con status `pending`
3. In background, il file viene processato:
   - **PDF**: `pdfplumber` estrae testo e tabelle
   - **Excel/CSV**: `pandas` converte in formato testuale
   - **Immagini**: inviate direttamente a Claude Vision
4. Il testo viene inviato a Claude API con un prompt strutturato
5. Claude restituisce un JSON con: tipo documento, date, importi, nome veicolo, NAV, distribuzioni, capital calls, metriche TVPI/IRR
6. Il `normalizer` applica i dati estratti alle tabelle appropriate del DB
7. Ogni record creato mantiene il riferimento al `document_id` originale

---

## Aggiungere nuovi tipi di documento

Per aggiungere il parsing di un nuovo tipo di documento, modifica il prompt in `backend/extractors/claude_extractor.py` e aggiungi il relativo handler in `backend/services/normalizer.py`.

---

## Deploy

### Opzione 1: VPS (Hetzner, DigitalOcean, ecc.)
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
# Usa nginx come reverse proxy
```

### Opzione 2: Railway / Render (zero config)
```bash
# Aggiungi Procfile:
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
```

### Opzione 3: Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Roadmap (il 10% mancante 😄)

- [ ] Autenticazione utenti (JWT)
- [ ] Storage file su S3/Cloudflare R2 (invece che locale)
- [ ] Export report PDF
- [ ] Alert capital call in scadenza (email/notifiche)
- [ ] Multi-currency con conversione automatica
- [ ] API webhooks per aggiornamenti automatici
