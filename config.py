from os import path

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, sdch, br",
    "Accept-Language": "en-US,en;q=0.8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
}

DATADIR = 'd:/data/amazon'
# ALL_ASIN_FILE = path.join(DATADIR, 'asin_list_all.txt')
# ASIN_FILE = path.join(DATADIR, 'asin_list.txt')
# SCRAPE_DIR = path.join(DATADIR, 'scraped')
SCRAPE_STATUS_FILE = path.join(DATADIR, 'scrape_status.txt')
METADATA_FILE = path.join(DATADIR, 'metadata.json')
