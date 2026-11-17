# LoreGuard AI

LoreGuard combines Gemini screenplay generation with a deterministic memory
and consistency checker. The Streamlit UI is in `app.py`.

## Setup

Use Python 3.10 or newer, then install dependencies:

```bash
python -m pip install -r requirements.txt
```

Set the Gemini key before starting the app:

```bash
export GEMINI_API_KEY="your-key"
streamlit run app.py
```

The optional `GEMINI_MODEL` environment variable selects the model and defaults
to `gemini-2.0-flash`. Never commit `.env` files or API keys.

## Integration contract

`ai_generator.generate_screenplay(request)` returns structured JSON containing
one or more scenes under `branches`. Each scene may contain `assertions`,
`actions`, `suggested_traits`, and `screenplay_text`.

`integration.generate_and_check()` validates that output and checks every scene
against `memory.json`:

```python
from ai_generator import generate_screenplay
from consistency_engine import load_memory
from integration import generate_and_check

result = generate_and_check(
    generate_screenplay,
    {"prompt": "Mira finds a hidden letter", "branch_count": 3},
    load_memory("memory.json"),
    branches=True,
)
```

The result contains `ok`, `error`, `generated`, and checked `results`. Invalid
AI output is returned as a controlled error instead of crashing the frontend.

## Tests

Run the complete suite from the repository root:

```bash
python -m unittest discover -v
```

The tests use fake generators and do not require a Gemini API key.
