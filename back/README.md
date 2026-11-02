# Backend

Backend code is grouped by the feature it serves.

- `features/assets/` — asset pages/routes, validation and search service, QR creation/storage.
- `features/authentication/` — sign-in, sign-out, password reset/change and MFA.
- `features/access/` — administrator and technician permission checks.
- `features/team/` — technician create/list/update-access/delete operations.
- `features/dashboard/`, `features/history/`, `features/verification/` — their routes and feature logic.
- `features/demo/` — demo data setup.
- `models/` — SQLAlchemy database entities.
- `database/` and `config/` — reference SQL files and settings documentation.

The root `app.py` creates the Flask app, registers each feature blueprint, and provides database setup commands. Keep `.env`, `requirements.txt`, and the Windows launcher beside it.