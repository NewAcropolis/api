#!/bin/bash
set +e

function setupURLS {
    if [ "$1" = "dev" ]; then
        export api_server="${API_BASE_URL}/dev"
    elif [ "$1" = "preview" ]; then
        export api_server="${API_BASE_URL}/preview"
    else
        export api_server='http://localhost:5000'
    fi
    export username=$ADMIN_CLIENT_ID
    export password=$ADMIN_CLIENT_SECRET

    echo "*** running on - " $api_server
}

function setupAccessToken {
    export TKN=$(curl -X POST $api_server'/auth/login' \
    -H "Content-Type: application/json" \
    -X "POST" \
    -d '{"username": "'$username'","password": "'$password'"}' | jq -r '.access_token')
    echo $TKN
}

function GetFees {
    echo "*** Get fees ***"

    curl -X GET $api_server'/fees' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" | jq .
}

function GetEventTypes {
    echo "*** Get event_types ***"

    curl -X GET $api_server'/event_types' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

event_types=$(cat  << EOF
    [
        {"id":"1","EventType":"Talk","Fees":"5","ConcFees":"3","EventDesc":"","EventFilename":null},
        {"id":"2","EventType":"Introductory Course","Fees":"120","ConcFees":"85","EventDesc":"","EventFilename":null},
        {"id":"3","EventType":"Seminar","Fees":"0","ConcFees":null,"EventDesc":"","EventFilename":null},
        {"id":"4","EventType":"Ecological event","Fees":"0","ConcFees":null,"EventDesc":"","EventFilename":null}
    ]
EOF
)

function ImportEventTypes {
    echo "*** Import event types ***"

    curl -X POST $api_server'/event_types/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d @data/event_types.json
}

function GetSpeakers {
    echo "*** Get speakers ***"

    curl -X GET $api_server'/speakers' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" | jq .
}

speakers=$(cat  << EOF
    [ 
        {"title": "Mrs", "name": "Sabine Leitner"},
        {"name": "Sabine Leitner, Director of New Acropolis UK", "parent_name": "Sabine Leitner"},
        {"title": "Mr", "name": "Julian Scott"},
        {"title": "Mr", "name": "James Chan"},
        {"name": "James Chan Lee", "parent_name": "James Chan"}
    ]
EOF
)

function ImportSpeakers {
    echo "*** Import speakers ***"

    curl -X POST $api_server'/speakers/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d @data/speakers.json
}


function GetVenues {
    echo "*** Get venues ***"

    curl -X GET $api_server'/venues' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" | jq .
}


venues=$(cat  << EOF
    [
        {
            "id": "1",
            "name": "",
            "address": "19 Compton Terrace N1 2UN, next door to Union Chapel.",
            "tube": "Highbury & Islington (Victoria Line), 2 minutes walk",
            "bus": "Bus routes 4, 19, 30, 43 & 277 stop nearby"
        },
        {
            "id": "2",
            "name": "Bristol",
            "address": "Caf\u00e9 Revival, 56 Corn Street, Bristol, BS1 1JG",
            "tube": "",
            "bus": ""
        },
        {
            "id": "3",
            "name": "Bristol",
            "address": "Hamilton House, 80 Stokes Croft, Bristol, BS1 3QY",
            "tube": "",
            "bus": ""
        }
    ]
EOF
)

function ImportVenues {
    echo "*** Import venues ***"

    curl -X POST $api_server'/venues/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d @data/venues.json
}

events=$(cat  << EOF
    [
        {
            "id": "1",
            "BookingCode": "",
            "MemberPay": "0",
            "Approved": "y",
            "Type": "1",
            "Title": "Philosophy of Economics",
            "SubTitle": "",
            "Description": "How Plato and Confucius can help understand economic development",
            "venue": "1",
            "Speaker": "Sabine Leitner",
            "MultiDayFee": "0",
            "MultiDayConcFee": "0",
            "StartDate": "2004-09-20 19:30:00",
            "StartDate2": "0000-00-00 00:00:00",
            "StartDate3": "0000-00-00 00:00:00",
            "StartDate4": "0000-00-00 00:00:00",
            "EndDate": "0000-00-00 00:00:00",
            "Duration": "0",
            "Fee": "4",
            "ConcFee": "2",
            "Pub-First-Number": "3",
            "Mem-SignOn-Number": "12",
            "ImageFilename": "2004/Economics.jpg",
            "WebLink": "",
            "LinkText": null,
            "MembersOnly": "n",
            "RegisterStartOnly": "0",
            "SoldOut": null
        },
        {
            "id": "2",
            "BookingCode": "",
            "MemberPay": "0",
            "Approved": "y",
            "Type": "2",
            "Title": "Study Philosophy",
            "SubTitle": "",
            "Description": "16-week course introducing the major systems of thoughts from the East and West",
            "venue": "1",
            "Speaker": "Julian Scott",
            "MultiDayFee": null,
            "MultiDayConcFee": "0",
            "StartDate": "2004-09-29 19:30:00",
            "StartDate2": "0000-00-00 00:00:00",
            "StartDate3": "0000-00-00 00:00:00",
            "StartDate4": "0000-00-00 00:00:00",
            "EndDate": "0000-00-00 00:00:00",
            "Duration": "0",
            "Fee": "96",
            "ConcFee": "64",
            "Pub-First-Number": "1",
            "Mem-SignOn-Number": "0",
            "ImageFilename": "2004/WinterCourse.jpg",
            "WebLink": "",
            "LinkText": "",
            "MembersOnly": "n",
            "RegisterStartOnly": "0",
            "SoldOut": null
        }
    ]
EOF
)

function ExtractSpeakers {
    echo "*** Extract Speakers ***"

    curl -X POST $api_server'/events/extract-speakers' \
    -H "Accept: application/json" \
    -d @data/events.json
}

function ImportEvents {
    echo "*** Import Events ***"

    curl -X POST $api_server'/events/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d @data/events.json
}

function GetEvents {
    echo "*** Get Events ***"

    curl -X GET $api_server'/events' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function Logout {
    echo "*** Logout ***"

    curl -X DELETE $api_server'/auth/logout' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" | jq .
}

# API calls
# GetFees
# GetEventTypes
# PostSpeakers
# GetSpeakers
# ImportVenues
# GetVenues
# ExtractSpeakers
# ImportEvents
# Logout
# GetFees

# setup 
setupURLS "$2"
setupAccessToken

if [ -z $1 ]; then
    arg="-a"
else
    arg=$1
fi

case "$arg" in

        -a) echo "Run all"
            GetFees
            GetEventTypes
            ImportEventTypes
            ImportSpeakers
            GetSpeakers
            ImportVenues
            GetVenues
            ExtractSpeakers
            Logout
            GetFees
        ;;

        -et)
            GetEventTypes
        ;;

        -iet)
            ImportEventTypes
        ;;

        -iv)
            ImportVenues
        ;;

        -s)
            GetSpeakers
        ;;

        -is)
            ImportSpeakers
        ;;

        -es)
            ExtractSpeakers
        ;;

        -ie)
            ImportEvents
        ;;

        -e)
            GetEvents
        ;;

        -x)
            Logout
        ;;

esac
