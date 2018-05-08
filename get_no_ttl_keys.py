# encoding: utf-8
"""
author: yangyi@youzan.com
time: 2018/4/26 下午4:34
func: 获取数据库中没有设置ttl的 key
"""
import redis
import argparse
import time
import sys


class ShowProcess:
    """
    显示处理进度的类
    调用该类相关函数即可实现处理进度的显示
    """
    i = 0           # 当前的处理进度
    max_steps = 0   # 总共需要处理的次数
    max_arrow = 50  # 进度条的长度

    # 初始化函数，需要知道总共的处理次数
    def __init__(self, max_steps):
        self.max_steps = max_steps
        self.i = 0

    # 显示函数，根据当前的处理进度i显示进度
    # 效果为[>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>]100.00%
    def show_process(self, i = None):
        if i is not None:
            self.i = i
        else:
            self.i += 1
        num_arrow = int(self.i * self.max_arrow / self.max_steps)  # 计算显示多少个'>'
        num_line = self.max_arrow - num_arrow                      # 计算显示多少个'-'
        percent = self.i * 100.0 / self.max_steps                  # 计算完成进度，格式为xx.xx%
        process_bar = '[' + '>' * num_arrow + ' ' * num_line + ']'\
                      + '%.2f' % percent + '%' + '\r'              # 带输出的字符串，'\r'表示不换行回到最左边
        sys.stdout.write(process_bar)                              # 这两句打印字符到终端
        sys.stdout.flush()

    def close(self, words='done'):
        print ''
        print words
        self.i = 0


def usage():
    print """
    usage: get_no_ttl_keys.py [-h] [-p PORT] [-d DB_LIST]
    """


def check_ttl(redis_conn, no_ttl_file, dbindex):
    start_time = time.time()
    no_ttl_num = 0
    keys_num = redis_conn.dbsize()
    print "there are {num} keys in db {index} ".format(num=keys_num, index=dbindex)
    process_bar = ShowProcess(keys_num)
    with open(no_ttl_file, 'a') as f:

        for key in redis_conn.scan_iter(count=1000):
            process_bar.show_process()
            if redis_conn.ttl(key) == -1:
                no_ttl_num += 1
                if no_ttl_num < 1000:
                    f.write(key+'\n')
            else:
                continue

    process_bar.close()
    print "cost time(s):", time.time() - start_time
    print "no ttl keys number:", no_ttl_num
    print "we write keys with no ttl to the file: %s" % no_ttl_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, dest='port', action='store', help='port of redis ')
    parser.add_argument('-d', type=str, dest='db_list', action='store', default=0,
                        help='ex : -d all / -d 1,2,3,4 ')
    args = parser.parse_args()
    if not args.port:
        usage()
        sys.exit(-1)
    else:
        port = args.port

    if args.db_list == 'all':
        db_list = [i for i in xrange(0, 16)]
    else:
        db_list = [int(i) for i in args.db_list.split(',')]

    for index in db_list:
        try:
            pool = redis.ConnectionPool(host='127.0.0.1', port=port, db=index)
            r = redis.StrictRedis(connection_pool=pool)
        except redis.exceptions.ConnectionError as e:
            print e
        else:
            no_ttl_keys_file = "/tmp/{port}_{db}_no_ttl_keys.txt".format(port=port, db=index)
            check_ttl(r, no_ttl_keys_file, index)


if __name__ == '__main__':
    main()
