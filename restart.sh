#!/bin/bash
# Uncomment set command below for code debugging bash
#set -x
echo -e "\nstop carwatch..."
killall python3 # when running on ubuntu
killall Python # when running on mac
secs=5
while [ $secs -gt 0 ]; do
    echo -ne "$secs\033[0K\r"
    sleep 1
    : $((secs--))
done
echo -e "\ndelete python cache folder..."
rm -rf __pycache__
echo -e "\ncarwatch starting..."
nohup python3 carwatch.py 2>&1 &
secs=5
while [ $secs -gt 0 ]; do
    echo -ne "$secs\033[0K\r"
    sleep 1
    : $((secs--))
done
echo -e "\nprocesses..."
ps -ef | grep carwatch | grep -v grep
echo -e "\nlogs..."
tail -20 logs/$(ls -lrt logs/ | tail -1 | awk '{print $9}')