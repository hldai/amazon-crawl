import json
import os
import config
import pandas as pd


def __get_product_num_reviews(review_file):
    asin_cnt_dict = dict()
    f = open(review_file, encoding='utf-8')
    for line in f:
        r = json.loads(line)
        asin = r['asin']
        cnt = asin_cnt_dict.get(asin, 0)
        asin_cnt_dict[asin] = cnt + 1
    f.close()
    return asin_cnt_dict


def __check_metadata(asins):
    asins_with_metadata = set()
    with open(config.METADATA_FILE, encoding='utf-8') as f:
        for line in f:
            # print(line)
            line = line.replace("'", '"')
            # try:
            obj = json.loads(line)
            # except Exception as e:
            #     print(line)
            asins_with_metadata.add(obj['asin'])

    for asin in asins:
        if asin not in asins_with_metadata:
            print(asin)


def __gen_asin_file(asin_cnt_dict):
    tups = [(k, v) for k, v in asin_cnt_dict.items()]
    tups.sort(key=lambda x: -x[1])
    df = pd.DataFrame(tups, columns=['asin', 'n_reviews'])
    with open(config.ALL_ASIN_FILE, 'w', encoding='utf-8', newline='\n') as fout:
        df['asin'].to_csv(fout, header=False, index=False)


# f = open('d:/data/amazon/scraped/B00J4J6JN0.html', encoding='utf-8')
# print(len(f.read()))
# exit()

# num_asins = 10000
review_file = os.path.join(config.DATADIR, 'Cell_Phones_and_Accessories_5.json')
asin_cnt_dict = __get_product_num_reviews(review_file)
__gen_asin_file(asin_cnt_dict)

# __check_metadata(asin_cnt_dict.keys())
