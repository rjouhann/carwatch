#!/bin/bash
# Uncomment set command below for code debuging bash
set -x

STATUS=$(ps -ef | grep carwatch.py | grep -v grep | wc -l)
# if number of processes is not 4, killall and restart
test "$STATUS" = "4" || nohup ./restart.sh 2>&1 &