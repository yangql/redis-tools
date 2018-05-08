# encoding: utf-8
"""
author: yangyi@youzan.com
time: 2018/3/9 下午8:35
func: 使用scan 方法遍历指定前缀的key ，然后使用pipeline删除
"""
import redis
import time
import argparse
import sys
import traceback


def del_keys_with_pipe(re_str, redis_conn):
    start_time = time.time()
    result_length = 0
    pipe = redis_conn.pipeline()
    for key in redis_conn.scan_iter(match=re_str, count=5000):
        pipe.delete(key)
        result_length += 1
        if result_length % 5000 == 0:
            pipe.execute()

    pipe.execute()
    print "cost time(s):", time.time() - start_time
    print "delete keys number:", result_length


def usage():
    print """
    use python delete_keys.py -h for more detail info
    usage:python delete_keys.py [-h] [-p PORT] [-k ITEM_LIST]
    """


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, dest='port', action='store', help='port of redis ')
    parser.add_argument('-d', type=int, dest='db_index', action='store', default=0,
                        help='ex : -d 4 ')
    parser.add_argument('-k', type=str, dest='item_list', action='store',
                        help="ex : -k 'E20180410*','E20180411*' ")
    args = parser.parse_args()
    if not args.port or not args.item_list or not args.db_index:
        usage()
        sys.exit(-1)
    else:
        redis_port = args.port
        key_prefix = args.item_list
        db_num = args.db_index

    try:
        pool = redis.ConnectionPool(host='127.0.0.1', port=redis_port, db=db_num)
        r = redis.StrictRedis(connection_pool=pool)
    except redis.ConnectionError as e:
        print traceback.format_exc(e)
    else:
        for item in key_prefix.split(','):
            del_keys_with_pipe(item, r)


if __name__ == '__main__':
    main()



