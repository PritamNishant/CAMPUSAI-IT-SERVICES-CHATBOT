# CampusFix AI Admin System

## Architecture
Students and employees authenticate with the existing user JWT, chat through the existing frontend, and reach Flask at `http://localhost:5001`. Flask calls the existing Groq SDK integration. Unresolved IT conversations are escalated by the backend into MongoDB tickets. Administrators use separate JWTs and the pages under `admin/`.

## MongoDB
The existing `campusfix_ai` database is reused. Collections are `users`, `conversations`, `tickets`, `admins`, and `counters`. Ticket IDs use an atomic counter and the format `CF-YYYY-00001`.

Tickets include user identity fields, issue/category/priority, description and AI summary, conversation ID, status, department/team assignment, admin notes, timeline, location, and timestamps. Password hashes and API credentials are never returned by APIs.

## APIs
User APIs: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/chat/send`, `POST /api/tickets`, `POST /api/tickets/create`, `GET /api/tickets/my`, `GET /api/tickets/<ticket_id>`.

Admin APIs: `POST /api/admin/register`, `POST /api/admin/login`, `GET /api/admin/stats`, `GET /api/admin/tickets`, `GET /api/admin/tickets/<ticket_id>`, `PATCH /api/admin/tickets/<ticket_id>`, and `GET /api/admin/users`.

## Admin authentication
Set `ADMIN_REGISTRATION_CODE` in `.env`. Open `/admin/login.html`, use the same email/password form plus the protected registration form to create the first admin, then sign in. Admin tokens contain `role: admin`, expire after one day, and are required by every admin API.

## Ticket lifecycle
The backend creates a ticket automatically when an IT conversation reaches the fourth user turn and the latest unresolved response indicates the issue remains unresolved. Creation is deduplicated by user and conversation ID. The chatbot displays the actual ticket ID. Admins can assign a team/admin, change priority or status, add notes, and resolve/close tickets. Every update appends a timeline event. Users see current status and assignment in My Tickets.

## Run
```bash
source venv/bin/activate
python backend/app.py
python3 -m http.server 8000
```
Open `http://localhost:8000` or `http://localhost:8000/admin/login.html`.

## Testing
Run `python backend/test_complete_flow.py`. The implemented checks also cover automatic unresolved escalation, ticket persistence, admin lifecycle updates, timeline changes, and cross-user ticket isolation.

## Environment
Required existing values: `MONGO_URI`, `SECRET_KEY`, and `GROQ_API_KEY`. Admin bootstrap additionally requires `ADMIN_REGISTRATION_CODE`. Keep `.env` local and rotate credentials if they have ever been shared.
