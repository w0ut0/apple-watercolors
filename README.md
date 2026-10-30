# 🍎 Apple Watercolors

A scraper and browsable slideshow for the **3,667 apple paintings** in the
[USDA Pomological Watercolor Collection](https://naldc.nal.usda.gov/usda_pomological_watercolor),
downloaded from Wikimedia Commons.

The repo includes the scraped dataset and images, so you can open the
slideshow right away without running the scraper.

## Quick start

Open `data/slideshow.html` in a browser. That's it: no server or build step needed.

The slideshow has keyboard navigation (← / →), search and filter, and a
thumbnail strip.

## Repository layout

```
scrape_apples.py      Scrapes Commons → data/paintings.jsonl, cultivars.json, images/
build_slideshow.py    Builds data/slideshow.html from the scraped data
requirements.txt
data/
  paintings.jsonl     One record per painting
  cultivars.json      Paintings grouped by cultivar
  images/POMxxxx.jpg  Painting images (public domain)
  slideshow.html      Generated, self-contained viewer
```

## Re-scraping / rebuilding

```bash
pip install -r requirements.txt
python scrape_apples.py --width 640          # resumable; skips existing images
python build_slideshow.py
```

Run `python scrape_apples.py --help` to see all options (e.g. `--limit`, `--out`).

### Record fields

`pom_id`, `cultivar`, `scientific_name`, `origin`, `description`, `date`,
`artist`, `license`, `categories`, `commons_url`, `usda_url`, `thumb_url`,
`original_size`, `image_file`

## License

- **Code**: [MIT](LICENSE)
- **Images**: public domain (U.S. federal government works). See [DATA_LICENSE.md](DATA_LICENSE.md).
- **Metadata**: public domain / factual. Some Commons description text is CC BY-SA 4.0.

Image credit: *U.S. Department of Agriculture Pomological Watercolor Collection.
Rare and Special Collections, National Agricultural Library, Beltsville, MD 20705.*
