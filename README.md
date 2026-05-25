# CogniFlow PPST

A Django web application for administering the **Philadelphia Pointing Span Test (PPST)**, a neuropsychological assessment tool. Built as the senior capstone project for CS 04400 at Rowan University.

## Tech Stack

- **Backend:** Django 6.0.3
- **Database:** SQLite
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Audio:** Web Speech API (text-to-speech for stimulus presentation)
- **Email:** Gmail SMTP via App Password (for password reset flow)
- **Config:** python-dotenv

## Prerequisites

- Python 3.10+
- `pip` and `venv`
- A Gmail account with 2FA enabled and an App Password generated (only needed if you want the password reset emails to actually send — otherwise the flow falls back to console output)

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/Senior-Year-Project-Team/demo-repository.git
cd demo-repository

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file (see "Environment Variables" below)
touch .env

# 5. Run migrations
python manage.py migrate

# 6. Create a superuser (optional, for admin access)
python manage.py createsuperuser

# 7. Start the dev server
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.

## Environment Variables

Create a `.env` file in the project root with the following:

```
GMAIL_USER=your.email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
```

If `.env` is missing or `python-dotenv` isn't installed, the app falls back to Django's console email backend (reset emails will print to your terminal instead of sending).

> **Note:** `.env` and `db.sqlite3` are gitignored. Never commit credentials.

## Project Structure

```
demo-repository/
├── config/              # Django project config (settings, wsgi, urls)
├── ppst/                # Main app
│   ├── templates/ppst/  # HTML templates (including branded password reset emails)
│   ├── static/          # JS, CSS, audio assets
│   └── ...
├── venv/                # Virtual environment (gitignored)
├── .env                 # Local credentials (gitignored)
├── db.sqlite3           # Local database (gitignored)
├── manage.py
└── requirements.txt
```

## Creating a Test User Manually

If your local database resets, you can recreate a clinician account via the Django shell:

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from ppst.models import Clinician

u = User.objects.create_user(
    username="yourname@gmail.com",
    email="yourname@gmail.com",
    password="your_password"
)
Clinician.objects.create(user=u, institution="")
```

## Verifying SMTP Works

From the Django shell:

```python
from django.core.mail import send_mail
send_mail(
    "Test from CogniFlow",
    "If you see this, SMTP works.",
    None,  # Uses DEFAULT_FROM_EMAIL
    ["your.email@gmail.com"],
)
```

## Git Workflow

- **Never commit directly to `main`.** Always work on a feature branch.
- Branch naming convention: `yourname/feature-description` (e.g., `ivan/fixes`)

```bash
git checkout main
git pull
git checkout -b yourname/your-feature
# ... make changes ...
git add .
git commit -m "Descriptive message"
git push -u origin yourname/your-feature
```

Then open a pull request against `main`.

## Key Configuration Notes

- `PASSWORD_RESET_TIMEOUT = 3600` (1 hour) — matches Google's benchmark for reset link expiry
- Pending patient session links have a separate 48-hour expiry window
- CSRF protection and session/link expiry address distinct threat models (don't conflate them)

## Team

- Harrison Springer (Lead)
- Ivan Hennessey
- Connor Bolton
- Ismael Ortiz
- Srinath Reddy
- Lalit Sharma

**Advisor:** Dr. Baliga

## License

Academic project — Rowan University, CS 04400.
