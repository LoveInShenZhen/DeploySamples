### Redis Sentinel 的部署实验记录
---

#### 采用Redis Sentinel的高可用部署
##### 参考资料整理
* [Redis 的 Sentinel 文档](http://www.redis.cn/topics/sentinel.html)
* [深入剖析Redis系列(二) - Redis哨兵模式与高可用集群](https://juejin.im/post/5b7d226a6fb9a01a1e01ff64)
* [Redis Sentinel机制与用法](https://segmentfault.com/a/1190000002680804)
* [Redis配置](http://www.redis.cn/topics/config.html)
* [Redis configuration](https://redis.io/topics/config)
* [**redis.conf.default**](./redis.conf)
* [Redis 的 Sentinel 文档](http://www.redis.cn/topics/sentinel.html)
* [Redis Sentinel Documentation](https://redis.io/topics/sentinel)
* [**sentinel.conf**](./sentinel.conf)

```shell
# 哨兵sentinel实例运行的端口，默认26379  
port 26379
# 哨兵sentinel的工作目录
dir ./

# 哨兵sentinel监控的redis主节点的 
## ip：主机ip地址
## port：哨兵端口号
## master-name：可以自己命名的主节点名字（只能由字母A-z、数字0-9 、这三个字符".-_"组成。）
## quorum：当这些quorum个数sentinel哨兵认为master主节点失联 那么这时 客观上认为主节点失联了  
# sentinel monitor <master-name> <ip> <redis-port> <quorum>  
sentinel monitor mymaster 127.0.0.1 6379 2

# 当在Redis实例中开启了requirepass <foobared>，所有连接Redis实例的客户端都要提供密码。
# sentinel auth-pass <master-name> <password>  
sentinel auth-pass mymaster 123456  

# 指定主节点应答哨兵sentinel的最大时间间隔，超过这个时间，哨兵主观上认为主节点下线，默认30秒  
# sentinel down-after-milliseconds <master-name> <milliseconds>
sentinel down-after-milliseconds mymaster 30000  

# 指定了在发生failover主备切换时，最多可以有多少个slave同时对新的master进行同步。
# 这个数字越小，完成failover所需的时间就越长；
# 反之，但是如果这个数字越大，就意味着越多的slave因为replication而不可用。
# 可以通过将这个值设为1，来保证每次只有一个slave，处于不能处理命令请求的状态。
# sentinel parallel-syncs <master-name> <numslaves>
sentinel parallel-syncs mymaster 1  

# 故障转移的超时时间failover-timeout，默认三分钟，可以用在以下这些方面：
## 1. 同一个sentinel对同一个master两次failover之间的间隔时间。  
## 2. 当一个slave从一个错误的master那里同步数据时开始，直到slave被纠正为从正确的master那里同步数据时结束。  
## 3. 当想要取消一个正在进行的failover时所需要的时间。
## 4.当进行failover时，配置所有slaves指向新的master所需的最大时间。
##   不过，即使过了这个超时，slaves依然会被正确配置为指向master，但是就不按parallel-syncs所配置的规则来同步数据了
# sentinel failover-timeout <master-name> <milliseconds>  
sentinel failover-timeout mymaster 180000

# 当sentinel有任何警告级别的事件发生时（比如说redis实例的主观失效和客观失效等等），将会去调用这个脚本。
# 一个脚本的最大执行时间为60s，如果超过这个时间，脚本将会被一个SIGKILL信号终止，之后重新执行。
# 对于脚本的运行结果有以下规则：  
## 1. 若脚本执行后返回1，那么该脚本稍后将会被再次执行，重复次数目前默认为10。
## 2. 若脚本执行后返回2，或者比2更高的一个返回值，脚本将不会重复执行。  
## 3. 如果脚本在执行过程中由于收到系统中断信号被终止了，则同返回值为1时的行为相同。
# sentinel notification-script <master-name> <script-path>  
sentinel notification-script mymaster /var/redis/notify.sh

# 这个脚本应该是通用的，能被多次调用，不是针对性的。
# sentinel client-reconfig-script <master-name> <script-path>
sentinel client-reconfig-script mymaster /var/redis/reconfig.sh

```

#### 实验说明
* 3 个Redis Server节点, 1 主 2 从
* 3 个Redis Sentinel节点
* 每个节点一个单独的docker实例,各自独立的配置文件
* 6 个节点部署在同一个 **docker network** 下
* 每个节点都把外面对应的实例的目录(目录名与docker实例的名称相同)映射到内部的 **/custom** 目录, 配置和日志文件都在此目录下
* 创建初期, 配置 **redis_1** 为主节点, 其余2个为从节点
* Redis 主节点 设置名称为 **redis_master**