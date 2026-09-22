# Contributing

Thanks for helping improve Ferrari Anki Decks.

## Local setup

Create and activate a Python 3.10+ virtual environment, then install the runtime dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Before opening a pull request

Keep changes focused, avoid committing generated datasets or Anki packages, and run:

```powershell
python -m ruff check .
python -m ruff format --check .
```

For scraper changes, use a small `--limit` run first. Please be respectful of Wikipedia and Wikimedia services: retain a request delay and do not bulk-fetch unnecessarily.
