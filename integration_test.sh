#!/bin/bash
set +e

function setupURLS {
    if [ "$1" = "dev" ]; then
        export api_server="${API_BASE_URL}"
        export username=$ADMIN_CLIENT_ID_development
        export password=$ADMIN_CLIENT_SECRET_development
    elif [ "$1" = "preview" ]; then
        export api_server="${API_BASE_URL}"
        export username=$ADMIN_CLIENT_ID_preview
        export password=$ADMIN_CLIENT_SECRET_preview
    elif [ "$1" = "live" ]; then
        export api_server="${API_BASE_URL}"
        export username=$ADMIN_CLIENT_ID_live
        export password=$ADMIN_CLIENT_SECRET_live
    else
        export api_server='http://localhost:5000'
        export username=$ADMIN_CLIENT_ID
        export password=$ADMIN_CLIENT_SECRET
    fi

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

function GetEvents {
    echo "*** Get events ***"

    curl -X GET $api_server'/events' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function GetLimitedEvents {
    echo "*** Get limited events ***"

    curl -X GET $api_server'/events/limit/20' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function DeleteEvent {
    echo "*** Delete event ***"

    curl -X DELETE $api_server'/event/'$event_id \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function GetEventsPastYear {
    echo "*** Get events past year ***"

    curl -X GET $api_server'/events/past_year' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function GetFutureEvents {
    echo "*** Get future events ***"

    curl -X GET $api_server'/events/future' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
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
        {"id":"4","EventType":"Ecological event","Fees":"0","ConcFees":null,"EventDesc":"","EventFilename":null},
        {"id":"5","EventType":"Excursion","Fees":"0","ConcFees":null,"EventDesc":"","EventFilename":"TextExcursion.gif"},
        {"id":"6","EventType":"Exhibition","Fees":"0","ConcFees":null,"EventDesc":"","EventFilename":null},
        {"id":"7","EventType":"Meeting","Fees":"0","ConcFees":null,"EventDesc":"","EventFilename":null},
        {"id":"8","EventType":"Cultural Event","Fees":"0","ConcFees":null,"EventDesc":"","EventFilename":"TextCultural.gif"},
        {"id":"9","EventType":"Short Course","Fees":"0","ConcFees":null,"EventDesc":null,"EventFilename":null},
        {"id":"10","EventType":"Workshop","Fees":"0","ConcFees":null,"EventDesc":null,"EventFilename":null}
    ]
EOF
)

function ImportEventTypes {
    echo "*** Import event types ***"

    curl -X POST $api_server'/event_types/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$event_types"
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

function ImportEmails {
    echo "*** Import Emails ***"

    curl -X POST $api_server'/emails/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d @data/emails.json
}

function ImportEmailToMembers {
    echo "*** Import Email to Members ***"
    if [ -z $1 ]; then
        json_file=emailmailings.json
    else
        json_file=$1
    fi

    echo "Importing "$json_file

    curl -X POST $api_server'/emails/members/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d @data/$json_file
}

event=$(cat  << EOF
    {
        "event_dates": [{"event_date": "2019-04-01 19:00:00"}],
        "event_type_id":"351526a8-1e56-4b7b-a600-f9a20715e2b4",
        "title": "Test title",
        "description": "Test description",
        "venue_id": "181d885e-fee4-4d58-be44-9a89a0d8ba67",
        "image_filename": "test_img.png",
        "image_data": "iVBORw0KGgoAAAANSUhEUgAAADgAAAAsCAYAAAAwwXuTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAEMElEQVRoge2ZTUxcVRTH/+fed9+bDxFEQUCmDLWbtibWDE2MCYGa6rabykITA7pV6aruNGlcGFe6c2ui7k1cmZp0YGdR2pjqoklBpkCVykem8/HeffceF8MgIC3YvDczNP0ls5l3cuf8cuee++65wGMe09LQQQP5xkkXJ4rpjYU40zkY7UcA/NZWopM3gv1iHyg4M5NTuRPrPf56cJ4ETgsHg1ZHludDIxQQBphLpOiasfTrtVvPXB4a+nnPzO4rWFnOjroJO25CfkF5UAgBrTm+rP8nyiHAAzgALNNsCHzjdXZdIdop+h/BmzePeYPd+lXW9pIj4eqAwa3jtSeuV9PQhvKqKC7S4Hy1/myHIHNfSq84nyqXR7Tf+mK7cdMEU6G89O2HlLldAQCxPSD4U55TaRoJqodPDgCCEkOmaMR38HH9uy3B4tLAceViUt8zzckuInTJwE3QmerikbPApuDaXLbDk3yBCMnDOHPbYQYISEiJC7x6tF0AQNrzn1dpejnwD7ndJoHPcBKc0WX/uACAkOUr7Ntm5xUp2mdYQR8RAPBa5vqjMnvbceTmGoxajqj2aTah2bVNRAIB1pBmrm3AzfaMXNBNEqQU3wp2Jo2lWVKbok0yjWUGjWGjeuevyM6Fd2HxgbW4Kh1qiqgT07gEAEQwwO08M6bDu9lhhnnbcWiIBNCod9y4BHdABAvM55kxFa5khtmIcaVsDhS/aEME6xCBgcIUgCm9lBlmBxNKUQ4UfSWvE/0aPCCqrzDtdhfeCUO8pzX94qp/jz1R0jTBOqq7MO12L0xUfXq/WsWsktEWoqYL1kn2FaaSvYXxUlVOWkNhVJINXYMPggGqLg+MSrJvMlhGVXhaQlCvDJzRlicSyr5YKzjRjd00QWbI8E7/MEkxIaU9BQkEQfSVtOGCvJDps2l6w6ziNSFtRiiObYsAGihYWhnoVYbHNPF5pfhJ6zMMA2HMx7S4BLeyvvdXtsexdgzWjqkU2sIKIyjH9Kt7EL0gA5aRKC4f61LQ47DmnJdCm26wWB0CAP9O//UoR+TaPqbdJJLN7q/GMoNCsgPACar7RseOAGq9iyhhRss0jgUAaI3FVuihRI3rUU1QWL6kYniTbyauR/Cr+FIAgEp5v4dVKsRxXGkGShECjT88Nl8JAKDOWxvG4HNmVB6FvyolBIyhr6lvqbx1XEo8t3BZB/hCPRFxxWkwtSs0zid7wu+BXedB91nznSlx3k0fzml00wTjU75QFBeJlsrAHje8PJdN6Db7mZI8AsTXK4kSIQBH0f43vHWYc8pfXRl1gLcE8UukAF1uPVGVItgKw0oqGiM/8bqe/nHfO/rtzMzk1Kmjd8+SNKd1hV4nQKIVPAlgwKgk/6DL8qpnwp+of/Hv+4QejLW5bEeHsLQRXZoPTTuAdSv4qcH59f1i/wGycsTRKGME7gAAAABJRU5ErkJggg=="
    }
EOF
)

event_update=$(cat  << EOF
    {
        "sub_title": "Test title",
        "event_state": "ready"
    }
EOF
)

event_rejected=$(cat  << EOF
    {
        "event_state": "rejected",
        "reject_reasons": [
            {
                "reason": "Better title needed"
            }
        ]
    }
EOF
)

function CreateEvent {
    echo "*** Create Event ***"

    curl -X POST $api_server'/event' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$event"
}

function UpdateEvent {
    echo "*** Update Event ***"

    curl -X POST $api_server'/event/df3baba5-e6fa-4c81-b0bf-c56c08c79c94' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$event_update"
}

function UpdateEventRejected {
    echo "*** Update Event Rejected ***"

    curl -X POST $api_server'/event/df3baba5-e6fa-4c81-b0bf-c56c08c79c94' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$event_rejected"
}

function ImportTargetEvents {
    if [ -z $EVENT_TARGET ]; then
        echo "*** No Target Event Specified ***"
        exit
    fi

    echo "*** Import Target Event $EVENT_TARGET.json ***"

    curl -X POST $api_server'/events/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d @data/$EVENT_TARGET.json
}

function ImportArticles {
    echo "*** Import articles ***"

    curl -X POST $api_server'/articles/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d @data/articles.json
}

function GetArticles {
    echo "*** Get articles ***"

    curl -X GET $api_server'/articles' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function GetArticlesSummary {
    echo "*** Get articles summary ***"

    curl -X GET $api_server'/articles/summary' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

admin_user=$(cat  << EOF
    {"email":"$ADMIN_USER","access_area":",email,","name":"Admin","active":true}
EOF
)

function CreateAdminUser {
    echo "*** Create admin user ***"

    curl -X POST $api_server'/user' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$admin_user"
}

function GetUsers {
    echo "*** Get users ***"

    curl -X GET $api_server'/users' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" 
}

function GetMembers {
    echo "*** Get members ***"

    curl -X GET $api_server'/members' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" 
}

function GetUserByEmail {
    echo "*** Get user by email ***"

    curl -X GET $api_server'/user/'$OTHER_USER \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" 
}

email=$(cat  << EOF
    {
        "event_id": "$EVENT_ID",
        "details": "<div>Some additional details</div>",
        "extra_txt": "<div>Some more information about the event</div>",
        "replace_all": false,
        "email_type": "event"
    }
EOF
)

preview_email="%7B%22details%22%3A%20%22%3Cdiv%3ESome%20additional%20details%3C/div%3E%22%2C%20%22email_type%22%3A%20%22event%22%2C%20%22event_id%22%3A%20%22$EVENT_ID%22%2C%20%22extra_txt%22%3A%20%22%3Cdiv%3ESome%20more%20information%20about%20the%20event%3C/div%3E%22%2C%20%22replace_all%22%3A%20false%7D"

update_email=$(cat  << EOF
    {
        "email_state": "ready", 
        "email_type": "event", 
        "event_id": "$EVENT_ID"
    }
EOF
)

update_email_approved=$(cat  << EOF
    {
        "email_state": "approved", 
        "email_type": "event", 
        "event_id": "$EVENT_ID"
    }
EOF
)

function PreviewEmail {
    echo "*** Preview email ***"

    echo $preview_email

    curl -X GET $api_server'/email/preview?data='$preview_email \
    -H "Accept: application/json" > 'data/preview_email.html'

    open 'data/preview_email.html'
}

function CreateEmail {
    echo "*** Create email ***"

    curl -X POST $api_server'/email' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$email"
}

function UpdateEmailToReady {
    echo "*** Update email to ready ***"

    curl -X POST $api_server'/email/'$EMAIL_ID \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$update_email"
}

function UpdateEmailToApproved {
    echo "*** Update email to approved ***"

    curl -X POST $api_server'/email/'$EMAIL_ID \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$update_email_approved"
}

function GetFutureEmails {
    echo "*** Get future emails ***"

    curl -X GET $api_server'/emails/future' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function ImportMarketings {
    echo "*** Import marketings ***"

    curl -X POST $api_server'/marketings/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d @data/marketings.json
}

function GetMarketings {
    echo "*** Get marketings ***"

    curl -X GET $api_server'/marketings' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function ImportMembers {
    echo "*** Import members ***"

    curl -X POST $api_server'/members/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d @data/members.json
}

function TestPaypal {
    echo "*** Test paypal ***"

    curl -X POST $api_server'/paypal/42111e2a-c990-4d38-a785-394277bbc30c' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" 
}


sample_ipn="mc_gross=0.01&protection_eligibility=Ineligible&item_number1=$EVENT_ID&tax=0.00&payer_id=XXYYZZ1&payment_date=10%3A00%3A00+Jan+01%2C+2018+PST&option_name2_1=Date&option_selection1_1=Concession&payment_status=Completed&charset=windows-1252&mc_shipping=0.00&mc_handling=0.00&first_name=Test&mc_fee=0.01&notify_version=3.8&custom=&payer_status=verified&business=receiver%40example.com&num_cart_items=1&mc_handling1=0.00&verify_sign=XXYYZZ1.t.sign&payer_email=$ADMIN_USER&mc_shipping1=0.00&tax1=0.00&btn_id1=XXYYZZ1&option_name1_1=Type&txn_id=112233&payment_type=instant&option_selection2_1=1&last_name=User&item_name1=Get+Inspired+-+Discover+Philosophy&receiver_email=receiver%40example.com&payment_fee=&quantity1=1&receiver_id=AABBCC1&txn_type=Cart&mc_gross_1=0.01&mc_currency=GBP&residence_country=GB&transaction_subject=&payment_gross=&ipn_track_id=112233"


function TestPaypalIPN {
    echo "*** Test paypal IPN ***"

    curl -X POST $api_server'/orders/paypal/ipn' \
    -H "Accept: application/x-www-form-urlencoded" \
    -d "$sample_ipn"
}


function Logout {
    echo "*** Logout ***"

    curl -X DELETE $api_server'/auth/logout' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" | jq .
}

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
            ExtractSpeakers
            ImportEventTypes
            ImportSpeakers
            ImportVenues
            GetFees
            GetEventTypes
            GetSpeakers
            GetVenues
            Logout
            GetFees
        ;;

        -es)
            ExtractSpeakers
        ;;

        -et)
            GetEventTypes
        ;;

        -e)
            GetEvents
        ;;

        -le)
            GetLimitedEvents
        ;;

        -de)
            DeleteEvent
        ;;

        -ep)
            GetEventsPastYear
        ;;

        -fe)
            GetFutureEvents
        ;;

        -s)
            GetSpeakers
        ;;

        -iet)
            ImportEventTypes
        ;;

        -iv)
            ImportVenues
        ;;

        -is)
            ImportSpeakers
        ;;

        -ie)
            ImportEvents
        ;;

        -ce)
            CreateEvent
        ;;

        -ue)
            UpdateEvent
        ;;

        -uer)
            UpdateEventRejected
        ;;

        -iem)
            ImportEmails
        ;;

        -ite)
            ImportTargetEvents
        ;;

        -ia)
            ImportArticles
        ;;

        -ima)
            ImportMarketings
        ;;

        -ime)
            ImportMembers
        ;;

        -ie2m)
            ImportEmailToMembers $3
        ;;

        -ga)
            GetArticles
        ;;

        -gfe)
            GetFutureEmails
        ;;

        -gm)
            GetMarketings
        ;;

        -gas)
            GetArticlesSummary
        ;;

        -gv)
            GetVenues
        ;;

        -cau)
            CreateAdminUser
        ;;

        -gu)
            GetUsers
        ;;

        -gmem)
            GetMembers
        ;;

        -gue)
            GetUserByEmail
        ;;

        -pe)
            PreviewEmail
        ;;

        -cem)
            CreateEmail
        ;;

        -pay)
            TestPaypal
        ;;

        -pipn)
            TestPaypalIPN
        ;;

        -uem)
            UpdateEmailToReady
        ;;

        -uema)
            UpdateEmailToApproved
        ;;

        -setup)
            setupURLS
            setupAccessToken
        ;;

        -x)
            Logout
        ;;

esac
