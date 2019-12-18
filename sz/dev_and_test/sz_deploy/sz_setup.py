#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    本脚本, 是被部署在目标机器上, 负责 部署和更新/卸载/启动/停止 SZ应用服务的
    目录结构说明
    1. /etc/supervisor/conf.d/  每个应用服务, 一个独立的服务配置文件, 文件名为应用服务名称
    2. /sz/apps/        应用服务的部署目录, 在该目录, 每个应用服务一个独立的子目录, 子目录名为应用服务名称
    3. /sz/configs/     应用服务的配置文件目录, 在该目录, 每个应用服务一个独立的子目录, 子目录名为应用服务名称
"""

import argparse
import io
import os
import shutil
import subprocess
import sys
import time
from typing import List

supervisor_conf_dir = '/etc/supervisor/conf.d/'
apps_dir = '/sz/apps/'
app_configs_dir = '/sz/deploy/configs/'
apps_zip_dir = '/sz/deploy/zips/'


def code_to_chars(code):
    return '\033[' + str(code) + 'm'


class AnsiFore(object):

    def __init__(self):
        # the subclasses declare class attributes which are numbers.
        # Upon instantiation we define instance attributes, which are the same
        # as the class attributes but wrapped with the ANSI escape sequence
        for name in dir(self):
            if not name.startswith('_'):
                value = getattr(self, name)
                setattr(self, name, code_to_chars(value))

    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    RESET = 39

    # These are fairly well supported, but not part of the standard.
    LIGHTBLACK_EX = 90
    LIGHTRED_EX = 91
    LIGHTGREEN_EX = 92
    LIGHTYELLOW_EX = 93
    LIGHTBLUE_EX = 94
    LIGHTMAGENTA_EX = 95
    LIGHTCYAN_EX = 96
    LIGHTWHITE_EX = 97


Fore = AnsiFore()


def info(msg: str):
    print(Fore.YELLOW + '[docker] ' + msg + Fore.RESET)


def warn(msg: str):
    print(Fore.BLUE + '[docker] ' + msg + Fore.RESET)


def err(msg: str):
    print(Fore.RED + '[docker] ' + msg + Fore.RESET)


def shell(cmd: str, exitOnError: bool = False) -> int:
    """
    执行 shell 命令, 如果命令执行失败, 程序结束.

    Parameters
    ----------
    cmd : str
        需要执行的命令字符串
    exitOnError : bool
        命令执行失败的时候, 是否结束退出程序, 默认: True
    """
    info(cmd)
    p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
    for line in io.TextIOWrapper(p.stdout, encoding = 'utf-8'):
        li = line.rstrip()
        print(li)

    ret = p.wait()
    if exitOnError:
        if (ret != 0):
            err(f'operation failed. [return code: {ret}]')
            sys.exit(ret)
    return ret


def rmdir(dir: str, excludes: List[str]):
    if not os.path.exists(dir):
        return
    for name in os.listdir(dir):
        if name not in excludes:
            fpath = os.path.join(dir, name)
            if os.path.isdir(fpath):
                shutil.rmtree(fpath)
            else:
                os.remove(fpath)


def app_home_dir(app_name: str) -> str:
    return f'{apps_dir}{app_name}'


def app_script_path(app_name: str) -> str:
    return f'{apps_dir}{app_name}/bin/{app_name}'


def app_conf_dir(app_name: str) -> str:
    return f'{app_configs_dir}{app_name}'


def app_sz_props_url(app_name: str) -> str:
    return f'{app_conf_dir(app_name)}/sz.app.properties'


def app_supervisord_conf(app_name: str) -> str:
    """
    返回指定的应用服务对应的 supervisor 配置文件路径
    Parameters
    ----------
    app_name : str
        应用服务名称

    Returns
    -------
    str
        返回指定的应用服务对应的 supervisor 配置文件路径
    """
    return f'{supervisor_conf_dir}{app_name}.conf'


def conf_exists(app_name: str) -> bool:
    """
    根据应用服务名称, 判断对应的 配置 是否已经部署

    Parameters
    ----------
    app_name

    Returns
    -------

    """
    conf_dir = app_conf_dir(app_name)
    return os.path.exists(conf_dir)


# noinspection PyListCreation
def create_config_url_prop(app_name: str) -> str:
    """
    为指定的应用服务, 生成 sz.app.properties 文件
    Parameters
    ----------
    app_name : str
        应用服务的名称

    Returns
    ----------
    str
        返回生成的 sz.app.properties 文件路径
    """
    conf_dir = app_conf_dir(app_name)
    lines: List[str] = []
    lines.append(f'config.url = file://{conf_dir}/application.conf')
    lines.append(f'logback.configurationFile = file://{conf_dir}/logback.xml')
    lines.append(f'sz.vertxOptions.url = file://{conf_dir}/vertxOptions.json')
    lines.append(f'sz.zookeeper.config.url = file://{conf_dir}/zookeeper.json')

    fpath = app_sz_props_url(app_name)
    with open(fpath, 'w') as f:
        f.writelines([f'{line}\n' for line in lines])


def app_supervisor_exists(app_name: str) -> bool:
    """
    根据应用服务名称判断对应的 supervisor 配置是否存在
    Parameters
    ----------
    app_name

    Returns
    -------

    """
    conf_path = app_supervisord_conf(app_name)
    return os.path.exists(conf_path)


# noinspection PyListCreation
def setup_app_supervisor(app_name: str):
    conf_path = app_supervisord_conf(app_name)
    lines: List[str] = []
    lines.append(f'[program:{app_name}]')
    lines.append(f'directory={app_home_dir(app_name)}')
    lines.append(f'command={app_script_path(app_name)}')
    lines.append(f'environment=JAVA_OPTS="-Dsz.properties.url=file://{app_sz_props_url(app_name)}"')
    lines.append('autostart=true')
    lines.append('autorestart=true')
    lines.append('startsecs=5')

    with open(conf_path, 'w') as f:
        f.writelines([f'{line}\n' for line in lines])


def start_app(app_name: str):
    if not app_supervisor_exists(app_name):
        info(f'应用服务[{app_name}]未安装')
        return
    shell(f'supervisorctl start {app_name}')


def stop_app(app_name: str):
    if not app_supervisor_exists(app_name):
        info(f'应用服务[{app_name}]未安装')
        return
    shell(f'supervisorctl stop {app_name}')


def status_of(app_name):
    if not app_supervisor_exists(app_name):
        info(f'应用服务[{app_name}]未安装')
        return
    shell(f'supervisorctl status {app_name}')


def supervisord_update():
    shell('supervisorctl update')


def cmd_init(args: argparse.Namespace):
    shell(f'mkdir -p {app_home_dir(args.app_name)}')
    shell(f'mkdir -p {app_conf_dir(args.app_name)}')
    shell(f'mkdir -p {apps_zip_dir}')
    info(f'应用服务[{args.app_name}]目录初始化完毕')


def cmd_install_zip(args: argparse.Namespace):
    app_name = args.app_name
    app_dir = app_home_dir(app_name)
    zip_path = os.path.join(apps_zip_dir, f'{app_name}.zip')
    if not os.path.exists(zip_path):
        raise Exception(f'请先rsync应用包:[{app_name}.zip]到目录: {apps_zip_dir}')

    if app_supervisor_exists(app_name):
        is_upgrade = True
    else:
        is_upgrade = False

    shell(f'mkdir -p {app_dir}')
    shell(f'unzip {zip_path} -d {apps_zip_dir}')
    rmdir(app_dir, excludes = ['logs'])
    shell(f'mv -v {apps_zip_dir}{app_name}/* {app_dir}')
    shell(f'rm -rf {apps_zip_dir}{app_name}')

    # 判断 app 对应的conf/application.conf 文件是否存在, 如果不存在, 则复制当前的一套配置文件
    conf_dir = app_conf_dir(app_name)
    if not os.path.exists(f'{conf_dir}/application.conf'):
        shell(f'cp -rvf {app_dir}/conf/* {conf_dir}')

    # 生成 config_url.properties 文件
    create_config_url_prop(app_name)
    # 生成 supervisord conf
    setup_app_supervisor(app_name)
    supervisord_update()
    if not is_upgrade:
        time.sleep(5)


def cmd_install(args: argparse.Namespace):
    app_name = args.app_name
    app_dir = app_home_dir(app_name)
    # 判断 app 是否已经被 rsync 到对应的目录
    if not os.path.exists(app_dir):
        raise Exception('请先rsync应用到对应目录')

    if app_supervisor_exists(app_name):
        is_upgrade = True
    else:
        is_upgrade = False

    # 判断 app 对应的conf/application.conf 文件是否存在, 如果不存在, 则复制当前的一套配置文件
    conf_dir = app_conf_dir(app_name)
    if not os.path.exists(f'{conf_dir}/application.conf'):
        shell(f'cp -rvf {app_dir}/conf/* {conf_dir}')

    # 生成 config_url.properties 文件
    create_config_url_prop(app_name)
    # 生成 supervisord conf
    setup_app_supervisor(app_name)
    supervisord_update()
    if not is_upgrade:
        time.sleep(5)


def cmd_uninstall(args: argparse.Namespace):
    app_name = args.app_name
    app_dir = app_home_dir(app_name)
    conf_dir = app_conf_dir(app_name)
    supervisord_conf = app_supervisord_conf(app_name)
    zip_path = os.path.join(apps_zip_dir, f'{app_name}.zip')
    stop_app(app_name)
    shell(f'rm -rf {app_dir}')
    shell(f'rm -rf {conf_dir}')
    shell(f'rm -rf {supervisord_conf}')
    shell(f'rm -rf {zip_path}')
    supervisord_update()
    info(f'应用[{app_name}]删除清理完毕')


def cmd_start(args: argparse.Namespace):
    start_app(app_name = args.app_name)


def cmd_stop(args: argparse.Namespace):
    stop_app(app_name = args.app_name)


def cmd_status(args: argparse.Namespace):
    status_of(args.app_name)


def main():
    top_parser = argparse.ArgumentParser(description = 'SZ后端 [应用服务] 安装工具.')

    subcmds = top_parser.add_subparsers(title = '子命令', description = "注: 通过以下子命令指定操作类型, 详细参数用法请在子命令后加上 -h 查看",
                                        dest = 'cmd_name')

    init_parser = subcmds.add_parser('init', help = '在服务器上初始化部署操作需要的目录')
    init_parser.add_argument('--app-name', help = '应用服务名称,必填参数',
                             metavar = 'api_server', required = True)

    # install_parser = subcmds.add_parser('install', help = '在服务器上 部署/更新 应用服务')
    # install_parser.add_argument('--app-name', help = '应用服务名称,必填参数',
    #                             metavar = 'api_server', required = True)

    install_zip_parser = subcmds.add_parser('installzip', help = '由上传/更新的应用程序的zip文件,在服务器上 部署/更新 应用服务')
    install_zip_parser.add_argument('--app-name', help = '应用服务名称,必填参数',
                                    metavar = 'api_server', required = True)

    uninstall_parser = subcmds.add_parser('uninstall', help = '在服务器上 卸载 应用服务')
    uninstall_parser.add_argument('--app-name', help = '应用服务名称,必填参数',
                                  metavar = 'api_server', required = True)

    start_parser = subcmds.add_parser('start', help = '在服务器上 启动 应用服务')
    start_parser.add_argument('--app-name', help = '应用服务名称,必填参数',
                              metavar = 'api_server', required = True)

    stop_parser = subcmds.add_parser('stop', help = '在服务器上 停止 应用服务')
    stop_parser.add_argument('--app-name', help = '应用服务名称,必填参数',
                             metavar = 'api_server', required = True)

    status_parser = subcmds.add_parser('status', help = '在服务器上查看 应用服务 的状态')
    status_parser.add_argument('--app-name', help = '应用服务名称,必填参数',
                               metavar = 'api_server', required = True)

    args = top_parser.parse_args()

    if not args.cmd_name:
        top_parser.print_help()
        sys.exit(1)

    cmd_actions = {
        'init': cmd_init,
        # 'install': cmd_install,
        'installzip': cmd_install_zip,
        'uninstall': cmd_uninstall,
        'start': cmd_start,
        'stop': cmd_stop,
        'status': cmd_status
    }

    action = cmd_actions[args.cmd_name]
    action(args)
    sys.exit(0)


if __name__ == '__main__':
    main()
