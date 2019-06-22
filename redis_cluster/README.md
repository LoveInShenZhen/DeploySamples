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
redis-trib.rb create --replicas 1 redis_1:6379 redis_2:6379 redis_3:6379 redis_4:6379 redis_5:6379 redis_6:6379
```