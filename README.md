# ProjectAtlas

ProjectAtlas is an AI-powered project knowledge and management platform. It brings project documents, tasks, decisions, and AI-assisted analysis into a single workspace so teams can ask questions grounded in their own project data.

This repository is being built as a production-minded portfolio project, with an emphasis on clear architecture, secure authorization, reliable AI behavior, automated testing, and a polished responsive interface.

## Planned MVP Features

- Email and password authentication
- Project workspaces with ownership-based access control
- Task, document, and project-decision management
- PDF, text, and Markdown document ingestion
- Retrieval-augmented project Q&A with source citations
- Structured AI project analysis and task suggestions
- Activity tracking and dashboard summaries

## Planned Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Tailwind CSS |
| Backend | Python, Flask |
| Database | PostgreSQL with pgvector |
| AI | Provider-agnostic interfaces, initially backed by OpenAI |
| Infrastructure | Docker Compose, GitHub Actions |

## Repository Structure

```text
project-atlas/
├── backend/            # Flask REST API (introduced in Milestone 2)
├── frontend/           # React application (introduced in Milestone 1)
├── docs/
│   └── architecture.md # Evolving technical decisions and system design
├── .gitignore
└── README.md
```

The application code will be introduced in focused milestones. Empty tracked directories currently mark the intended monorepo boundaries without prematurely selecting implementation details.

## Architecture

The React client will communicate with a versioned Flask REST API. The backend will own authentication, authorization, business rules, document ingestion, and AI orchestration. PostgreSQL will store application data, while pgvector will keep embeddings close to document metadata and transactional project data.

AI concerns will be separated into ingestion, embedding, retrieval, prompt construction, and generation services. This keeps providers replaceable, enables deterministic tests with fakes, and ensures non-AI features remain usable during provider outages.

See [docs/architecture.md](docs/architecture.md) for the current architectural plan.

## Development Status

Milestone 0 establishes repository structure and architecture only. Application setup begins in Milestone 1 after the initial commit is reviewed and pushed.

## Local Development

Setup instructions will be added alongside each runnable application layer so the documentation remains accurate to the implemented system.

## Security

Secrets and local environment files must never be committed. Future authentication, upload, and AI endpoints will validate inputs and enforce project-level authorization on the server.

## License

A license has not yet been selected.

