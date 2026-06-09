# Product Requirements

## Goal

Codebook is a local-first smart attendance and lesson-hour management system for
campus scenarios. A Mac mini with a USB camera performs local face recognition.
The backend records attendance, lesson status, and hour ledgers. A WeChat Mini
Program lets learners, guardians, teachers, and campus administrators view and
manage their permitted data.

## Roles

- Learner viewer: students and guardians share the same learner-side pages.
- Teacher: manages own lessons and confirms attendance.
- Campus admin: manages one campus.
- Super admin: manages cross-campus operations.
- Device: the Mac mini camera agent.

## Core Flow

1. Campus admin creates students, teachers, courses, and hour accounts.
2. Teacher or campus admin creates a lesson and assigns students.
3. Student appears in front of the USB camera.
4. Camera agent recognizes the student and uploads a punch event.
5. Backend matches the punch event to an active lesson.
6. Backend creates attendance and applies deduction rules.
7. Backend writes an hour ledger and updates the hour account.
8. Learner, teacher, and campus pages show the same result within their scope.

## MVP

- One Mac mini.
- One USB camera.
- Manual lesson creation.
- Face recognition punch events.
- Configurable deduction rules.
- Learner schedule and hour ledger views.
- Teacher attendance confirmation.
- Campus student, lesson, rule, and device management.

