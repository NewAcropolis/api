#!/bin/bash
set -o pipefail

echo "Checking: $1"

n=0
until [ $n -ge 20 ]
do
    json=$(curl -s -X GET "$1")
    if [ ! -z "$json" ]; then
        commit=$(echo $json | jq -r '.commit')
        if [ "$commit" = "$GITHUB_SHA" ]; then
            if [ "$2" = "no_workers" ]; then
                echo "ok"
                exit 0
            fi
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
    echo 'failed '$commit' expecting '$GITHUB_SHA
    exit 1
else
    if [ "$workers" != "Running" ]; then
        echo "workers not running"
        exit 1
    fi

    echo 'success '$commit
fi
