#coding:utf-8

from bs4 import BeautifulSoup
import requests
import logging
import re

logger = logging.getLogger(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/64.0.3282.186 Safari/537.36"
}

def get_html(url):
    request = requests.get(url, headers=headers)
    if request.encoding == 'ISO-8859-1':
        request.encoding = 'utf-8'
    return request.text

def get_soup(url):
    soup = BeautifulSoup(get_html(url), 'lxml')
    return soup

def fetch_kxdaili(page):
    """
    从www.kxdaili.com抓取免费代理
    """
    proxies = []
    try:
        url = 'http://www.kxdaili.com/dailiip/1/%d.html' % page
        soup = get_soup(url)
        table_tag = soup.find('table', attrs={'class': 'ui table segment'})
        trs = table_tag.tbody.find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            ip = tds[0].text
            port = tds[1].text
            latency = tds[4].text.split()[0]
            if float(latency) < 0.5:
                proxy = '%s:%s' % (ip, port)
                proxies.append(proxy)
    except BaseException as e:
        logger.warning('fail to fetch from kxdaili')
    return proxies

def img2port(img_url):
    """
    mimvp.com的端口号用图片来显示, 本函数将图片url转为端口, 目前的临时性方法并不准确
    """
    code = img_url.split('=')[-1]
    if code.endswith('W12cDgw'):
        return 80
    if code.endswith('W12cDEwODAO0O'):
        return 1080
    if code.endswith('W12cDgwODAO0O'):
        return 8080
    if code.endswith('W12cDgxMTgO0O'):
        return 8118
    if code.endswith('W12ck5OTkO0O'):
        return 9999
    else:
        return None

def fetch_mimvp():
    """
    从http://proxy.mimvp.com/free.php抓免费代理
    """
    proxies = []
    try:
        url = 'http://proxy.mimvp.com/free.php?proxy=in_hp'
        soup = get_soup(url)
        table_tag = soup.find('table', attrs={'class': 'free-table table table-bordered table-striped'})
        tds = table_tag.tbody.find_all('td')
        for i in range(0, len(tds), 10):
            ip = tds[i+1].text
            port = img2port(tds[i+2].img['src'])
            response_time = tds[i+7]['title'][:-1]
            if port and float(response_time) < 0.5:
                proxy = '%s:%s' % (ip, port)
                proxies.append(proxy)
    except BaseException as e:
        logger.warning('fail to fetch from mimvp')
    return proxies

def fetch_xici():
    """
    http://www.xicidaili.com/nn/
    """
    proxies = []
    try:
        url = 'http://www.xicidaili.com/nn/'
        soup = get_soup(url)
        table = soup.find('table', attrs={'id': 'ip_list'})
        trs = table.find_all('tr')
        for i in range(1, len(trs)):
            tds = trs[i].find_all('td')
            ip = tds[1].text
            port = tds[2].text
            speed = tds[6].div['title'][:-1].replace('秒', '')
            latency = tds[7].div['title'][:-1].replace('秒', '')
            if float(speed) < 3 and float(latency) < 0.5:
                proxy = '%s:%s' % (ip, port)
                proxies.append(proxy)
    except BaseException as e:
        logger.warning('fail to fetch from xici')
    return proxies

def fetch_ip181():
    """
    http://www.ip181.com/
    """
    proxies = []
    try:
        url = 'http://www.ip181.com/'
        soup = get_soup(url)
        table = soup.find('table', attrs={'class': 'table table-hover panel-default panel ctable'})
        trs = table.find_all('tr')
        for i in range(1, len(trs)):
            tds = trs[i].find_all('td')
            ip = tds[0].text
            port = tds[1].text
            latency = tds[4].text[:-2].split()[0]
            if float(latency) < 0.5:
                proxy = '%s:%s' % (ip, port)
                proxies.append(proxy)
    except BaseException as e:
        logger.warning('fail to fetch from ip181')
    return proxies


def fetch_httpdaili():
    """
    http://www.httpdaili.com/
    更新比较频繁
    """
    url = 'http://www.httpdaili.com'
    proxies = []
    try:
        url = 'http://www.httpdaili.com'
        soup = get_soup(url)
        table = table = list(soup.find("div", attrs={'id': 'success-case'}).children)[1]
        trs = table.find_all('span', attrs={'class': 'STYLE1'})
        for i in range(0, len(trs), 3):
            ip = trs[i].text
            port = trs[i+1].text
            proxy = '%s:%s' % (ip, port)
            print(proxy)
            proxies.append(proxy)
    except BaseException as e:
        logger.warning('fail to fetch from httpdaili')
    return proxies


def check(proxy):
    url = 'https://www.amazon.com/dp/B0017JY5FE'
    # url = 'https://baike.baidu.com/'
    try:
        request = requests.get(url, proxies={'http': proxy, 'https': proxy},
                               headers=headers, timeout=5)
        # request = requests.get(url, proxies={'http': 'http://%s' % proxy, 'https': 'http://%s' % proxy},
        #                        headers=headers)
        print(request.status_code, end='\t')
        if request.status_code == 200 and len(request.content) > 50000:
            return request.ok
        else:
            return False
    except BaseException as e:
        # print(e)
        return False


def __proxies_from_fpl():
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


def fetch_all(candidate_proxies_file):
    proxies = []
    # for i in range(1, endpage):
    #     proxies += fetch_kxdaili(i)
    # proxies += fetch_httpdaili()
    # proxies += fetch_mimvp()
    # proxies += fetch_xici()
    # proxies += fetch_ip181()
    # with open(candidate_proxies_file) as f:
    #     proxies = [line.strip() for line in f]
    proxies = __proxies_from_fpl()
    # print(proxies)
    # exit()
    valid_proxies = []
    logger.info('checking proxies validation')
    for i, proxy in enumerate(proxies):
        print(i, proxy, end='\t')
        if check(proxy):
            print('ok')
            valid_proxies.append(proxy)
            # if len(valid_proxies) > 100:
            #     break
        else:
            print('failed')
    return valid_proxies


if __name__ == '__main__':
    # candidate_proxies_file = 'candidate_proxies.txt'
    candidate_proxies_file = 'proxies_all.txt'
    import sys
    root_logger = logging.getLogger('')
    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(name)-8s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S',)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    proxies = fetch_all(candidate_proxies_file)
    print('found {} valid urls'.format(len(proxies)))
    with open('proxies.txt', 'w', encoding='utf-8', newline='\n') as f:
        for proxy in proxies:
            # print(proxy)
            f.write(proxy + '\n')
