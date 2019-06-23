### Redis Cluster 的部署实验记录

#### Redis Cluster 相关资料收集整理
* [深入剖析Redis系列(三) - Redis集群模式搭建与原理详解](https://juejin.im/post/5b8fc5536fb9a05d2d01fb11#heading-14)
* [Redis 集群教程](http://www.redis.cn/topics/cluster-tutorial.html)
* [Redis 集群规范](http://www.redis.cn/topics/cluster-spec.html)

#### 实验说明
* 6个Redis节点, 3主3从
* 注: 
> WARNING: redis-trib.rb is not longer available!
> You should use redis-cli instead.


#### 创建 docker 实例
```
# 创建 redis_1 到 redis_6 共 6 个redis docker 实例
./create_all.sh
```

#### 创建集群
在管理节点
```
docker run --net=kk-dev --rm -it redis:alpine redis-cli --cluster help

docker run --net=kk-dev --rm -it redis:alpine redis-cli --cluster create --cluster-replicas 1 redis_1:6379 redis_2:6379 redis_3:6379 redis_4:6379 redis_5:6379 redis_6:6379
```

* 以上命令执行会报如下错误
```
Node redis_2:6379 replied with error:
ERR Invalid node address specified: redis_1:6379
```

redis cluster 对本机名设别不了，支持的不是很好, 换成ip:port的方式即可解决

* 依次执行以下命令, 查询 redis_1 到 redis_2 的IP
```
docker run --net=kk-dev --rm -it redis:alpine nslookup redis_1
...
docker run --net=kk-dev --rm -it redis:alpine nslookup redis_6
```

* 执行如下命令:
```
docker run --net=kk-dev --rm -it redis:alpine redis-cli --cluster create --cluster-replicas 1 172.18.0.3:6379 172.18.0.4:6379 172.18.0.5:6379 172.18.0.6:6379 172.18.0.7:6379 172.18.0.8:6379
```