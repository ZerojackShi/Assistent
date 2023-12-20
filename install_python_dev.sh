#!/bin/bash

# 获取系统信息
source /etc/os-release

# 判断系统类型
if [ "$ID" == "ubuntu" ] || [ "$ID" == "debian" ]; then
    echo "Installing on Ubuntu/Debian"
    apt-get update
    apt-get install python3-dev
elif [ "$ID" == "centos" ] || [ "$ID" == "rhel" ]; then
    echo "Installing on CentOS/RHEL"
    yum install python3-devel
elif [ "$ID" == "fedora" ]; then
    echo "Installing on Fedora"
    dnf install python3-devel
else
    echo "Unsupported system"
fi
