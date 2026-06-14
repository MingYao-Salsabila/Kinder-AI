# KinderAi

KinderAi is a Streamlit-based AI learning assistant for the **MajuBarengAi programme by Hacktiv8 with Google**.

It is organised around three user-facing modes:

- **Kid Mode** for guided, child-friendly learning.
- **Teacher Mode** for lesson planning and classroom support.
- **Admin Mode** for supervision, logs, and configuration review.

## What this project is

This repository is a clean starter architecture for a safe educational assistant. It is designed to stay simple enough for a hackathon prototype while still leaving room for proper growth into retrieval, quizzes, speech, and progress tracking.

## Repository layout

```text
KinderAi/
├── README.md
├── KinderAi.md
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── modes/
│   │   ├── __init__.py
│   │   ├── landing.py
│   │   ├── kid_mode.py
│   │   ├── teacher_mode.py
│   │   └── admin_mode.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── conversation.py
│   │   ├── models/
│   │   ├── speech/
│   │   ├── rag/
│   │   ├── quiz/
│   │   ├── safety/
│   │   └── progress/
│   ├── db/
│   │   ├── __init__.py
│   │   ├── schema.sql
│   │   └── database.py
│   └── styles/
│       ├── kid_theme.css
│       ├── teacher_theme.css
│       └── shared.css
└── scripts/
    ├── build_vector_index.py
    └── seed_db.py
```

## Features

- Mode-based UI with a shared backend
- Safe Gemini API key stubbing through environment variables
- SQLite-backed conversation logs and demo progress records
- Simple safety filtering for child-facing prompts
- Placeholder retrieval, quiz, and progress modules ready for future expansion

## Setup

1. Create and activate a virtual environment.

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

2. Install dependencies.

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`.

   ```bash
   copy .env.example .env
   ```

4. Edit `.env` and keep the Gemini API key as a stub unless you later wire a real provider.

5. Run the app.

   ```bash
   streamlit run app/main.py
   ```

## Configuration

The project reads configuration from environment variables:

- `APP_NAME`
- `APP_ENV`
- `DEFAULT_MODE`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GEMINI_USE_STUB`
- `SQLITE_PATH`
- `VECTOR_INDEX_PATH`

### Gemini key stub

This project intentionally uses a stub by default:

```dotenv
GEMINI_API_KEY=stub-gemini-api-key
GEMINI_USE_STUB=true
```

That lets the app run without a real secret while keeping the code ready for a later integration.

## Running the app

The default entry point is:

```bash
streamlit run app/main.py
```

Inside the app, use the sidebar to switch between modes.

## Data and persistence

The app uses SQLite for lightweight local persistence:

- conversation logs
- demo learner progress
- mode settings

The database file path is controlled by `SQLITE_PATH` in `.env`.

## Security notes

- Never commit real API keys.
- Keep `.env` out of version control.
- Use a secret manager in production.
- Rotate credentials if a key is ever exposed.
- Keep child-facing answers behind safety checks.

## Development notes

The code has been reorganised into small modules so each concern has one place:

- configuration in `app/config.py`
- routing in `app/core/router.py`
- response generation in `app/core/conversation.py`
- database access in `app/db/database.py`
- UI screens in `app/modes/`

## Future improvements

Recommended next steps after this starter:

- replace the Gemini stub with a real provider adapter
- add real retrieval over curated lesson documents
- connect speech input and output
- store richer learner progress metrics
- add tests for the conversation and database layers

## Troubleshooting

### Streamlit will not start
Check that the virtual environment is active and the dependencies installed correctly.

### Missing configuration
If the app warns about configuration, confirm that `.env` exists and includes the required keys.

### Empty data views
Run `python scripts/seed_db.py` to populate demo rows.

## Changelog

### 1.1.0
- Improved repository documentation
- Added structured configuration and Gemini stubbing
- Replaced placeholders with a working Streamlit skeleton
- Added SQLite helpers and safer mode routing

### 1.0.0
- Initial project skeleton
