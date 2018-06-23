#!/bin/bash
# grab , print and send redis monitoring values to zabbix via zabbix_sender

export PATH=$PATH:/opt/redis/bin:/usr/local/bin

TMPFILE=`mktemp --suffix=-redis-monitoring`
TMPFILE1=`mktemp --suffix=-redis-monitoring`
TMPFILE2=`mktemp --suffix=-redis-monitoring`

ZABBIX_SENDER="/opt/zabbix/bin/zabbix_sender"
ZABBIX_AGENT_CONF="/opt/zabbix/etc/zabbix_agentd.conf"
ZABBIX_SERVER=$(awk -F= '/^ServerActive/ { print $2 } ' $ZABBIX_AGENT_CONF)
REDIS_CLI="redis-cli -h 127.0.0.1 -p $1"

trap "rm -f $TMPFILE $TMPFILE1 $TMPFILE2; exit" SIGHUP SIGINT SIGTERM EXIT

#check redis run status
RUNNING_OK=$($REDIS_CLI ping)
if [ $RUNNING_OK = 'PONG' ];then
    echo "redis_running_ok 0" > $TMPFILE
else
    # NOK or with no response
    echo "redis_running_ok 1" > $TMPFILE
fi

#收集内存，客户端会话，统计信息
$REDIS_CLI info memory  | grep -v -E "^#|^$" >> $TMPFILE
$REDIS_CLI info clients | grep -v -E "^#|^$" >> $TMPFILE
$REDIS_CLI info stats   | grep -v -E "^#|^$" >> $TMPFILE
sed -i 's/\r$//;s/:/ /' $TMPFILE

# 计算命中率
HITS=`awk '/keyspace_hits/{print $2}' $TMPFILE`
MISS=`awk '/keyspace_misses/{print $2}' $TMPFILE`

if [ $(($HITS+$MISS)) -eq 0 ];then
    echo hitrate 1 >> $TMPFILE
else
    echo hitrate $(echo "scale=4;$HITS/($HITS+$MISS)" | bc | awk '{printf "%.4f", $0}') >> $TMPFILE
fi

# rt
$REDIS_CLI --intrinsic-latency 1 | awk '/avg latency/{print "redis_avg_latency "$6}' >> $TMPFILE

# keyspace
$REDIS_CLI info Keyspace > $TMPFILE1
KEYSPACE_TOTAL_KEYS=`awk -F, '/^db/{print $1}' $TMPFILE1 | awk -F= '{sum+=$2}END{print sum}'`
KEYSPACE_TOTAL_KEYS_HAS_TTL=`awk -F, '/^db/{print $2}' $TMPFILE1 | awk -F= '{sum+=$2}END{print sum}'`
echo keyspace_total_keys ${KEYSPACE_TOTAL_KEYS:=0} >> $TMPFILE
echo keyspace_total_keys_has_ttl ${KEYSPACE_TOTAL_KEYS_HAS_TTL:=0} >> $TMPFILE
if [ "$KEYSPACE_TOTAL_KEYS_HAS_TTL" -eq 0 ];then
    echo keyspace_keys_avg_ttl 0 >> $TMPFILE
else
    KEYSPACE_KEYS_AVG_TTL=`sed 's/db.*expires=/ /;s/,avg_ttl=/ /' $TMPFILE1 | awk '{sumt+=($1*$2);sumk+=$1}END{printf "%.0f", sumt/sumk}'`
    echo keyspace_keys_avg_ttl $KEYSPACE_KEYS_AVG_TTL >> $TMPFILE
fi

IFS=$'\n'
for d in `cat $TMPFILE`
do
    echo "$HOSTNAME $d" >> $TMPFILE2
done

IFS=""

$ZABBIX_SENDER -z $ZABBIX_SERVER -i $TMPFILE2
rm -f $TMPFILE $TMPFILE1 $TMPFILE2
