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


def __gen_asin_file(asin_cnt_dict, dst_file):
    tups = [(k, v) for k, v in asin_cnt_dict.items()]
    tups.sort(key=lambda x: -x[1])
    df = pd.DataFrame(tups, columns=['asin', 'n_reviews'])
    with open(dst_file, 'w', encoding='utf-8', newline='\n') as fout:
        df.to_csv(fout, index=False)


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


def __gen_asin_num_reviews_file(category):
    review_file = os.path.join(config.DATADIR, '{}_5.json'.format(category))
    all_asin_file = os.path.join(config.DATADIR, 'asin_list_all_{}.txt'.format(category))
    asin_cnt_dict = __get_product_num_reviews(review_file)
    __gen_asin_file(asin_cnt_dict, all_asin_file)


def __tmp_func(ret_dict):
    import time
    time.sleep(3)
    ret_dict['s'] = 'ok'
    return 31


from multiprocessing import Process, Manager
if __name__ == '__main__':
    all_done = False
    manager = Manager()
    return_dict = manager.dict()
    p = Process(target=__tmp_func, args=(return_dict,))
    p.start()
    p.join()
    print(return_dict)
    print('ok')
# fout = open(config.SCRAPE_STATUS_FILE, 'a', encoding='utf-8', newline='\n')
# for file in os.listdir('d:/data/amazon/scraped_Cell_Phones_and_Accessories'):
#     fout.write('{},{}\n'.format(file[:-5], os.path.join(config.DATADIR, 'scraped_Cell_Phones_and_Accessories', file)))
# for file in os.listdir('./log'):
#     nf_asins = __get_404_asins(os.path.join('./log', file))
#     for asin in nf_asins:
#         fout.write('{},{}\n'.format(asin, 404))
# fout.close()

# num_asins = 10000
# category = 'Cell_Phones_and_Accessories'
# category = 'Electronics'
# category = 'Tools_and_Home_Improvement'
# category = 'Home_and_Kitchen'
# __gen_asin_num_reviews_file(category)

# __check_metadata(asin_cnt_dict.keys())
