#!/bin/bash
# Uncomment set command below for code debugging bash
#set -x
echo -e "\nstop carwatch..."
killall python3 # when running on ubuntu
killall Python # when running on mac
echo -e "\nbackup log file..."
cp carwatch.log logs/$(date +"%Y-%m-%d")_carwatch.log
echo -e "\nwait 5 secs..."
sleep 5
echo -e "\ncarwatch starting..."
nohup python3 carwatch.py 2>&1 &> carwatch.log &
echo -e "\nwait 5 secs..."
sleep 5
echo -e "\nlogs..."
tail -20 carwatch.log