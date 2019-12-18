# 开发和测试阶段的部署
---

## 开发阶段的部署需求
* 因为是前后端分离的开发模式, 所以部署一套专门给前端工程师进行联调开发测试使用
* 开发的项目系统虽然是分布式的, 但是需要在开发工程师的单机上完成部署, 不需要集群.
* 要能够快速更新, 避免每次重新构建 docker image 的流程, 节省开发测试时间
* 要有脚本, 打包/更新部署, 一个脚本命令搞定
* 不同的应用服务可以各自独立更新
* 运行在容器中的 MySql, Redis 可以被容器外直接访问
* 运行应用服务器的容器, 提供 ssh 端口, 便于开发人员登录进去查看log, 进行调试
* 采用 Docker Compose 的方式进行部署
* 包含一个 Docker 的数据卷
* 包含一个 Nginx 的容器, 提供前端的静态内容的 host 和 测试环境的配置文件
* 包含一个 Zookeeper 的容器, 提供集群功能

## 开发阶段的部署限制
* 部署仅限在单台物理机上, 否则, docker 跨物理机需要工作在集群模式. 集群模式下的部署, 不在本文的描述范围内. 会提供另外的文档描述.

---

## 操作步骤

### 准备 Docker 的宿主机
* 一台专门用于开发测试的物理机, 内存大点(16 GB 以上), CPU (i7 4核8线程配置以上), SSD硬盘, 512 GB以上 _(总之就是在预算范围内, 配置越高越好)_
* 操作系统: Ubuntu 18.04 LTS

#### 安装 Docker Engine - Community 版
* Docker 引擎的社区版是免费的, 功能满足我们开发测试部署的需求
* 按照 [官方文档](https://docs.docker.com/install/linux/docker-ce/ubuntu/) 的说明安装 Docker 引擎
* 修改 docker daemon 的默认配置
    * 修改docker的默认存储位置及镜像存储位置, 下面的脚本, 我假设配置到 **/mnt/docker_data** 目录. 
        > 1. docker 引擎默认镜像以及容器的数据, 都保存在 **/var/run/docker** 目录下
        > 1. 但是, **/var/run/docker** 是使用的 系统根目录 / 挂载点的空间. 而系统根目录的空间通常都不是很大, 所以我们需要将docker的默认存储位置及镜像存储位置改到一个挂载到大容量磁盘空间的目录下
    * 配置镜像加速器, 这里我们配置成使用 [阿里云docker镜像加速器](https://cr.console.aliyun.com/cn-hangzhou/instances/mirrors) 服务
    * [docker daemon 配置的官方参考文档](https://docs.docker.com/engine/reference/commandline/dockerd/#daemon-configuration-file)

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
    "data-root" : "/mnt/docker_data",
    "registry-mirrors" : ["https://zgvtbml8.mirror.aliyuncs.com"]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```

#### 安装 Docker Compose
* 我们采用 Docker Compose file 来编排我们的单机开发测试环境
* 参考 [官方文档-Install Docker Compose](https://docs.docker.com/compose/install/)

#### 获取测试环境的 Docker Compose file

##### sz 后端应用的通常组成
sz 后端应用, 按照提供的服务类型, 由以下几个部分组成
* MySql (*注: 测试环境, MySql 由一个mysql容器提供服务, 正式站点, 通常使用云服务商提供的云数据库服务*)
* Redis (*注: 仅作为缓存来使用,可靠性没有要求的那么高, 能够快速恢复就行, 所以通常redis使用容器方式提供服务, 正式站点,也是可以选择使用云服务商提供的redis云服务*)

