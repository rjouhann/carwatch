#!/bin/bash
# Uncomment set command below for code debuging bash
set -x

STATUS=$(ps -ef | grep carwatch.py | grep -v grep | wc -l)
# if number of processes is not 4, killall and restart
test "$STATUS" = "4" || nohup python3 carwatch.py 2>&1 &