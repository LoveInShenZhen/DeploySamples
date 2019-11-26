#!/bin/bash

SCRIPT_FILE_FOLDER=$(cd "$(dirname "${BASH_SOURCE-$0}")"; pwd)

mkdir -p $SCRIPT_FILE_FOLDER/redis_1

cp -vf $SCRIPT_FILE_FOLDER/sample.redis.conf redis_1/redis.conf

# 在指定的网络中创建docker
# NETWORK='kk-dev'

# docker run --name redis_1 --hostname redis_1 --net=$NETWORK \
# -v $SCRIPT_FILE_FOLDER/redis_1:/custom \
# -d redis:alpine redis-server /custom/redis.conf

docker run --name redis_1 --hostname redis_1 --rm -p 6379:6379 \
-v $SCRIPT_FILE_FOLDER/redis_1:/custom \
-d redis:alpine redis-server /custom/redis.conf