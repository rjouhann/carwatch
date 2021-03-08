#!/bin/bash
# Uncomment set command below for code debuging bash
set -x

STATUS=$(ps -ef | grep carwatch.py | grep -v grep | wc -l)
# if number of processes is not 4, killall and restart
test "$STATUS" = "4" || killall python3; cd /home/maxwell/carwatch; nohup python3 carwatch.py 2>&1 &> /home/maxwell/carwatch/carwatch.log &
