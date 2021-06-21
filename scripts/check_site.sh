#!/bin/bash
set -o pipefail

echo "Checking: $1"

n=0
until [ $n -ge 10 ]
do
    json=$(curl -s -X GET "$1")
    if [ ! -z "$json" ]; then
        commit=$(echo $json | jq -r '.commit')
        if [ "$commit" = "$GITHUB_SHA" ]; then
            workers=$(echo $json | jq -r '.workers')
            if [ "$workers" = "Running" ]; then
                break
            fi
        fi
    fi

    n=$[$n+1]

    echo "retry $n"
    sleep 10
done

if [ -z "$commit" -o "$commit" != $GITHUB_SHA ]; then
    echo 'failed '$commit
    exit 1
else
    if [ "$workers" != "Running" ]; then
        echo "workers not running"
        exit 1
    fi

    echo 'success '$commit
fi
