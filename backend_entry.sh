#!/bin/sh

cd  "$(dirname $0)"
pwd

python -m pip install EdgeGPT --upgrade

python  bing_chat.py

