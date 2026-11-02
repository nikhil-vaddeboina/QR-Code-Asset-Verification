# Quick code map for the team

Open the file that matches the feature you are explaining:

| What to present | Main file | Related file/page |
|---|---|---|
| Flask startup and blueprint registration | `app.py` | `START_ASSETVERIFY.bat` |
| Asset add/list/edit/delete and bulk upload | `back/features/assets/routes.py` | `back/features/assets/service.py` |
| QR image generation, save and retrieval | `back/features/assets/qr.py` | `back/models/asset.py` |
| Login, password change/reset, MFA | `back/features/authentication/routes.py` | `back/models/user.py` |
| Technician account CRUD and permissions | `back/features/team/routes.py` | `back/features/access/permissions.py` |
| Dashboard summary | `back/features/dashboard/routes.py` | `front/templates/dashboard/index.html` |
| QR scan and verification | `back/features/verification/routes.py` | `back/features/verification/service.py` |
| Verification history | `back/features/history/routes.py` | `front/templates/history/index.html` |
| Database entities/tables | `back/models/` | `back/database/schema.sql` |
| Asset pages | `front/templates/assets/` | `front/static/css/shared/` |
| Sign-in and MFA pages | `front/templates/authentication/` | `front/static/js/shared/` |
| Camera scanner | `front/templates/verification/scan.html` | `front/static/js/verification/scanner.js` |
| Project architecture | `docs/ARCHITECTURE.md` | `README.md` |

## Simple explanation for the mentor

“Each feature has its own folder. The frontend folder contains the screens and browser scripts. The backend feature folder contains the Flask routes and the logic for that feature. Shared database models are kept in one place. This makes the code easier for each team member to find and explain.”