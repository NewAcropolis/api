#!/bin/bash

function update_book {
    export BOOK_ID=$1

export update_book=$(cat << EOF
    {
        "buy_code": "$2",
        "price": "7.00"
    }
EOF
)

    ./integration_test.sh -ub
}

update_book "20d82304-3dec-4021-b0fe-e42ea4219636" "3XNNKCHUS8FTA"
update_book "17dcfcd3-3ca2-4376-b62a-0955c0e13d55" "7NCM85QGQX6SW"
update_book "e4ed0d22-b7c3-4eb8-b433-476322b9d1a4" "3E8WZGLGMCBYE"
update_book "3d97db87-8e82-4f4c-80c0-595d43f21f11" "CJQEVQEQC923J"
update_book "ef96d2b5-5bf7-4771-b0e7-2d713973c0a8" "C78DW7NZU5K4Q"
update_book "c67d67f9-f573-4a2c-bada-ce0fe326ce77" "7GYHBG4UC8N86"
update_book "6627e350-1c2b-466d-9d5c-bc1291bf0388" "WNEL6YAXEVKL4"
