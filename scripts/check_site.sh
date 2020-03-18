#!/bin/bash
set -o pipefail

echo "Checking: $1"

n=0
until [ $n -ge 10 ]
do
    commit=$(curl -s -X GET "$1" | jq -r '.commit')
    if [ ! -z "$commit" ]; then
        break
    fi

    n=$[$n+1]

    echo "retry $n"
    sleep 10
done

if [ -z "$commit" -o "$commit" != $TRAVIS_COMMIT ]; then
    echo 'failed '$commit
    exit 1
else
    echo 'success '$commit
fi
