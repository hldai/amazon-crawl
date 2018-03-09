import requests
import re
import os
import time
import datetime
import logging
from requests.exceptions import RequestException

import config
from utils.loggingutils import init_logging


def make_request(url):
    proxy_url = "socks5://{ip}:{port}/".format(
        ip='127.0.0.1',
        port=8899,
    )
    proxies = {"http": proxy_url, "https": proxy_url}

    fail = True
    while fail:
        try:
            r = requests.get(url, headers=config.headers, proxies=proxies)
            fail = False
        except RequestException as e:
            logging.warning("Request for {} failed, trying again.".format(url))
            time.sleep(5)

    # print(r.headers)
    if r.status_code != 200:
        logging.warning('Got a {} status code for URL: {}'.format(r.status_code, url))
        return None
    return r


str_today = datetime.date.today().strftime('%y-%m-%d')
init_logging('log/{}.log'.format(str_today), to_stdout=True)

with open(config.ASIN_FILE, encoding='utf-8') as f:
    asins = f.read().strip().split('\n')
# print(asins)
# exit()

for asin in asins:
    logging.info('requesting {}'.format(asin))
    r = make_request('https://www.amazon.com/dp/{}/'.format(asin))
    if r is None:
        exit()

    with open(os.path.join(config.SCRAPE_DIR, '{}.html'.format(asin)), 'wb') as fout:
        # html_str = str(r.content, encoding='utf-8')
        html_str = r.content

        html_str = re.sub(b'<script.*?>(.|\n)*?</script>', b'', html_str)
        html_str = re.sub(b'<style.*?>(.|\n)*?</style>', b'', html_str)
        html_str = re.sub(b'\n\s*\n+', b'', html_str)
        fout.write(html_str)

    time.sleep(5)
