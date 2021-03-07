#!/bin/bash
# Uncomment set command below for code debugging bash
#set -x
echo -e "\nstop carwatch..."
killall python3
echo -e "\nwait 5 secs..."
sleep 5
echo "\ncarwatch starting..."
nohup python3 carwatch.py 2>&1 &> carwatch.log &
echo -e "\nwait 5 secs..."
sleep 5
echo -e "\nlogs..."
tail -20 carwatch.log