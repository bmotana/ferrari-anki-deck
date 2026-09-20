"""
main.py
-------
CLI entry point to scrape Ferrari road car models and output:
1. ferrari_anki.csv (flashcard deck with image front and model name + year)
2. ferrari_kaggle.csv (dataset with technical specs, production, engine, license)
"""

import argparse
import logging
import sys

from ferrari_scraper import FerrariScraper


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape Ferrari road car models for Anki and Kaggle datasets."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of models to scrape (e.g. --limit 25).",
    )
    parser.add_argument(
        "--count-only",
        action="store_true",
        help="List available road models without scraping pages.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.25,
        help="Polite delay in seconds between Wikipedia requests (default: 0.25s).",
    )
    parser.add_argument(
        "--anki-out",
        type=str,
        default="ferrari_anki.csv",
        help="Output filepath for Anki deck CSV (default: ferrari_anki.csv).",
    )
    parser.add_argument(
        "--kaggle-out",
        type=str,
        default="ferrari_kaggle.csv",
        help="Output filepath for Kaggle dataset CSV (default: ferrari_kaggle.csv).",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging(args.verbose)

    scraper = FerrariScraper(request_delay=args.delay)

    if args.count_only:
        models = scraper.get_road_cars_list()
        print(f"\nFound {len(models)} production Ferrari road models:\n")
        for i, m in enumerate(models, start=1):
            year_info = f" ({m['list_year']})" if m["list_year"] else ""
            print(f"  {i:3d}. [{m['category']}] {m['name']}{year_info}")
        return 0

    print("=" * 60)
    print("       Ferrari Road Cars Dataset & Anki Deck Scraper        ")
    print("=" * 60)
    if args.limit:
        print(f"Mode: Test run limited to {args.limit} models")
    else:
        print("Mode: Full scrape of all production road models")
    print(f"Anki output:   {args.anki_out}")
    print(f"Kaggle output: {args.kaggle_out}")
    print("=" * 60)

    cars = scraper.scrape(limit=args.limit)

    # Save outputs
    scraper.save_anki_csv(cars, args.anki_out)
    scraper.save_kaggle_csv(cars, args.kaggle_out)

    print("\n" + "=" * 60)
    print(f"Scraping successfully completed! Processed {len(cars)} models.")
    print(f"  1. Anki Deck saved to:   {args.anki_out}")
    print(f"  2. Kaggle Data saved to: {args.kaggle_out}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
