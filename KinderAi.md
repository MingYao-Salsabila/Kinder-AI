# KinderAi

KinderAi is a Streamlit-based AI learning assistant for the **MajuBarengAi programme by Hacktiv8 with Google**.

It uses one shared backend with three front-line modes:

- **Kid Mode**: playful, visual, guided learning.
- **Teacher Mode**: lesson planning, explanation, worksheet generation, classroom support.
- **Admin Mode**: supervision, safety controls, logs, and progress review.

## Product goal

Build a safe, modular, bilingual-ready learning assistant that can support children and educators with:
- simple question answering,
- curated knowledge retrieval,
- voice interaction,
- quiz generation,
- image understanding,
- progress tracking,
- admin supervision.

## Core principles

- One shared backend.
- Separate mode-specific UIs.
- Curated content for child-facing answers.
- Teacher mode for open-ended educational workflows.
- Safety checks before rendering child-facing responses.
- SQLite for local persistence.
- A vector index for retrieval over approved lesson content.

## Recommended stack

- **Frontend**: Streamlit
- **Backend logic**: Python
- **LLM**: Claude or compatible model API
- **Retrieval**: Chroma or FAISS
- **Speech**: Browser Web Speech API for MVP
- **Storage**: SQLite
- **Deployment**: Streamlit Community Cloud or Docker

## Modes

### Kid Mode
Designed for children with:
- large buttons,
- mascot-led interaction,
- guided answers,
- reward badges,
- quiz cards,
- limited vocabulary,
- strict safety filtering.

### Teacher Mode
Designed for educators with:
- lesson planning,
- quiz creation,
- worksheet generation,
- concept explanation by grade level,
- image analysis,
- classroom chat,
- broader educational search.

### Admin Mode
Designed for supervisors with:
- conversation logs,
- flagged content review,
- safety settings,
- profile management,
- content activation/deactivation.

## Suggested project structure

```text
KinderAi/
├── README.md
├── KinderAi.md
├── requirements.txt
├── .env.example
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
│   │   ├── models/
│   │   ├── speech/
│   │   ├── rag/
│   │   ├── quiz/
│   │   ├── safety/
│   │   └── progress/
│   ├── data/
│   │   ├── knowledge_base/
│   │   ├── quiz_bank/
│   │   ├── mascot_assets/
│   │   └── vector_index/
│   ├── db/
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

## MVP phases

1. Streamlit shell and mode picker.
2. Teacher mode MVP with text chat and image upload.
3. Kid mode core loop with curated retrieval and safety filtering.
4. Quiz and reward system.
5. Admin review and settings.
6. Deployment and polish.

## Notes

- Kid mode should never answer from open internet.
- Teacher mode can be broader but should still support educational grounding.
- The backend should remain stable even if the UI is redesigned later.
- The project should stay simple enough for an early hackathon build, then grow in phases.
