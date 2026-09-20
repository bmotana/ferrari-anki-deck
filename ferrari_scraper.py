"""
ferrari_scraper.py
------------------
Core scraper module to extract Ferrari road cars from Wikipedia for:
1. Anki Flashcards (front: <img src="...">, back: Model Name (Years))
2. Kaggle Dataset (comprehensive production & technical specs)
"""

import csv
import logging
import os
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("ferrari_scraper")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 "
    "FerrariDatasetScraper/1.0 (educational/dataset creation; contact: dev@example.com)"
)

EXCLUDED_CATEGORIES = {
    "one-off & few-off",
    "concept",
    "see also",
    "references",
    "external links",
    "contents",
    "models by category",
}


class FerrariScraper:
    """Scrapes Ferrari road car models and technical specs from Wikipedia."""

    ROAD_CARS_URL = "https://en.wikipedia.org/wiki/List_of_Ferrari_road_cars"
    MEDIAWIKI_API = "https://en.wikipedia.org/w/api.php"

    def __init__(self, request_delay: float = 0.25):
        self.delay = request_delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.5",
            }
        )
        self._html_cache = {}
        self._img_meta_cache = {}

    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and cache a page's HTML parsed with BeautifulSoup."""
        base_url = url.split("#")[0]
        if base_url in self._html_cache:
            return self._html_cache[base_url]

        if self.delay > 0:
            time.sleep(self.delay)

        resp = self.session.get(base_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        self._html_cache[base_url] = soup
        return soup

    def get_image_info(self, file_title: str) -> dict:
        """Query MediaWiki API for canonical image URL and license."""
        if not file_title:
            return {}
        if not file_title.startswith("File:"):
            file_title = f"File:{file_title}"

        if file_title in self._img_meta_cache:
            return self._img_meta_cache[file_title]

        params = {
            "action": "query",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "format": "json",
        }
        try:
            if self.delay > 0:
                time.sleep(self.delay)
            resp = self.session.get(self.MEDIAWIKI_API, params=params, timeout=10)
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for _, page_data in pages.items():
                imageinfo = page_data.get("imageinfo", [])
                if imageinfo:
                    info = imageinfo[0]
                    direct_url = info.get("url", "")
                    ext = info.get("extmetadata", {})
                    license_name = ext.get("LicenseShortName", {}).get("value", "")
                    artist = ext.get("Artist", {}).get("value", "")
                    # Strip any HTML from artist
                    artist_clean = re.sub(r"<[^>]+>", "", artist).strip()
                    res = {
                        "direct_image_url": direct_url,
                        "license": license_name,
                        "artist": artist_clean,
                    }
                    self._img_meta_cache[file_title] = res
                    return res
        except Exception as e:
            logger.debug("Failed to retrieve image info for %s: %s", file_title, e)

        empty_res = {"direct_image_url": "", "license": "", "artist": ""}
        self._img_meta_cache[file_title] = empty_res
        return empty_res

    def get_road_cars_list(self) -> list[dict]:
        """Parse List_of_Ferrari_road_cars to extract all road/production models."""
        soup = self.fetch_page(self.ROAD_CARS_URL)
        models = []
        seen_names = set()

        for sec in soup.find_all("section"):
            h = sec.find(["h2", "h3"])
            if not h:
                continue
            title = h.get_text(strip=True).replace("[edit]", "")
            if title.lower() in EXCLUDED_CATEGORIES:
                continue

            # 1. Current models (wikitable)
            if title == "Current models":
                table = sec.find("table", class_="wikitable")
                if table:
                    for tr in table.find_all("tr")[2:]:
                        th = tr.find("th")
                        tds = tr.find_all("td")
                        if th and tds:
                            a_tag = th.find("a")
                            raw_name = (
                                a_tag.get_text(strip=True)
                                if a_tag
                                else th.get_text(strip=True)
                            )
                            car_name = (
                                raw_name
                                if raw_name.startswith("Ferrari")
                                else f"Ferrari {raw_name}"
                            )
                            href = (
                                urljoin(self.ROAD_CARS_URL, a_tag["href"])
                                if a_tag and "href" in a_tag.attrs
                                else None
                            )
                            year = tds[1].get_text(strip=True) if len(tds) > 1 else ""

                            img_src = ""
                            img = tds[0].find("img")
                            if img and img.get("src"):
                                img_src = (
                                    ("https:" + img["src"])
                                    if img["src"].startswith("//")
                                    else img["src"]
                                )

                            if car_name not in seen_names:
                                seen_names.add(car_name)
                                models.append(
                                    {
                                        "category": title,
                                        "name": car_name,
                                        "list_year": year,
                                        "url": href,
                                        "list_image": img_src,
                                    }
                                )
                continue

            # 2. Historical road models by category (unordered lists)
            for ul in sec.find_all("ul", recursive=False):
                for li in ul.find_all("li"):
                    if li.find("ul"):
                        continue
                    text = li.get_text(" ", strip=True).replace("\xa0", " ")
                    a_tags = [
                        a
                        for a in li.find_all("a")
                        if not a.get("href", "").startswith("#cite")
                    ]
                    if not a_tags:
                        continue

                    b_tag = li.find("b")
                    car_a = (
                        b_tag.find("a") if (b_tag and b_tag.find("a")) else a_tags[0]
                    )
                    raw_name = car_a.get_text(strip=True)
                    car_name = (
                        raw_name
                        if (
                            raw_name.startswith("Ferrari")
                            or raw_name.startswith("Dino")
                        )
                        else f"Ferrari {raw_name}"
                    )
                    href = (
                        urljoin(self.ROAD_CARS_URL, car_a["href"])
                        if "href" in car_a.attrs
                        else ""
                    )

                    m = re.match(r"^(\d{4}(?:\s*[\u2013\u2014\-]\s*\d{4})?)", text)
                    year = m.group(1).replace(" ", "") if m else ""

                    if car_name not in seen_names:
                        seen_names.add(car_name)
                        models.append(
                            {
                                "category": title,
                                "name": car_name,
                                "list_year": year,
                                "url": href,
                                "list_image": "",
                            }
                        )

        return models

    def parse_car_details(self, model_info: dict) -> dict:
        """Extract infobox metadata, specs, and image for a single car."""
        url = model_info.get("url")
        car_name = model_info["name"]
        category = model_info["category"]
        list_year = model_info.get("list_year", "")

        details = {
            "name": car_name,
            "years_produced": list_year,
            "category": category,
            "engine": "",
            "power_output": "",
            "transmission": "",
            "body_style": "",
            "layout": "",
            "number_produced": "",
            "designer": "",
            "image_url": model_info.get("list_image", ""),
            "image_license": "",
            "source_url": url or "",
        }

        if not url:
            return details

        try:
            soup = self.fetch_page(url)
            parsed = urlparse(url)
            fragment = parsed.fragment

            # Locate the relevant infobox
            target_infobox = None
            if fragment:
                # Try finding element by ID or name
                sec_el = soup.find(id=fragment) or soup.find(attrs={"name": fragment})
                if sec_el:
                    parent_sec = sec_el.find_parent("section")
                    if parent_sec:
                        target_infobox = parent_sec.find(
                            "table", class_=lambda c: c and "infobox" in c
                        )
                    if not target_infobox:
                        # Search siblings following the anchor
                        curr = sec_el.next_element
                        steps = 0
                        while curr and steps < 30:
                            if getattr(
                                curr, "name", None
                            ) == "table" and "infobox" in curr.get("class", []):
                                target_infobox = curr
                                break
                            curr = curr.next_element
                            steps += 1

            if not target_infobox:
                target_infobox = soup.find(
                    "table", class_=lambda c: c and "infobox" in c
                )

            if target_infobox:
                # 1. Parse Image
                img = target_infobox.find("img")
                if img and img.get("src"):
                    src = img["src"]
                    full_src = ("https:" + src) if src.startswith("//") else src
                    details["image_url"] = full_src

                    # Check parent link for File: metadata
                    a_parent = img.find_parent("a")
                    if a_parent and a_parent.get("href"):
                        file_match = re.search(r"File:(.+)$", a_parent["href"])
                        if file_match:
                            file_title = file_match.group(1)
                            meta = self.get_image_info(file_title)
                            if meta.get("direct_image_url"):
                                details["image_url"] = meta["direct_image_url"]
                            if meta.get("license"):
                                details["image_license"] = meta["license"]

                # 2. Parse Infobox Rows
                for tr in target_infobox.find_all("tr"):
                    th = tr.find("th")
                    td = tr.find("td")
                    if not th or not td:
                        continue
                    header = th.get_text(strip=True).lower().replace("\xa0", " ")
                    val = td.get_text(separator=" ", strip=True).replace("\xa0", " ")
                    val = re.sub(
                        r"\[\s*[\w\d\s]+\s*\]", "", val
                    ).strip()  # remove citations [1], [citation needed]

                    if "production" in header:
                        # Extract counts like "1,311 produced", "38 made"
                        num_m = re.search(
                            r"([\d,]+(?:\+)?\s*(?:produced|units|built|made|examples|coupes|spiders))",
                            val,
                            re.I,
                        )
                        if num_m:
                            details["number_produced"] = num_m.group(1)
                        elif not details["number_produced"]:
                            pure_num = re.search(r"\b(\d[\d,]+)\b", val)
                            if pure_num and not (
                                1940 <= int(pure_num.group(1).replace(",", "")) <= 2035
                            ):
                                details["number_produced"] = pure_num.group(1)

                        # Check for years if list_year was missing
                        if not details["years_produced"]:
                            y_m = re.search(
                                r"(\d{4}(?:\s*[\u2013\u2014\-]\s*\d{4})?)", val
                            )
                            if y_m:
                                details["years_produced"] = y_m.group(1).replace(
                                    " ", ""
                                )

                    elif "engine" in header:
                        details["engine"] = val
                    elif "power" in header:
                        details["power_output"] = val
                    elif "body" in header:
                        details["body_style"] = val
                    elif "designer" in header:
                        details["designer"] = val
                    elif "layout" in header:
                        details["layout"] = val
                    elif "transmission" in header:
                        details["transmission"] = val

        except Exception as e:
            logger.warning("Error parsing details for %s (%s): %s", car_name, url, e)

        return details

    def scrape(self, limit: int | None = None) -> list[dict]:
        """Scrape all (or up to limit) road car models."""
        models = self.get_road_cars_list()
        total_found = len(models)
        target_list = models[:limit] if limit else models
        total_to_scrape = len(target_list)

        logger.info(
            "Found %d total road models. Scraping %d models...",
            total_found,
            total_to_scrape,
        )

        results = []
        for idx, model_info in enumerate(target_list, start=1):
            name = model_info["name"]
            logger.info("[%d/%d] Scraping %s...", idx, total_to_scrape, name)
            details = self.parse_car_details(model_info)
            results.append(details)

        return results

    @staticmethod
    def save_anki_csv(cars: list[dict], filepath: str):
        """
        Generate ferrari_anki.csv with columns:
        front: <img src="{image_url}">
        back: {name} ({years_produced})
        """
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["front", "back"])
            for car in cars:
                img_url = car.get("image_url", "").strip()
                front = f'<img src="{img_url}">' if img_url else ""

                name = car.get("name", "").strip()
                years = car.get("years_produced", "").strip()
                back = f"{name} ({years})" if years else name

                writer.writerow([front, back])
        logger.info("Saved Anki deck CSV: %s (%d rows)", filepath, len(cars))

    @staticmethod
    def save_kaggle_csv(cars: list[dict], filepath: str):
        """
        Generate ferrari_kaggle.csv with full technical & production specs.
        """
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        fieldnames = [
            "name",
            "years_produced",
            "category",
            "engine",
            "power_output",
            "transmission",
            "body_style",
            "layout",
            "number_produced",
            "designer",
            "image_url",
            "image_license",
            "source_url",
        ]
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for car in cars:
                row = {k: car.get(k, "") for k in fieldnames}
                writer.writerow(row)
        logger.info("Saved Kaggle dataset CSV: %s (%d rows)", filepath, len(cars))
