# Technical Architecture

## Components

- WeChat Mini Program: learner, teacher, and campus admin views.
- Nginx: HTTPS entrypoint on the Mac mini.
- FastAPI backend: business API and device API.
- PostgreSQL: source of truth for users, lessons, attendance, and hour ledgers.
- Camera agent: USB camera capture, face recognition, deduplication, and punch upload.
- External disk: snapshots, exports, logs, and backups.

## Deployment Shape

```mermaid
flowchart LR
  Camera["USB camera"] --> Agent["Mac mini camera agent"]
  Agent --> API["FastAPI backend"]
  Mini["WeChat Mini Program"] --> Nginx["Nginx HTTPS"]
  Nginx --> API
  API --> DB["PostgreSQL"]
  API --> Disk["External disk"]
```

## Principles

- Punch events are camera facts.
- Attendance records are lesson business results.
- Hour ledgers are the only reason balances change.
- All balance changes must be transactional.
- All manual changes must create operation logs.

