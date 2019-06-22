#!/bin/bash

SCRIPT_FILE_FOLDER=$(cd "$(dirname "${BASH_SOURCE-$0}")"; pwd)

mkdir -p $SCRIPT_FILE_FOLDER/redis_1
mkdir -p $SCRIPT_FILE_FOLDER/redis_2
mkdir -p $SCRIPT_FILE_FOLDER/redis_3
mkdir -p $SCRIPT_FILE_FOLDER/sentinel_1
mkdir -p $SCRIPT_FILE_FOLDER/sentinel_2
mkdir -p $SCRIPT_FILE_FOLDER/sentinel_3

NETWORK='kk-dev'

# docker network create --driver bridge $NETWORK
# docker pull redis:alpine

cp -vf $SCRIPT_FILE_FOLDER/sample-master.redis.conf redis_1/redis.conf

cp -vf $SCRIPT_FILE_FOLDER/sample-slave.redis.conf redis_2/redis.conf
cp -vf $SCRIPT_FILE_FOLDER/sample-slave.redis.conf redis_3/redis.conf

cp -vf $SCRIPT_FILE_FOLDER/sample-sentinel.conf sentinel_1/sentinel.conf
cp -vf $SCRIPT_FILE_FOLDER/sample-sentinel.conf sentinel_2/sentinel.conf
cp -vf $SCRIPT_FILE_FOLDER/sample-sentinel.conf sentinel_3/sentinel.conf

# 依次创建 redis_1, redis_2, redis_3
docker run --name redis_1 --hostname redis_1 --net=$NETWORK \
-v $SCRIPT_FILE_FOLDER/redis_1:/custom \
-d redis:alpine redis-server /custom/redis.conf

docker run --name redis_2 --hostname redis_2 --net=$NETWORK \
-v $SCRIPT_FILE_FOLDER/redis_2:/custom \
-d redis:alpine redis-server /custom/redis.conf

docker run --name redis_3 --hostname redis_3 --net=$NETWORK \
-v $SCRIPT_FILE_FOLDER/redis_3:/custom \
-d redis:alpine redis-server /custom/redis.conf

# 依次创建 sentinel_1, sentinel_2, sentinel_3

docker run --name sentinel_1 --hostname sentinel_1 --net=$NETWORK \
-v $SCRIPT_FILE_FOLDER/sentinel_1:/custom \
-d redis:alpine redis-sentinel /custom/sentinel.conf

docker run --name sentinel_2 --hostname sentinel_2 --net=$NETWORK \
-v $SCRIPT_FILE_FOLDER/sentinel_2:/custom \
-d redis:alpine redis-sentinel /custom/sentinel.conf

docker run --name sentinel_3 --hostname sentinel_3 --net=$NETWORK \
-v $SCRIPT_FILE_FOLDER/sentinel_3:/custom \
-d redis:alpine redis-sentinel /custom/sentinel.conf