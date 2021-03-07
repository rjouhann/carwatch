#!/bin/bash
# Uncomment set command below for code debugging bash
#set -x

killall python3
sleep 5
nohup python3 carwatch.py 2>&1 &> carwatch.log &
sleep 5
tail -15 carwatch.log