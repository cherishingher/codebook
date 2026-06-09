# API Design

Base prefix:

```text
/api/v1
```

Groups:

- `/auth`: WeChat login and role switching.
- `/learner`: schedule, lesson detail, hour accounts, and hour ledgers.
- `/teacher`: teacher dashboard, lessons, and attendance confirmation.
- `/campus`: campus dashboard, students, teachers, courses, lessons, rules, and devices.
- `/device`: heartbeat, face profile sync, and punch events.
- `/exports`: attendance and hour ledger exports.

Device punch upload:

```http
POST /api/v1/device/punch-events
```

The backend must verify device identity, deduplicate by local event id, match a
lesson, create or reuse attendance, and apply deduction rules in one controlled
business flow.

