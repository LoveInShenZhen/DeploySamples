#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import io
import os
import subprocess
import sys
from typing import List

import paramiko
from colorama import Fore
from paramiko import SSHClient

ssh_client: SSHClient = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

dest_host = 'localhost'
ssh_port = 10022
sshkey = os.path.expanduser('~/.ssh/id_rsa')

supervisor_conf_dir = '/etc/supervisor/conf.d/'
apps_dir = '/sz/apps/'
app_configs_dir = '/sz/deploy/configs/'
apps_zip_dir = '/sz/deploy/zips/'
nginx_conf_dir = '/etc/nginx/conf.d/'


def app_home_dir(app_name: str) -> str:
    return f'{apps_dir}{app_name}'


def app_script_path(app_name: str) -> str:
    return f'{apps_dir}{app_name}/bin/{app_name}'


def app_conf_dir(app_name: str) -> str:
    return f'{app_configs_dir}{app_name}'


def app_sz_props_url(app_name: str) -> str:
    return f'{app_conf_dir(app_name)}/sz.app.properties'


def deploy_setup_script():
    script_dir = os.path.dirname(__file__)
    script_path = os.path.join(script_dir, 'sz_setup.py')
    rsync(local_path = script_path, dest_path = '/usr/local/bin/', hideOutput = True)


def deploy_app_zip(args: argparse.Namespace):
    app_prj_path = args.prj_dir
    app_name = os.path.basename(app_prj_path)
    info(f'编译构建应用[{app_name}]')
    os.chdir(app_prj_path)
    shell(f'gradle build')

    ssh_cmd(f'/usr/local/bin/sz_setup.py init --app-name {app_name}')
    ssh_cmd(f'/usr/local/bin/sz_setup.py stop --app-name {app_name}')

    local_path = os.path.join(
        app_prj_path, 'build/distributions', f'{app_name}.zip')
    rsync(local_path, apps_zip_dir)

    ssh_cmd(f'/usr/local/bin/sz_setup.py installzip --app-name {app_name}')
    ssh_cmd(f'/usr/local/bin/sz_setup.py start --app-name {app_name}')
    ssh_cmd(f'supervisorctl status {app_name}')
    info(f"应用[{app_name}]在目标机器上部署完毕")


def deploy_app(args: argparse.Namespace):
    """
    部署"应用"到目标服务器

    Parameters
    ----------
    args :
           部署参数
    """
    app_prj_path = os.path.expanduser(args.prj_dir)
    app_name = os.path.basename(app_prj_path)
    info(f'编译构建应用[{app_name}]')
    os.chdir(app_prj_path)
    shell(f'gradle installDist')

    ssh_cmd(f'/usr/local/bin/sz_setup.py init --app-name {app_name}')
    ssh_cmd(
        f'/usr/local/bin/sz_setup.py stop --app-name {app_name}', exitOnError = False)

    local_path = os.path.join(app_prj_path, 'build/install', app_name)
    rsync(local_path, apps_dir, excluded_del = ['logs/', 'h2db/'])

    ssh_cmd(f'/usr/local/bin/sz_setup.py install --app-name {app_name}')
    ssh_cmd(f'/usr/local/bin/sz_setup.py start --app-name {app_name}')
    ssh_cmd(f'supervisorctl status {app_name}')
    info(f"应用[{app_name}]在目标机器上部署完毕")


def deploy_conf(args: argparse.Namespace):
    info("部署运行环境配置文件")
    app_prj_path = os.path.expanduser(args.prj_dir)
    app_name = os.path.basename(app_prj_path)
    local_conf_dir = f'{os.path.expanduser(args.conf_dir)}/*'
    dest_conf_dir = app_conf_dir(app_name)
    dest_app_conf_dir = f'{app_home_dir(app_name)}/conf'

    ssh_cmd(f'/usr/local/bin/sz_setup.py init --app-name {app_name}')
    rsync(local_conf_dir, dest_conf_dir, delete = False)
    rsync(local_conf_dir, dest_app_conf_dir, delete = False)

    ssh_cmd(f'/usr/local/bin/sz_setup.py stop --app-name {app_name}')
    ssh_cmd(f'/usr/local/bin/sz_setup.py start --app-name {app_name}')
    ssh_cmd(f'/usr/local/bin/sz_setup.py status --app-name {app_name}')
    info(f"应用[{app_name}]的运行环境配置文件在目标机器上部署完毕")


def undeploy(args: argparse.Namespace):
    app_prj_path = args.prj_dir
    app_name = os.path.basename(app_prj_path)
    info(f"开始清理删除部署在目标服务器的应用[{app_name}]")
    ssh_cmd(f'/usr/local/bin/sz_setup.py uninstall --app-name {app_name}')
    info(f"应用[{app_name}]在目标机器上清理完毕")


def cmd_list_nginx_conf(args: argparse.Namespace):
    ssh_cmd(f'/usr/local/bin/sz_setup.py list_nginx_conf')


def cmd_dump_nginx_conf(args: argparse.Namespace):
    conf_name = args.conf
    conf_path = os.path.join(nginx_conf_dir, conf_name)
    ssh_cmd(f'cat {conf_path}', showPrefix = False)


def cmd_install_nginx_conf(args: argparse.Namespace):
    """
    * 将指定的 nginx 配置文件上传到目标服务器的 /etc/nginx/conf.d 目录下
    * 在目标服务器上检查配置文件是否合法有效
    * 检查通过, 则重启 nginx 服务
    * 检查不通过, 则删除此配置文件

    Parameters
    ----------
    args : 命令行参数对象
    """
    conf_path: str = args.conf
    if not os.path.exists(conf_path):
        err(f'File [{conf_path}] does not exists.')
        sys.exit(-1)
    if not conf_path.endswith('.conf'):
        err('File extension name must be ".conf".')
        sys.exit(-1)
    conf_name = os.path.basename(conf_path)
    rsync(conf_path, nginx_conf_dir)
    ssh_cmd(f'/usr/local/bin/sz_setup.py test_nginx_conf --conf {conf_name}')


def info(msg: str):
    print(Fore.GREEN + '==> ' + msg + Fore.RESET)


def warn(msg: str):
    print(Fore.YELLOW + '==> ' + msg + Fore.RESET)


def err(msg: str):
    print(Fore.RED + '==> ' + msg + Fore.RESET)


def shell(cmd: str, exitOnError: bool = True, useShell: bool = True, hideOutput: bool = False):
    """
    执行 shell 命令, 如果命令执行失败, 程序结束.

    Parameters
    ----------
    cmd : str
        需要执行的命令字符串
    exitOnError : bool
        命令执行失败的时候, 是否结束退出程序, 默认: True
    useShell : bool
        是否使用shell, 默认为 True
    hideOutput : bool
        是否隐藏输出, 默认为 False, 不隐藏
    """
    # info(cmd)
    # ret = os.system(cmd)
    # if exitOnError:
    #     if (ret != 0):
    #         err('Deploy operation failed.')
    #         sys.exit(ret)
    info(cmd)
    p = subprocess.Popen(cmd, stdout = subprocess.PIPE,
                         stderr = subprocess.STDOUT, shell = useShell)
    if not hideOutput:
        for line in io.TextIOWrapper(p.stdout, encoding = 'utf-8'):
            li = line.rstrip()
            print(li)

    ret = p.wait()
    if exitOnError:
        if (ret != 0):
            err(f'operation failed. [return code: {ret}]')
            sys.exit(ret)
    return ret


def ssh_cmd(cmd: str, exitOnError: bool = True, showPrefix: bool = True) -> (List[str], int):
    """
    在目标主机上, 通过 ssh 执行命令.

    Parameters
    ----------
    cmd : str
        要在远程ssh主机上执行的命令字符串
    exitOnError : Bool
        命令执行失败的时候, 是否结束退出程序, 默认: True

    Returns
    ----------
    (List[str], int)
        元组: (命令输出[列表], exit_status)
    """
    info(f'[ssh] {cmd}')
    global ssh_client
    cmd_txt = f'{cmd} 2>&1'
    _, stdout, _ = ssh_client.exec_command(cmd_txt)
    output_lines = []
    for line in io.TextIOWrapper(stdout, encoding = 'utf-8'):
        li = line.rstrip()
        output_lines.append(li)
        if showPrefix:
            print(Fore.BLUE + '==> ' + Fore.RESET + li)
        else:
            print(li)
    ret = stdout.channel.recv_exit_status()
    if exitOnError:
        if ret != 0:
            sys.exit(ret)
    return (output_lines, ret)


def connect_ssh(host: str, port: int, ssh_key: str):
    global ssh_client, dest_host, ssh_port, sshkey
    dest_host = host
    ssh_port = port
    sshkey = os.path.expanduser(ssh_key)
    ssh_client.connect(hostname = host, port = port,
                       username = 'root', key_filename = sshkey)


def rsync(local_path: str, dest_path: str, delete: bool = True, excluded_del: List[str] = [], hideOutput: bool = False):
    """
    向目标主机, 通过 rsync 命令传输文件.

    Parameters
    ----------
    local_path : str
        要传输到目标主机的文件/目录在本机上的路径
    dest_path : str
        要传输到目标主机的文件/目录在目标主机上的路径
    delete : bool
        是否删除目标目录比源目录多余的文件, 默认: True, 删除多余文件
    excluded_del : List[str]
        目标机器上本应该被删除的文件, 按照此参数进行排除
    hideOutput : bool
        是否隐藏输出内容, 默认不隐藏
    """
    global dest_host, ssh_port, sshkey
    if delete and len(excluded_del) > 0:
        excluded_expr = ' '.join([f'--exclude "{it}"' for it in excluded_del])
        cmd = f'rsync -av --delete {excluded_expr} --progress -e "ssh -i {os.path.expanduser(sshkey)} -p {ssh_port}" {local_path} root@{dest_host}:{dest_path}'
    else:
        cmd = f'rsync -av --progress -e "ssh -i {os.path.expanduser(sshkey)} -p {ssh_port}" {local_path} root@{dest_host}:{dest_path}'
    shell(cmd, hideOutput = hideOutput)


def main():
    top_parser = argparse.ArgumentParser(description = 'SZ 后端 [应用]/[配置文件] 部署工具.')

    subcmds = top_parser.add_subparsers(title = '子命令', description = "注: 通过以下子命令指定部署/操作类型, 详细参数用法请在子命令后加上 -h 查看",
                                        dest = 'cmd_name')

    deployapp_parser = subcmds.add_parser('app', help = '部署[应用]到目标服务器')
    deployapp_parser.add_argument('--prj-dir', help = '[应用]对应的gradle工程目录路径,必填参数',
                                  metavar = '~/work/vertx-web-mutli/api_server', required = True)
    deployapp_parser.add_argument(
        '--host', help = '目标主机IP,默认:127.0.0.1', default = "127.0.0.1", metavar = "127.0.0.1")
    deployapp_parser.add_argument('--port', help = '目标主机ssh服务端口,默认:10022', type = int, default = 10022,
                                  metavar = '10022')
    deployapp_parser.add_argument('--ssh-key', help = '用于ssh登录的证书路径,默认:~/.ssh/id_rsa', default = '~/.ssh/id_rsa',
                                  metavar = '~/.ssh/id_rsa')

    deployconf_parser = subcmds.add_parser('conf', help = '部署[一组配置文件]到目标服务器')
    deployconf_parser.add_argument('--conf-dir', help = '配置文件目录的路径,必填参数', metavar = '~/work/test_env/api_server/conf',
                                   required = True)
    deployconf_parser.add_argument('--prj-dir', help = '[应用]对应的gradle工程目录路径,必填参数',
                                   metavar = '~/work/vertx-web-mutli/api_server', required = True)
    deployconf_parser.add_argument(
        '--host', help = '目标主机IP,默认:127.0.0.1', default = "127.0.0.1", metavar = "127.0.0.1")
    deployconf_parser.add_argument('--port', help = '目标主机ssh服务端口,默认:10022', type = int, default = 10022,
                                   metavar = '10022')
    deployconf_parser.add_argument('--ssh-key', help = '用于ssh登录的证书路径,默认:~/.ssh/id_rsa', default = '~/.ssh/id_rsa',
                                   metavar = '~/.ssh/id_rsa')

    undeploy_parser = subcmds.add_parser(
        'undeploy', help = '清理删除部署在目标服务器的[应用]和[配置]')
    undeploy_parser.add_argument('--prj-dir', help = '[应用]对应的gradle工程目录路径,必填参数',
                                 metavar = '~/work/vertx-web-mutli/api_server', required = True)
    undeploy_parser.add_argument(
        '--host', help = '目标主机IP,默认:127.0.0.1', default = "127.0.0.1", metavar = "127.0.0.1")
    undeploy_parser.add_argument('--port', help = '目标主机ssh服务端口,默认:10022', type = int, default = 10022,
                                 metavar = '10022')
    undeploy_parser.add_argument('--ssh-key', help = '用于ssh登录的证书路径,默认:~/.ssh/id_rsa', default = '~/.ssh/id_rsa',
                                 metavar = '~/.ssh/id_rsa')

    list_nginx_conf_parser = subcmds.add_parser(
        'list_nginx_conf', help = '列出服务器上 /etc/nginx/conf.d/ 下所有的配置文件')
    list_nginx_conf_parser.add_argument(
        '--host', help = '目标主机IP,默认:127.0.0.1', default = "127.0.0.1", metavar = "127.0.0.1")
    list_nginx_conf_parser.add_argument('--port', help = '目标主机ssh服务端口,默认:10022', type = int, default = 10022,
                                        metavar = '10022')
    list_nginx_conf_parser.add_argument('--ssh-key', help = '用于ssh登录的证书路径,默认:~/.ssh/id_rsa', default = '~/.ssh/id_rsa',
                                        metavar = '~/.ssh/id_rsa')

    dump_nginx_conf_parser = subcmds.add_parser('dump_nginx_conf', help = '输出指定的 nginx 配置文件内容')
    dump_nginx_conf_parser.add_argument('--conf', help = '指定的 nginx 配置文件名称(仅文件名)', required = True)
    dump_nginx_conf_parser.add_argument(
        '--host', help = '目标主机IP,默认:127.0.0.1', default = "127.0.0.1", metavar = "127.0.0.1")
    dump_nginx_conf_parser.add_argument('--port', help = '目标主机ssh服务端口,默认:10022', type = int, default = 10022,
                                        metavar = '10022')
    dump_nginx_conf_parser.add_argument('--ssh-key', help = '用于ssh登录的证书路径,默认:~/.ssh/id_rsa', default = '~/.ssh/id_rsa',
                                        metavar = '~/.ssh/id_rsa')

    install_nginx_conf_parser = subcmds.add_parser(
        'install_nginx_conf', help = '部署/更新指定的 nginx 配置文件')
    install_nginx_conf_parser.add_argument('--conf', help = '需要部署的 nginx 配置文件路径', required = True)
    install_nginx_conf_parser.add_argument(
        '--host', help = '目标主机IP,默认:127.0.0.1', default = "127.0.0.1", metavar = "127.0.0.1")
    install_nginx_conf_parser.add_argument('--port', help = '目标主机ssh服务端口,默认:10022', type = int, default = 10022,
                                           metavar = '10022')
    install_nginx_conf_parser.add_argument('--ssh-key', help = '用于ssh登录的证书路径,默认:~/.ssh/id_rsa',
                                           default = '~/.ssh/id_rsa',
                                           metavar = '~/.ssh/id_rsa')

    cmd_actions = {
        'app': deploy_app_zip,
        'conf': deploy_conf,
        'undeploy': undeploy,
        'list_nginx_conf': cmd_list_nginx_conf,
        'dump_nginx_conf': cmd_dump_nginx_conf,
        'install_nginx_conf': cmd_install_nginx_conf,
    }

    args = top_parser.parse_args()

    if not args.cmd_name:
        top_parser.print_help()
        sys.exit(1)

    action = cmd_actions[args.cmd_name]
    connect_ssh(host = args.host, port = args.port, ssh_key = args.ssh_key)
    deploy_setup_script()

    action(args)


if __name__ == '__main__':
    main()
