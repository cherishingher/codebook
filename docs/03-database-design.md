# Database Design

Primary tables:

- `campuses`
- `users`
- `user_roles`
- `students`
- `guardian_student_relations`
- `teachers`
- `courses`
- `lessons`
- `lesson_students`
- `face_profiles`
- `devices`
- `punch_events`
- `attendance_records`
- `hour_accounts`
- `hour_ledgers`
- `deduction_rules`
- `notifications`
- `operation_logs`

Critical constraints:

- `lesson_students` has one row per lesson and student.
- `attendance_records` has one row per lesson and student.
- `punch_events` is idempotent by device and local event id.
- `hour_accounts.balance_hours` can only change through `hour_ledgers`.

