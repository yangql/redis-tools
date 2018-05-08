# encoding: utf-8
"""
author: yangyi@youzan.com
time: 2018/4/27 下午2:53
func: 使用scan 方法遍历指定前缀的key ，然后使用pipeline删除，
      需要编辑脚本，修改数据源和指定具体的keys ，该脚本不通用。
"""
import redis
import time
pool = redis.ConnectionPool(host='127.0.0.1', port=6381, db=2)
r = redis.Redis(connection_pool=pool)


def del_keys_with_pipe(re_str):
    start_time = time.time()
    result_length = 0
    pipe = r.pipeline()
    for key in r.scan_iter(match=re_str, count=5000):
        pipe.delete(key)
        result_length += 1
        if result_length % 5000 == 0:
            pipe.execute()
    pip_time = time.time()
    print "use pipeline scan time ", time.time() - start_time
    pipe.execute()

    print "use pipeline end at:", time.time() - pip_time
    print "use pipeline ways delete numbers:", result_length


def get_keys(re_str):
    redis_cursor = 0
    result_length = 0
    redis_ret = r.scan(redis_cursor, match=re_str, count=100)
    redis_cursor = redis_ret[0]
    result_length += len(redis_ret[1])
    print redis_ret[1]


def main():
    for item in ['E20180410*', 'E20180411*']:
        del_keys_with_pipe(item)


if __name__ == '__main__':
    main()


