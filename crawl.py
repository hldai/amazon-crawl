import requests
import re
import os
import time
import datetime
import pandas as pd
import logging
from requests.exceptions import RequestException

import config
from utils.loggingutils import init_logging


def make_request(url, cookies):
    proxy_url = "socks5://{ip}:{port}/".format(
        ip='127.0.0.1',
        port=8899,
    )
    proxies = {"http": proxy_url, "https": proxy_url}

    fail = True
    while fail:
        try:
            r = requests.get(url, headers=config.headers, proxies=proxies, cookies=cookies)
            # r = requests.get(url, headers=config.headers, cookies=cookies)
            fail = False
        except RequestException as e:
            logging.warning("Request for {} failed, trying again.".format(url))
            time.sleep(5)

    # print(r.headers)
    if r.status_code != 200:
        logging.warning('Got a {} status code for URL: {}'.format(r.status_code, url))
        if r.status_code == 503:
            time.sleep(60)
        return None
    return r


def __get_asins(asin_file):
    with open(asin_file, encoding='utf-8') as f:
        return f.read().strip().split('\n')


def __get_404_asins(log_file):
    f = open(log_file, encoding='utf-8')
    cur_asin = ''
    asin_set = set()
    for line in f:
        line = line.strip()
        if line[:-11].endswith('requesting'):
            cur_asin = line[-10:]
        if '404 status' in line:
            asin_set.add(cur_asin)
    f.close()
    return asin_set


def __update_asins():
    df = pd.read_csv(config.ALL_ASIN_FILE)
    all_asins = df['asin']
    # all_asins = __get_asins(config.ALL_ASIN_FILE)
    scraped_asins = set()
    for file in os.listdir(config.SCRAPE_DIR):
        scraped_asins.add(file[:-5])
    for file in os.listdir('./log'):
        nf_asins = __get_404_asins(os.path.join('./log', file))
        scraped_asins = scraped_asins.union(nf_asins)
    # print(scraped_asins)
    with open(config.ASIN_FILE, 'w', encoding='utf-8', newline='\n') as fout:
        pd.DataFrame({'asin': [asin for asin in all_asins if asin not in scraped_asins]}
                     ).to_csv(fout, header=False, index=False)


__update_asins()
# exit()

str_today = datetime.date.today().strftime('%y-%m-%d')
init_logging('log/{}.log'.format(str_today), to_stdout=True)

asins = __get_asins(config.ASIN_FILE)

cookies = None
for i, asin in enumerate(asins):
    logging.info('requesting {}'.format(asin))
    r = make_request('https://www.amazon.com/dp/{}/'.format(asin), cookies)
    if r is None:
        time.sleep(5)
        continue
    if len(r.content) < 50000:
        logging.warning("Captcha detected")
        time.sleep(60)
        continue

    if cookies is None:
        cookies = r.cookies
    else:
        for k, v in r.cookies.items():
            cookies[k] = v
    if i < 10:
        print(cookies)

    with open(os.path.join(config.SCRAPE_DIR, '{}.html'.format(asin)), 'wb') as fout:
        # html_str = str(r.content, encoding='utf-8')
        html_str = r.content

        html_str = re.sub(b'<script.*?>(.|\n)*?</script>', b'', html_str)
        html_str = re.sub(b'<style.*?>(.|\n)*?</style>', b'', html_str)
        html_str = re.sub(b'\n\s*\n+', b'', html_str)
        fout.write(html_str)

    # exit()
    time.sleep(5)
