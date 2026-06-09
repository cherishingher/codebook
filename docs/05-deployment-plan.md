# Mac mini Deployment Plan

## Network

- Point a domain such as `api.example.com` to the campus public IP.
- Forward only port `443` from the router to the Mac mini.
- Keep PostgreSQL and backend ports bound to localhost.
- Configure the WeChat Mini Program legal request domain to the HTTPS domain.

## Storage

Recommended external disk layout:

```text
/Volumes/AttendanceData/storage/
  backups/
  snapshots/
  enrollments/
  exports/
  logs/
```

Database primary storage should stay on the internal disk. The external disk is
for backups and large files.

## Services

- Nginx for HTTPS.
- FastAPI backend through launchd.
- Camera agent through launchd.
- PostgreSQL as local database.
- Scheduled backup script.

