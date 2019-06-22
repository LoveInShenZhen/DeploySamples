#!/bin/bash

SCRIPT_FILE_FOLDER=$(cd "$(dirname "${BASH_SOURCE-$0}")"; pwd)

docker stop redis_1 redis_2 redis_3 sentinel_1 sentinel_2 sentinel_3
docker rm redis_1 redis_2 redis_3 sentinel_1 sentinel_2 sentinel_3

rm -rf $SCRIPT_FILE_FOLDER/redis_1/*
rm -rf $SCRIPT_FILE_FOLDER/redis_2/*
rm -rf $SCRIPT_FILE_FOLDER/redis_3/*

rm -rf $SCRIPT_FILE_FOLDER/sentinel_1/*
rm -rf $SCRIPT_FILE_FOLDER/sentinel_2/*
rm -rf $SCRIPT_FILE_FOLDER/sentinel_3/*

