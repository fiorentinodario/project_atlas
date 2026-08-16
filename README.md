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

Le funzionalità mostrate nella dashboard usano attualmente dati mock. Persistenza e autenticazione saranno introdotte nei rispettivi milestone.

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
npm run build
```

Prerequisito backend: Python 3.11 o versione compatibile successiva.

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
flask --app wsgi run --debug
```

L'health endpoint sarà disponibile su `http://localhost:5000/api/v1/health`.

Controlli di qualità backend:

```bash
ruff check .
ruff format --check .
pytest
```

## Sicurezza

Secret e file di ambiente locali non devono essere aggiunti al repository. I futuri endpoint di autenticazione, caricamento e AI convalideranno gli input e applicheranno sul server l'autorizzazione per ogni progetto.

## Licenza

La licenza non è ancora stata scelta.
