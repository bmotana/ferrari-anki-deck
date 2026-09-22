# Ferrari Anki Decks

[![CI](https://github.com/bmotana/ferrari-anki-deck/actions/workflows/ci.yml/badge.svg)](https://github.com/bmotana/ferrari-anki-deck/actions/workflows/ci.yml)

Build an image-led Ferrari road-car flashcard deck and a reusable dataset from Wikipedia. One command creates two CSV files: an Anki import with image cards, and a Kaggle-friendly dataset with production and technical details.

## What it creates

| File | Intended use | Contents |
| --- | --- | --- |
| `ferrari_anki.csv` | Import into Anki | `front` HTML image and `back` model name/year |
| `ferrari_kaggle.csv` | Publish or analyse | Model, production years, engine, power, body style, image licence, source URL, and more |

Generated datasets and Anki packages are deliberately excluded from Git so that the repository stays lightweight.

## Quick start

Python 3.10 or newer is required.

```powershell
git clone https://github.com/bmotana/ferrari-anki-deck.git
cd ferrari-anki-deck
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py --limit 25
```

Start with a small run, then omit `--limit` to scrape the full road-car list:

```powershell
python main.py
```

Useful options:

```text
--count-only        List available models without fetching their detail pages
--limit N           Scrape only N models (recommended while testing)
--delay SECONDS     Set a polite delay between requests; default: 0.25
--anki-out PATH     Choose the Anki CSV output path
--kaggle-out PATH   Choose the dataset CSV output path
-v, --verbose       Show debug logging
```

## Importing into Anki

Import `ferrari_anki.csv` as a comma-separated file with two fields. Map `front` to the card front and `back` to the card back. The front field contains an HTML `<img>` tag that points to the image URL.

## Data source and responsible use

The scraper uses Wikipedia's [List of Ferrari road cars](https://en.wikipedia.org/wiki/List_of_Ferrari_road_cars) as its index and reads individual model pages plus the MediaWiki API for image metadata. Keep a sensible request delay, check the generated image licences before redistribution, and verify fields before publishing a derived dataset.

## Development

Ruff handles linting and formatting:

```powershell
python -m ruff check .
python -m ruff format --check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance. This project is released under the [MIT License](LICENSE).
