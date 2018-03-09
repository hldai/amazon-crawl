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


# num_asins = 10000
review_file = os.path.join(config.DATADIR, 'Cell_Phones_and_Accessories_5.json')
asin_cnt_dict = __get_product_num_reviews(review_file)
tups = [(k, v) for k, v in asin_cnt_dict.items()]
tups.sort(key=lambda x: -x[1])
df = pd.DataFrame(tups, columns=['asin', 'n_reviews'])
with open(config.ASIN_FILE, 'w', encoding='utf-8', newline='\n') as fout:
    df['asin'].to_csv(fout, header=False, index=False)
