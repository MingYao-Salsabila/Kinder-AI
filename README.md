# KinderAi

KinderAi is a Streamlit-based AI learning assistant for the **MajuBarengAi programme by Hacktiv8 with Google**.

It is organised around four screens:

- **Landing** -- an overview of the app, live status, and quick navigation.
- **Kid Mode** -- short, friendly, safety-checked answers grounded in a curated knowledge base, plus a quick quiz and a progress tracker.
- **Teacher Mode** -- classroom-ready explanations (Explanation / Example / Check for understanding) plus a downloadable quiz generator.
- **Admin Mode** -- conversation logs, learner progress, quiz attempts, configuration, and knowledge-base management.

## What this project is

KinderAi works **fully offline out of the box** -- with `GEMINI_USE_STUB=true` (the default), every mode runs with deterministic placeholder responses and a local TF-IDF knowledge base, no API key or network access required. Set a real `GEMINI_API_KEY` and `GEMINI_USE_STUB=false` to switch to live Gemini responses with no other code changes.

## Repository layout

```text
KinderAi/
├── README.md
├── KinderAi.md
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── Dockerfile
├── .dockerignore
├── Procfile
├── runtime.txt
├── pyproject.toml
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── app/
│   ├── main.py
│   ├── config.py
│   ├── modes/
│   │   ├── landing.py
│   │   ├── kid_mode.py
│   │   ├── teacher_mode.py
│   │   └── admin_mode.py
│   ├── core/
│   │   ├── router.py
│   │   ├── conversation.py
│   │   ├── providers/        # Gemini + offline stub, behind one interface
│   │   ├── rag/               # dependency-free TF-IDF retrieval
│   │   ├── quiz/               # LLM-backed quiz generation + offline fallback
│   │   ├── progress/           # scoring, levels, badges
│   │   ├── safety/             # kid-mode keyword screening
│   │   ├── speech/             # browser text-to-speech component
│   │   └── models/
│   ├── db/
│   │   ├── schema.sql
│   │   └── database.py
│   ├── data/
│   │   ├── knowledge_base/      # lesson notes (.md) used for retrieval
│   │   └── vector_index/        # generated index.json (not committed)
│   └── styles/
│       ├── shared.css
│       ├── kid_theme.css
│       └── teacher_theme.css
├── scripts/
│   ├── build_vector_index.py
│   └── seed_db.py
└── tests/
```

## Features

- **Real Gemini integration with an offline stub fallback.** `app/core/providers/` wraps the [`google-genai`](https://pypi.org/project/google-genai/) SDK behind a small `LLMProvider` interface. If `GEMINI_USE_STUB=true`, the key is missing/placeholder, or a live call errors, the app transparently falls back to a deterministic stub provider -- the UI still works, with a note explaining the fallback.
- **Retrieval over a local knowledge base.** `app/core/rag/` is a small, pure-Python/stdlib TF-IDF + cosine-similarity index over `app/data/knowledge_base/*.md`. No `chromadb`/`faiss`/embedding API required. Kid and Teacher mode ground their answers in matching lesson notes and show "Where this came from".
- **Interactive quizzes.** `app/core/quiz/` asks Gemini for JSON-formatted quiz questions (grounded in retrieved lesson notes) when live, and otherwise builds a true/false + multiple-choice + reflection quiz directly from the knowledge base. Kid Mode scores answers, awards badges, and shows balloons on a perfect score; Teacher Mode renders an answer key and a downloadable Markdown quiz sheet.
- **Learner progress tracking.** `app/db/database.py` records per-learner lesson completions, badges, and active days in SQLite. `app/core/progress/` turns that into a score and a friendly level ("Curious Seedling" → "KinderAi Champion"). Admin Mode shows progress and quiz history for every learner.
- **Browser-based read-aloud.** `app/core/speech/` renders a small HTML/JS widget using the browser's built-in `SpeechSynthesis` API -- no extra dependencies, no API key, works offline.
- **Mode-specific themes.** `app/styles/kid_theme.css` (warm, playful, chat-bubble alerts) and `teacher_theme.css` (calm paper palette with a notebook-margin accent) layer on top of `shared.css`.
- **Kid-safety keyword filter.** `app/core/safety/` screens Kid Mode prompts for self-harm, violence, sexual content, drugs/alcohol, and personal-information requests before anything is sent to a model.
- **Admin dashboard.** Conversation logs (with a "danger zone" to clear them), learner progress, quiz attempts, knowledge-base contents with a "rebuild index" action, and a configuration snapshot with live/stub status.

## Quick start

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

3. Copy `.env.example` to `.env`. The defaults run the app fully offline.

   ```bash
   cp .env.example .env
   ```

4. Run the app.

   ```bash
   streamlit run app/main.py
   ```

The database is created and seeded with demo data automatically on first run.

## Configuration

All configuration is read from environment variables (via `.env` locally, or your platform's environment/secrets in production). Relative paths are resolved against the project root, so the app behaves the same regardless of the working directory it's launched from.

| Variable | Default | Notes |
| --- | --- | --- |
| `APP_NAME` | `KinderAi` | Shown as the page title. |
| `APP_ENV` | `development` | Free-form label, shown in Admin Mode. |
| `DEFAULT_MODE` | `landing` | One of `landing`, `kid`, `teacher`, `admin`. Falls back to `landing` if invalid. |
| `GEMINI_API_KEY` | _(empty)_ | A real Gemini API key. Leave empty to stay in stub mode. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model used when live. |
| `GEMINI_USE_STUB` | `true` | Set to `false` to enable live Gemini calls (also requires a real key). |
| `GEMINI_MAX_OUTPUT_TOKENS` | `1024` | Upper bound on response length when live (minimum 128). |
| `SQLITE_PATH` | `app/db/kinderai.sqlite3` | Conversation logs, progress, quiz attempts, app settings. |
| `VECTOR_INDEX_PATH` | `app/data/vector_index` | Where `index.json` is written by the rebuild action / script. |
| `KNOWLEDGE_BASE_PATH` | `app/data/knowledge_base` | `.md`/`.txt` lesson notes used for retrieval. |

### Going live with Gemini

1. Get a key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. In `.env` (or your platform's secrets), set:

   ```dotenv
   GEMINI_API_KEY=your-real-key
   GEMINI_USE_STUB=false
   ```

3. Restart the app. Admin Mode's "Configuration snapshot" and the sidebar will show "Gemini: live" once a real key is detected. `settings.is_live` is `True` only when *both* `GEMINI_USE_STUB=false` *and* `GEMINI_API_KEY` is set to something other than a placeholder (`stub-gemini-api-key`, `your-gemini-api-key`, `changeme`, or empty).

If a live call fails for any reason (bad key, network error, safety block, rate limit), KinderAi automatically falls back to the offline stub for that turn and shows a short notice -- it never crashes the UI.

## Knowledge base & retrieval

`app/data/knowledge_base/` ships with six short lesson notes (plants & photosynthesis, the water cycle, the solar system, fractions, animal habitats, and states of matter). Each is a Markdown file starting with a `# Title` heading.

To add your own content, drop more `.md`/`.txt` files into that folder. The index is rebuilt automatically (in memory) the next time it's needed, or you can:

- Run `python -m scripts.build_vector_index` to persist `app/data/vector_index/index.json`, or
- Use the **"🔄 Rebuild & save index"** button in Admin Mode.

The index is plain JSON (vocabulary + IDF weights + per-document vectors) with no `numpy`/`scikit-learn` dependency at search time, so it's safe to inspect, persist, or omit entirely.

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

The test suite covers configuration, safety filtering, retrieval, quiz generation (live + fallback), the conversation service, providers, and all database operations -- all using temporary directories, so it never touches your real `.env` or database.

## Deployment

KinderAi works fully offline, so the simplest deployments need **no secrets at all**. Add `GEMINI_API_KEY` / `GEMINI_USE_STUB=false` to any of the options below to go live.

### Streamlit Community Cloud

1. Push this repository to GitHub.
2. Create a new app pointing at `app/main.py`.
3. (Optional, for live Gemini) Open **Settings → Secrets** and paste the contents of `.streamlit/secrets.toml.example` with a real key. Streamlit exposes secrets as environment variables, so `app/config.py` picks them up automatically.
4. `.streamlit/config.toml` (committed) sets the theme and disables usage-stats collection.

### Docker

```bash
docker build -t kinderai .
docker run --rm -p 8501:8501 --env-file .env kinderai
```

The image runs as a non-root user and exposes a healthcheck at `/_stcore/health`.

### Render / Railway / Heroku-style platforms

`Procfile` and `runtime.txt` are included:

```
web: streamlit run app/main.py --server.port=$PORT --server.address=0.0.0.0
```

Set `GEMINI_API_KEY` and `GEMINI_USE_STUB=false` as environment variables in the platform's dashboard for live mode.

### Filesystem notes

SQLite (`SQLITE_PATH`) and the optional vector index (`VECTOR_INDEX_PATH`) are written at runtime. On platforms with a read-only filesystem outside of a specific volume, point these at a writable path (e.g. `/tmp` or a mounted volume) via environment variables. If persisting the index fails, Admin Mode falls back to an in-memory index automatically.

## Data and persistence

SQLite (`SQLITE_PATH`) stores:

- conversation logs (`conversations`)
- per-learner progress (`learner_progress`)
- quiz attempts (`quiz_attempts`)
- app settings, including a one-time demo-seed flag (`app_settings`)

`scripts/seed_db.py` re-runs the same idempotent demo seeding used on first launch.

## Security notes

- Never commit real API keys; `.env` and `.streamlit/secrets.toml` are both gitignored.
- Use your platform's secret manager in production (Streamlit Cloud secrets, Docker `--env-file`, etc.).
- Rotate credentials if a key is ever exposed.
- The Kid Mode keyword filter (`app/core/safety/`) is a fast first line of defense, not a substitute for the underlying model's own safety behaviour.

## Troubleshooting

**Streamlit will not start.** Confirm the virtual environment is active and `pip install -r requirements.txt` completed without errors.

**Sidebar shows "Gemini: offline stub" even though I set a key.** Check that `GEMINI_USE_STUB=false` *and* `GEMINI_API_KEY` is a real key (not `stub-gemini-api-key`/`your-gemini-api-key`/`changeme`). Both conditions are required.

**`google-genai` import errors.** The package is optional at runtime -- if it's missing, KinderAi just uses the stub provider. Run `pip install -r requirements.txt` to install it.

**Empty data views in Admin Mode.** Run `python scripts/seed_db.py`, or just use the app once (the database is seeded automatically on first run).

**Knowledge base changes aren't showing up.** If `app/data/vector_index/index.json` exists, it takes priority over a fresh in-memory build. Click "🔄 Rebuild & save index" in Admin Mode, or delete `index.json` to force a rebuild from the current `.md` files.

**`ImportError: Unable to import required dependency numpy` (common on Windows).** This means the `numpy`/`pandas` pair installed in your virtual environment is broken or mismatched (a corrupted wheel, antivirus quarantining a DLL, or a stale install left over from another project reusing the same venv) -- it is an environment issue, not a code bug. KinderAi itself never imports `pandas`/`numpy` directly (`st.dataframe` accepts plain Python lists/dicts); they are only present as transitive dependencies of Streamlit. Fix it with a clean reinstall:

```bash
pip uninstall -y numpy pandas
pip install --no-cache-dir --force-reinstall -r requirements.txt
```

If that doesn't resolve it, delete the virtual environment entirely and recreate it (`python -m venv .venv` again) -- this is the most reliable fix for a corrupted Windows install.

## Changelog

### 2.0.1
- Removed the direct `pandas` import from Admin Mode (`st.dataframe` now receives plain Python lists of dicts) and dropped the unpinned `pandas`/`numpy` entries from `requirements.txt`. They're still installed transitively by Streamlit, but Streamlit now owns the version pin instead of a separate, unpinned spec from this project -- this avoids a binary ABI mismatch between independently-resolved pandas/numpy versions (`ImportError: Unable to import required dependency numpy`), a common failure on Windows.
- Fixed a crash when navigating from the Landing page buttons ("Try Kid Mode", etc.): writing to the sidebar radio's own session-state key after it was instantiated raised `StreamlitAPIException`. Navigation now goes through a separate staging key consumed before the radio widget is created.

### 2.0.0
- Real Gemini provider (`google-genai`) behind a small `LLMProvider` interface, with automatic, graceful fallback to an offline stub.
- Dependency-free TF-IDF retrieval over a new knowledge base of six lesson notes; Kid/Teacher Mode are now grounded and show sources.
- LLM-backed quiz generation with an offline fallback; interactive scoring, badges, and balloons in Kid Mode; downloadable quiz sheets in Teacher Mode.
- Learner progress tracking (lessons, badges, active days, levels) backed by new SQLite tables and surfaced in Kid and Admin Mode.
- Browser-based text-to-speech ("Read it to me") with no extra dependencies.
- Distinct Kid/Teacher visual themes; Admin dashboard expanded with progress, quiz history, knowledge-base management, and a conversation-log danger zone.
- Fixed a Streamlit deprecation (`use_container_width` → `width`, `components.v1.html` → `st.iframe`) and a `datetime.utcnow()` deprecation.
- Added Docker, `.streamlit/config.toml`, `Procfile`, `runtime.txt`, and a `requirements-dev.txt` + pytest suite (50 tests).
- Trimmed unused dependencies (`chromadb`, `faiss-cpu`, `anthropic`, `openai`, `pydantic`).

### 1.1.0
- Improved repository documentation.
- Added structured configuration and Gemini stubbing.
- Replaced placeholders with a working Streamlit skeleton.
- Added SQLite helpers and safer mode routing.

### 1.0.0
- Initial project skeleton.
