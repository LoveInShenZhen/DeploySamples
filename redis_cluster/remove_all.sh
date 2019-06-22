SCRIPT_FILE_FOLDER=$(cd "$(dirname "${BASH_SOURCE-$0}")"; pwd)

docker stop redis_1 redis_2 redis_3 redis_4 redis_5 redis_6
docker rm redis_1 redis_2 redis_3 redis_4 redis_5 redis_6

rm -rf $SCRIPT_FILE_FOLDER/redis_1/*
rm -rf $SCRIPT_FILE_FOLDER/redis_2/*
rm -rf $SCRIPT_FILE_FOLDER/redis_3/*
rm -rf $SCRIPT_FILE_FOLDER/redis_4/*
rm -rf $SCRIPT_FILE_FOLDER/redis_5/*
rm -rf $SCRIPT_FILE_FOLDER/redis_6/*