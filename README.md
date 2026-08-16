# ProjectAtlas

ProjectAtlas è una piattaforma di gestione e conoscenza dei progetti basata sull'intelligenza artificiale. Riunisce documenti, attività, decisioni e analisi assistite dall'AI in un unico spazio di lavoro, permettendo ai team di porre domande fondate sui dati dei propri progetti.

Il repository è sviluppato come progetto portfolio con attenzione ad architettura, autorizzazione sicura, affidabilità delle funzionalità AI, test automatici e interfaccia responsive professionale.

## Funzionalità dell'MVP

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

Il client React comunica con un'API REST Flask versionata. Il backend gestisce autenticazione, autorizzazione, regole applicative, acquisizione dei documenti e orchestrazione AI. PostgreSQL conserva i dati applicativi, mentre pgvector mantiene gli embedding vicini ai metadati e ai dati transazionali del progetto.

Le responsabilità AI sono separate in servizi di acquisizione, embedding, recupero, costruzione dei prompt e generazione. Questa divisione rende i provider sostituibili, permette test deterministici e mantiene utilizzabili le funzionalità non AI durante eventuali indisponibilità del provider.

Consulta [docs/architecture.md](docs/architecture.md) per l'architettura e [docs/security.md](docs/security.md) per il threat model e i rischi residui.

## Screenshot

Per evitare immagini dimostrative non corrispondenti al prodotto, gli screenshot devono essere acquisiti dall'app avviata con dati demo reali. Dopo `docker compose up --build`, cattura almeno dashboard, workspace, assistente con fonti e analisi AI in `docs/screenshots/` e collegali qui prima della pubblicazione definitiva del repository.

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
- Milestone 11: decisioni manuali, rilevamento AI con fonti e conferma umana obbligatoria.
- Milestone 12: analisi AI strutturata con riepilogo, requisiti, rischi, domande e task suggeriti.
- Milestone 13: selezione dei suggerimenti e creazione atomica di task AI tracciabili.
- Milestone 14: dashboard con statistiche aggregate, progetti recenti e activity feed.
- Milestone 15: copertura di integrazione ampliata e hardening delle risposte HTTP.
- Milestone 16: container Docker per frontend, backend e PostgreSQL/pgvector.
- Milestone 17: pipeline GitHub Actions per lint, test, build e immagini container.
- Milestone 18: audit responsive/accessibilità e documentazione portfolio completata.

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

## Avvio con Docker

Crea un file `.env` nella radice con due secret casuali e, facoltativamente, la chiave OpenAI:

```dotenv
SECRET_KEY=un-secret-lungo-e-casuale
JWT_SECRET_KEY=un-secondo-secret-lungo-e-casuale
OPENAI_API_KEY=
EMBEDDING_PROVIDER=disabled
LLM_PROVIDER=disabled
```

Avvia l'intero stack:

```bash
docker compose up --build
```

L'applicazione sarà disponibile su `http://localhost:8080`. Il backend applica automaticamente le migrazioni prima di avviare Gunicorn. PostgreSQL e i documenti caricati usano volumi persistenti.

## Sicurezza

Secret e file di ambiente locali non devono essere aggiunti al repository. Gli endpoint convalidano gli input sul server e applicano l'autorizzazione a ogni risorsa di progetto.

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

GET    /api/v1/projects/:projectId/decisions
POST   /api/v1/projects/:projectId/decisions
POST   /api/v1/projects/:projectId/decisions/detect
PATCH  /api/v1/decisions/:decisionId
DELETE /api/v1/decisions/:decisionId
POST   /api/v1/decisions/:decisionId/confirm
POST   /api/v1/decisions/:decisionId/reject

GET    /api/v1/projects/:projectId/analyses/latest
POST   /api/v1/projects/:projectId/analyses
POST   /api/v1/analyses/:analysisId/tasks
GET    /api/v1/dashboard
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

Le decisioni inserite manualmente sono fatti confermati. Quelle rilevate nei documenti dall'AI vengono invece salvate come proposte in attesa: entrano nel contesto fattuale dell'assistente soltanto dopo una conferma esplicita dell'utente.

L'analisi AI produce dati strutturati e validati per riepilogo, requisiti, rischi, domande aperte e task suggeriti. I riferimenti indicati dal modello vengono risolti dal backend contro i chunk realmente recuperati prima che l'analisi venga salvata.

I task suggeriti possono essere selezionati e creati in un'unica operazione atomica. Ogni task mantiene l'origine `AI_GENERATED`, l'analisi sorgente e l'indice del suggerimento; un vincolo del database impedisce conversioni duplicate.

Le liste dei progetti sono paginate. Gli utenti esterni a un progetto ricevono una risposta `404`, mentre le operazioni di modifica e cancellazione applicano i ruoli della membership sul server.

## Qualità e CI

La pipeline GitHub Actions esegue Ruff, pytest con coverage, typecheck TypeScript, ESLint, Vitest, build Vite e build delle immagini Docker. I test AI utilizzano provider deterministici e non effettuano chiamate esterne.

## Limiti consapevoli

- L'elaborazione documentale è sincrona; un worker asincrono è il passo naturale per carichi elevati.
- La cronologia della chat vive nella sessione browser e non viene ancora persistita.
- Non è presente un sistema di inviti: il modello dati supporta i ruoli, mentre la gestione membri è una futura estensione.
- Le chiamate AI dipendono dal provider configurato; tutte le funzioni non AI rimangono disponibili durante eventuali indisponibilità.

## Licenza

Distribuito con licenza MIT. Consulta [LICENSE](LICENSE).
