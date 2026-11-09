# Seedha

Kuku AI Generalist, Problem 2. An AI a person in India can talk to about three problems: a security deposit that was not returned, a refund that never came, and wages that stopped. It will not invent a section.

## In this folder

| File | What it is |
| --- | --- |
| `outputs/` | Unedited runs on the eleven test stories. |
| `app.py` and `static/` | The page. Click a sample. No API key. |
| `data/statutes.json` | The only quotes the tool may use. |

## Run

Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open http://127.0.0.1:8000 and click **Bengaluru deposit** first. No API key.

A new story, the way the interview will ask:

```bash
python -m seedha.cli "I left my flat in Jaipur in June 2026. Deposit was Rs 40,000. The landlord will not return it. I have the agreement."
python -m seedha.cli --hi "लखनऊ में जमानत 50,000 रुपये नहीं मिली."
```

Regenerate the raw outputs with:

```bash
python -m seedha.outputs
pytest
```

## Optional model

The model is one function, `seedha/llm.py`. It is off unless you set both of these:

```bash
export SEEDHA_LLM=1
export GEMINI_API_KEY=your_key
export GEMINI_MODEL=gemini-2.5-flash
```

It may only rephrase the explanation. If it names a section the retriever did not return, the template stays and the rewrite is marked rejected. Swap the model by changing `GEMINI_MODEL`.

## Where the decisions are

| File | What it decides |
| --- | --- |
| `seedha/extract.py` | City, amounts, track, violence, a request to add a criminal section. Rules, not a model. |
| `seedha/pipeline.py` | Which statute is retrieved, and which one is refused. |
| `data/statutes.json` | The only quotes the tool may use. |
| `seedha/verify.py` | Rejects a section, a rule, or a "you will win" line that was not retrieved. |
| `seedha/compose.py` | The case file and the notice. It does not choose the law. |
| `data/cases.json` | The test stories, including the ones that should cite nothing. |
