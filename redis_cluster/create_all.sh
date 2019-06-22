#!/bin/bash

set -e

SCRIPT_FILE_FOLDER=$(cd "$(dirname "${BASH_SOURCE-$0}")"; pwd)

NETWORK='kk-dev'

function create_docker() {
    local dockerName=$1
    mkdir -p $SCRIPT_FILE_FOLDER/$dockerName
    cp $SCRIPT_FILE_FOLDER/sample-redis.conf $SCRIPT_FILE_FOLDER/$dockerName/redis.conf
    docker run --name $dockerName --hostname $dockerName --net=$NETWORK -v $SCRIPT_FILE_FOLDER/$dockerName:/custom -d redis:alpine redis-server /custom/redis.conf
}

create_docker redis_1
create_docker redis_2
create_docker redis_3
create_docker redis_4
create_docker redis_5
create_docker redis_6