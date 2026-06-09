# Codebook

Codebook is a local-first campus attendance and lesson-hour management system.

The first deployment target is a Mac mini with one USB camera. The Mac runs the
camera recognition agent, backend API, PostgreSQL database, scheduled jobs, and
Nginx HTTPS entrypoint. A WeChat Mini Program provides learner, teacher, and
campus administrator views.

## Modules

- `backend/` - FastAPI backend for campuses, users, lessons, attendance, hour ledgers, devices, and notifications.
- `camera-agent/` - Local USB camera agent for face enrollment, recognition, device heartbeat, and punch event upload.
- `miniprogram/` - WeChat Mini Program scaffold for learner, teacher, and campus roles.
- `deploy/` - Mac mini deployment assets for Nginx and launchd.
- `docs/` - Product and technical design notes.

## MVP Scope

- One Mac mini and one USB camera.
- Data model supports multiple campuses; first deployment can use one campus.
- Manual lesson creation by campus admins or teachers.
- Face recognition creates punch events.
- Punch events match lessons and produce attendance records.
- Attendance rules produce hour ledgers.
- Learners and guardians can view schedule, deduction status, and remaining hours.
- Teachers can confirm attendance.
- Campus admins can manage students, teachers, lessons, hour accounts, rules, and devices.

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
codebook-init-db
uvicorn app.main:app --reload
```

Run `codebook-init-db` after pulling backend updates in a deployed environment.
It is idempotent and creates newly added tables such as device nonce tracking
without dropping existing data.

Camera agent:

```bash
cd camera-agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m agent.main
```
