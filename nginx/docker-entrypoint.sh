#!/bin/bash

# remove default nginx config
rm -f /etc/nginx/conf.d/default.conf

#https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
script=/usr/bin/wait-for-it.sh
chmod +x $script
bash -c "$script webmon:8000 --timeout=300"
