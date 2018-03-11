import requests
import re
import os
import time
import datetime
import pandas as pd
import logging
import random
from requests.exceptions import RequestException

import config
from utils.loggingutils import init_logging


def make_request(url, cookies, proxy_url):
    # proxy_ip = random.choice(proxy_ips)
    # proxy_url = 'http://{}'.format(proxy_ip)
    # print(proxy_url)
    # proxy_url = "socks5://{ip}:{port}/".format(
    #     ip='127.0.0.1',
    #     port=8899,
    # )
    proxies = {"http": proxy_url, "https": proxy_url}

    r = None
    fail = True
    while fail:
        try:
            r = requests.get(url, headers=config.headers, proxies=proxies, cookies=cookies, timeout=5)
            # r = requests.get(url, headers=config.headers, cookies=cookies)
            fail = False
        except RequestException as e:
            logging.warning("Request for {} failed".format(url))
            return None

    # print(r.headers)
    if r.status_code != 200:
        logging.warning('Got a {} status code for URL: {}'.format(r.status_code, url))
    return r


def __get_asins(asin_file):
    with open(asin_file, encoding='utf-8') as f:
        return f.read().strip().split('\n')


def __update_asins(df_all_asins, asin_file):
    df_visited = pd.read_csv(config.SCRAPE_STATUS_FILE, header=None)
    print(df_visited.shape[0], 'visited')
    assert df_visited.shape[1] == 2
    with open(asin_file, 'w', encoding='utf-8', newline='\n') as fout:
        df_all_asins[~df_all_asins['asin'].isin(df_visited[0])]['asin'].to_csv(fout, header=False, index=False)

# category = 'Cell_Phones_and_Accessories'
category = 'Electronics'
all_asin_file = os.path.join(config.DATADIR, 'asin_list_all_{}.txt'.format(category))
asin_file = os.path.join(config.DATADIR, 'asin_list_{}.txt'.format(category))
scraped_dir = os.path.join(config.DATADIR, 'scraped_{}'.format(category))
min_n_reviews = 20

df_all_asins = pd.read_csv(all_asin_file)
# __update_asins_ob(df_all_asins, asin_file, scraped_dir)
__update_asins(df_all_asins, asin_file)
# exit()

str_today = datetime.date.today().strftime('%y-%m-%d')
init_logging('log/{}.log'.format(str_today), to_stdout=True)

asins = __get_asins(asin_file)
asin_n_rev_dict = {asin: n for asin, n in df_all_asins.itertuples(False, None)}

with open('proxies.txt', encoding='utf-8') as f:
    proxy_ips = f.read().strip().split('\n')
    proxy_urls = ['http://{}'.format(ip) for ip in proxy_ips]
# proxy_urls = ["socks5://{ip}:{port}/".format(ip='127.0.0.1', port=8899)]
purl_cookies_tups = [(purl, None) for purl in proxy_urls]
proxy_fail_dict = {purl: 0 for purl in proxy_urls}

fout_status = open(config.SCRAPE_STATUS_FILE, 'a', encoding='utf-8', newline='\n')
for i, asin in enumerate(asins):
    n_reviews = asin_n_rev_dict[asin]
    if n_reviews < min_n_reviews:
        logging.info('num reviews smaller than {}'.format(min_n_reviews))
        break

    suc_flg = False
    while True:
        purl_idx = random.randint(0, len(purl_cookies_tups) - 1)
        purl, cookies = purl_cookies_tups[purl_idx]
        if i < 10:
            print(purl, cookies)

        logging.info('requesting {}'.format(asin))
        r = make_request('https://www.amazon.com/dp/{}/'.format(asin), cookies, purl)
        if r is None:
            time.sleep(5)
            fail_cnt = proxy_fail_dict[purl]
            proxy_fail_dict[purl] = fail_cnt + 1
            if fail_cnt == 3:
                del purl_cookies_tups[purl_idx]
                logging.info('{} ips left'.format(len(purl_cookies_tups)))
                with open('practiced_proxies.txt', 'w', encoding='utf-8', newline='\n') as fout_tmp:
                    pd.DataFrame({'proxies': [a for a, b in purl_cookies_tups]}).to_csv(
                        fout_tmp, header=False, index=False)
                if len(purl_cookies_tups) == 0:
                    break
            continue
        proxy_fail_dict[purl] = 0

        if r.status_code == 200 and len(r.content) > 50000:
            suc_flg = True
            break

        if r.status_code == 503:
            time.sleep(300.0 / len(purl_cookies_tups))
        elif r.status_code == 404:
            fout_status.write('{},{}\n'.format(asin, 404))
            fout_status.flush()
            time.sleep(5.0 / len(purl_cookies_tups))
            break
        if len(r.content) < 50000:
            logging.warning("Captcha detected")
            time.sleep(60.0 / len(purl_cookies_tups))

    if len(purl_cookies_tups) == 0:
        logging.warning('No available IP left')
        break

    if not suc_flg:
        continue

    if cookies is None:
        cookies = r.cookies
    else:
        for k, v in r.cookies.items():
            cookies[k] = v
    purl_cookies_tups[purl_idx] = (purl, cookies)

    dst_html_file = os.path.join(scraped_dir, '{}.html'.format(asin))
    with open(dst_html_file, 'wb') as fout:
        # html_str = str(r.content, encoding='utf-8')
        html_str = r.content

        html_str = re.sub(b'<script.*?>(.|\n)*?</script>', b'', html_str)
        html_str = re.sub(b'<style.*?>(.|\n)*?</style>', b'', html_str)
        html_str = re.sub(b'\n\s*\n+', b'', html_str)
        fout.write(html_str)

    fout_status.write('{},{}\n'.format(asin, dst_html_file))
    fout_status.flush()

    # exit()
    time.sleep(5.0 / len(purl_cookies_tups))
fout_status.close()
