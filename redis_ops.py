# encoding: utf-8
"""
author: yangyi@youzan.com
time: 2018/3/9 下午8:35
func: 
"""
import redis
import random
import string
import time
pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=2)
r = redis.Redis(connection_pool=pool)


def random_str():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(7))


def init_keys():
    start_time = time.time()
    for i in xrange(0, 100000):
        key_name = 'dba_'+str(i)
        value_name = random_str()
        r.set(key_name, value_name)
    print 'initial keys successfully,use time:', time.time() - start_time


def del_keys_without_pipe():
    start_time = time.time()
    redis_cursor = 0
    while True:
        redis_ret = r.scan(redis_cursor, match='dba_*', count=1000)
        redis_cursor = redis_ret[0]
        result_length = len(redis_ret[1])
        if not result_length:
            # 如果已经全部扫描完成
            break
        else:
            r.delete(*redis_ret[1])
            result_length += 1
    print "normal ways delete numbers:", result_length
    print "del keys without pipeline :", time.time() - start_time


def del_keys_with_pipe():
    start_time = time.time()
    redis_cursor = 0
    pipe = r.pipeline()
    while True:
        redis_ret = pipe.scan(redis_cursor, match='dba_*', count=1000).execute()
        redis_cursor = redis_ret[0][0]
        result_length = len(redis_ret[0][1])
        if not redis_cursor:
            # 如果已经全部扫描完成
            break
        else:
            pipe.delete(*redis_ret[0][1]).execute()
    print "normal ways delete numbers:", result_length
    print "del keys with pipeline:", time.time() - start_time


def main():
    init_keys()
    del_keys_without_pipe()
    init_keys()
    del_keys_with_pipe()


if __name__ == '__main__':
    main()


