import requests
import re
import os
import time
import datetime
import pandas as pd
import random
from multiprocessing import Process, Manager
from requests.exceptions import RequestException

import config
from utils import loggingutils


def __check_proxy(proxy_url):
    url = 'https://www.amazon.com/dp/B0017JY5FE'
    try:
        request = requests.get(url, proxies={'http': proxy_url, 'https': proxy_url},
                               headers=config.headers, timeout=5)
        print(request.status_code, end='\t')
        if request.status_code == 200 and len(request.content) > 50000:
            return request.ok
        else:
            return False
    except BaseException as e:
        # print(e)
        return False


def __get_proxy_urls():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/64.0.3282.186 Safari/537.36"
    }
    r = requests.get('https://free-proxy-list.net', headers=headers)
    # print(r.text)
    miter = re.finditer('<tr><td>(.*?)</td><td>(.*?)</td><td>.*?</td><td.*?<td.*?<td.*?<td class=\'hx\'>(.*?)</td>',
                        r.text)
    urls = list()
    for m in miter:
        protocol = 'https' if m.group(3) == 'yes' else 'http'
        urls.append('{}://{}:{}'.format(protocol, m.group(1), m.group(2)))
    # for url in urls:
    #     print(url)
    print(len(urls), 'urls')
    return urls


def __get_checked_proxies():
    proxy_urls = __get_proxy_urls()
    valid_proxies = []
    print('checking proxies ...')
    for i, proxy in enumerate(proxy_urls):
        print(i, proxy, end='\t')
        if __check_proxy(proxy):
            print('ok')
            valid_proxies.append(proxy)
            # if len(valid_proxies) > 100:
            #     break
        else:
            print('failed')
    return valid_proxies


def make_request(url, cookies, proxy_url):
    # proxy_ip = random.choice(proxy_ips)
    # proxy_url = 'http://{}'.format(proxy_ip)
    # print(proxy_url)
    # proxy_url = "socks5://{ip}:{port}/".format(
    #     ip='127.0.0.1',
    #     port=8899,
    # )
    proxies = {"http": proxy_url, "https": proxy_url}

    try:
        r = requests.get(url, headers=config.headers, proxies=proxies, cookies=cookies, timeout=5)
        # r = requests.get(url, headers=config.headers, cookies=cookies)
    except RequestException as e:
        return None

    # print(r.headers)
    return r


def __get_asins(asin_file):
    asins = list()
    with open(asin_file, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                asins.append(line)
    return asins


def __update_asins(df_all_asins, scrape_status_file, asin_file):
    if not os.path.isfile(scrape_status_file):
        with open(asin_file, 'w', encoding='utf-8', newline='\n') as fout:
            df_all_asins['asin'].to_csv(fout, header=False, index=False)
        return

    df_visited = pd.read_csv(scrape_status_file, header=None)
    print(df_visited.shape[0], 'visited')
    assert df_visited.shape[1] == 2
    with open(asin_file, 'w', encoding='utf-8', newline='\n') as fout:
        df_all_asins[~df_all_asins['asin'].isin(df_visited[0])]['asin'].to_csv(fout, header=False, index=False)


def __scrape_amazon(proxy_urls, category):
    str_today = datetime.date.today().strftime('%y-%m-%d')
    logger = loggingutils.get_logger('{}_log', 'log/{}-{}.log'.format(category, str_today), to_stdout=True)
    # init_logging('log/{}.log'.format(str_today), to_stdout=True)
    print('scraping in category: {}'.format(category))

    min_n_reviews = 0
    all_asin_file = os.path.join(config.DATADIR, 'asin_list_all_{}.txt'.format(category))
    asin_file = os.path.join(config.DATADIR, 'asin_list_{}.txt'.format(category))
    scraped_dir = os.path.join(config.DATADIR, 'scraped_{}'.format(category))
    scrape_status_file = os.path.join(config.DATADIR, 'scrape_status_{}.txt'.format(category))

    df_all_asins = pd.read_csv(all_asin_file)
    # __update_asins_ob(df_all_asins, asin_file, scraped_dir)
    # __update_asins(df_all_asins, scrape_status_file, asin_file)

    asins = __get_asins(asin_file)
    asin_n_rev_dict = {asin: n for asin, n in df_all_asins.itertuples(False, None)}

    # with open(proxy_file, encoding='utf-8') as f:
        # proxy_ips = f.read().strip().split('\n')
        # proxy_urls = ['https://{}'.format(ip) for ip in proxy_ips]
        # proxy_urls = f.read().strip().split('\n')
        # proxy_urls = ['https://185.93.3.123:8080/']
    # proxy_urls = ["socks5://{ip}:{port}/".format(ip='127.0.0.1', port=8899)]
    purl_cookies_tups = [(purl, None) for purl in proxy_urls]
    proxy_fail_dict = {purl: 0 for purl in proxy_urls}

    fout_status = open(scrape_status_file, 'a', encoding='utf-8', newline='\n')
    for i, asin in enumerate(asins):
        n_reviews = asin_n_rev_dict[asin]
        if n_reviews < min_n_reviews:
            logger.info('num reviews smaller than {}'.format(min_n_reviews))
            break

        suc_flg = False
        while True:
            purl_idx = random.randint(0, len(purl_cookies_tups) - 1)
            purl, cookies = purl_cookies_tups[purl_idx]
            if i < 10:
                print(purl, cookies)

            logger.info('requesting {}'.format(asin))
            r = make_request('https://www.amazon.com/dp/{}/'.format(asin), cookies, purl)

            if r is None:
                logger.warning("Request for {} failed".format(asin))
            elif r.status_code != 200:
                logger.warning('Got a {} status code for {}'.format(r.status_code, asin))
            elif len(r.content) < 50000:
                logger.warning("Captcha detected")
            else:
                suc_flg = True
                break

            if r is None or r.status_code == 503 or (r.status_code == 200 and len(r.content) < 50000):
                fail_cnt = proxy_fail_dict[purl]
                proxy_fail_dict[purl] = fail_cnt + 1
                if fail_cnt == 3:
                    del purl_cookies_tups[purl_idx]
                    logger.info('{} ips left'.format(len(purl_cookies_tups)))
                    with open('practiced_proxies_{}.txt'.format(category), 'w', encoding='utf-8', newline='\n'
                              ) as fout_tmp:
                        pd.DataFrame({'proxies': [a[7:] for a, b in purl_cookies_tups]}).to_csv(
                            fout_tmp, header=False, index=False)
                    if len(purl_cookies_tups) == 0:
                        break
                time.sleep(300.0 / len(purl_cookies_tups))
                continue
            proxy_fail_dict[purl] = 0

            if r.status_code == 404:
                fout_status.write('{},{}\n'.format(asin, 404))
                fout_status.flush()
                time.sleep(5.0 / len(purl_cookies_tups))
                break

        if len(purl_cookies_tups) == 0:
            logger.warning('No available IP left')
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


def __split_proxies(proxy_file, dst_files):
    with open(proxy_file, encoding='utf-8') as f:
        proxies = [line.strip() for line in f]
    p = 0
    n_proxies, n_dst_files = len(proxies), len(dst_files)
    for i, filename in enumerate(dst_files):
        pend = int(n_proxies * (i + 1) / n_dst_files)
        with open(filename, 'w', encoding='utf-8', newline='\n') as fout:
            for proxy in proxies[p:pend]:
                fout.write('{}\n'.format(proxy))
        p = pend


if __name__ == '__main__':
    # __scrape_amazon('proxies.txt', 'Cell_Phones_and_Accessories')
    # __scrape_amazon('proxies.txt', 'Electronics')

    # categories = ['Electronics', 'Tools_and_Home_Improvement']
    # categories = ['Electronics', 'Home_and_Kitchen']
    categories_all = ['Electronics']

    # proxy_file = 'proxies.txt'
    # proxy_files = ['proxies_{}.txt'.format(i) for i in range(len(categories))]
    # __split_proxies(proxy_file, proxy_files)

    while True:
        categories = list()
        for category in categories_all:
            all_asin_file = os.path.join(config.DATADIR, 'asin_list_all_{}.txt'.format(category))
            asin_file = os.path.join(config.DATADIR, 'asin_list_{}.txt'.format(category))
            scrape_status_file = os.path.join(config.DATADIR, 'scrape_status_{}.txt'.format(category))
            df_all_asins = pd.read_csv(all_asin_file)
            # __update_asins_ob(df_all_asins, asin_file, scraped_dir)
            __update_asins(df_all_asins, scrape_status_file, asin_file)
            asins = __get_asins(asin_file)
            if len(asins):
                categories.append(category)

        if not categories:
            break

        proxy_urls = __get_checked_proxies()
        proxy_urls_list = [proxy_urls]
        process_list = list()

        for purls, category in zip(proxy_urls_list, categories):
            p = Process(target=__scrape_amazon, args=(purls, category))
            p.start()
            process_list.append(p)
        for p in process_list:
            p.join()
