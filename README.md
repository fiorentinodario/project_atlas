# ProjectAtlas

ProjectAtlas è una piattaforma di gestione e conoscenza dei progetti basata sull'intelligenza artificiale. Riunisce documenti, attività, decisioni e analisi assistite dall'AI in un unico spazio di lavoro, permettendo ai team di porre domande fondate sui dati dei propri progetti.

Il repository è sviluppato come progetto portfolio con attenzione ad architettura, autorizzazione sicura, affidabilità delle funzionalità AI, test automatici e interfaccia responsive professionale.

## Funzionalità previste per l'MVP

- Autenticazione tramite email e password
- Spazi di lavoro con controllo degli accessi basato sulla proprietà
- Gestione di attività, documenti e decisioni progettuali
- Acquisizione di documenti PDF, testo e Markdown
- Domande e risposte basate su RAG con citazione delle fonti
- Analisi strutturata del progetto e suggerimenti di attività tramite AI
- Registro attività e riepiloghi nella dashboard

## Stack tecnologico

| Livello | Tecnologia |
| --- | --- |
| Frontend | React, TypeScript, Tailwind CSS, Vite |
| Backend | Python, Flask |
| Database | PostgreSQL con pgvector |
| AI | Interfacce indipendenti dal provider, inizialmente OpenAI |
| Infrastruttura | Docker Compose, GitHub Actions |

## Struttura del repository

```text
project-atlas/
├── backend/            # API REST Flask, dal Milestone 2
├── frontend/           # Applicazione React
├── docs/
│   └── architecture.md # Decisioni tecniche e architettura in evoluzione
├── .gitignore
└── README.md
```

## Architettura

Il client React comunicherà con un'API REST Flask versionata. Il backend gestirà autenticazione, autorizzazione, regole applicative, acquisizione dei documenti e orchestrazione AI. PostgreSQL conserverà i dati applicativi, mentre pgvector manterrà gli embedding vicini ai metadati e ai dati transazionali del progetto.

Le responsabilità AI saranno separate in servizi di acquisizione, embedding, recupero, costruzione dei prompt e generazione. Questa divisione rende i provider sostituibili, permette test deterministici e mantiene utilizzabili le funzionalità non AI durante eventuali indisponibilità del provider.

Consulta [docs/architecture.md](docs/architecture.md) per il piano architetturale corrente.

## Stato dello sviluppo

- Milestone 0: struttura del repository e pianificazione architetturale completate.
- Milestone 1: base frontend responsive implementata con dashboard dimostrativa e routing.
- Milestone 2: fondazione API Flask con configurazione per ambiente, health check, CORS e gestione uniforme degli errori.
- Milestone 3: modello relazionale PostgreSQL con SQLAlchemy e migrazione iniziale Alembic.
- Milestone 4: autenticazione email/password, JWT con refresh rotation, logout e route frontend protette.
- Milestone 5: CRUD progetti, autorizzazione per membership e workspace frontend.
- Milestone 6: gestione task con ricerca, filtri, Kanban e activity log.
- Milestone 7: upload documenti, storage privato, estrazione testuale e stati di elaborazione.
- Milestone 8: chunking offline, embedding sostituibili, pgvector e ricerca semantica con fonti.
- Milestone 9: assistente AI contestuale con RAG, cronologia breve e provider LLM sostituibile.
- Milestone 10: citazioni verificabili con documento, pagina, estratto e riferimento al chunk.

Progetti, task e documenti usano dati persistenti tramite API. La ricerca semantica richiede un provider di embedding configurato; in sua assenza il resto dell'applicazione continua a funzionare.

## Sviluppo locale

Prerequisiti frontend: Node.js 22 e npm 10 o versioni compatibili.

```bash
cd frontend
npm install
npm run dev
```

Controlli di qualità disponibili:

```bash
npm run typecheck
npm run lint
npm test
npm run build
```

Prerequisito backend: Python 3.11 o versione compatibile successiva.

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
flask --app wsgi db upgrade
flask --app wsgi run --debug
```

L'health endpoint sarà disponibile su `http://localhost:5000/api/v1/health`.

Controlli di qualità backend:

```bash
ruff check .
ruff format --check .
pytest
```

La variabile `DATABASE_URL` deve puntare a un'istanza PostgreSQL accessibile. Lo schema non viene creato automaticamente all'avvio: ogni modifica passa attraverso migrazioni versionate.

## Sicurezza

Secret e file di ambiente locali non devono essere aggiunti al repository. Gli endpoint convalidano gli input sul server; i futuri endpoint di progetto, caricamento e AI applicheranno anche l'autorizzazione per ogni risorsa.

L'autenticazione usa access token brevi conservati soltanto in memoria e refresh token in cookie `HttpOnly` protetti da CSRF. Nel database viene salvato soltanto l'hash dell'identificatore del refresh token. In produzione i cookie richiedono HTTPS e l'applicazione rifiuta l'avvio con secret predefiniti.

Endpoint disponibili:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me

GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/:projectId
PATCH  /api/v1/projects/:projectId
DELETE /api/v1/projects/:projectId

GET    /api/v1/projects/:projectId/tasks
POST   /api/v1/projects/:projectId/tasks
PATCH  /api/v1/tasks/:taskId
DELETE /api/v1/tasks/:taskId

GET    /api/v1/projects/:projectId/documents
POST   /api/v1/projects/:projectId/documents
DELETE /api/v1/documents/:documentId
POST   /api/v1/documents/:documentId/index
POST   /api/v1/projects/:projectId/search
POST   /api/v1/projects/:projectId/assistant/messages
```

I documenti supportati sono PDF, TXT e Markdown, fino a 10 MB. I file vengono conservati fuori dal controllo versione con nomi generati, mentre il database mantiene metadati, testo estratto e stato di elaborazione.

Per abilitare gli embedding OpenAI nel file `backend/.env`:

```dotenv
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=la-tua-chiave
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
LLM_PROVIDER=openai
LLM_MODEL=gpt-5-mini
```

Il valore predefinito `EMBEDDING_PROVIDER=disabled` non effettua chiamate esterne. I documenti vengono comunque estratti e suddivisi in chunk, mentre la ricerca semantica risponde esplicitamente che il servizio AI non è configurato.

Le risposte dell'assistente distinguono il testo generato dai metadati delle fonti. Le citazioni mostrate dall'interfaccia derivano direttamente dai chunk recuperati dal database e non da riferimenti liberamente generati dal modello.

Le liste dei progetti sono paginate. Gli utenti esterni a un progetto ricevono una risposta `404`, mentre le operazioni di modifica e cancellazione applicano i ruoli della membership sul server.

## Licenza

La licenza non è ancora stata scelta.
