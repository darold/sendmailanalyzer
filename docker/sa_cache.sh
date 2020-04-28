#!/bin/bash

/usr/local/sendmailanalyzer/sa_cache > /dev/null 2>&1
/usr/bin/pkill -HUP sendmailanalyzer
