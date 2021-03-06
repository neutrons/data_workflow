#!/bin/bash

# https://github.com/vishnubob/wait-for-it
script=wait-for-it.sh
url=https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh

curl --silent -o $script $url
chmod +x ./$script
bash -c "./$script web:8000 --timeout=300"
