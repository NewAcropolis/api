#!/bin/bash
set +e

function setupURLS {
    if [ $ENVIRONMENT = "development" ]; then
        export api_server="${API_BASE_URL}"
        export username=$ADMIN_CLIENT_ID_development
        export password=$ADMIN_CLIENT_SECRET_development
    elif [ $ENVIRONMENT = "preview" ]; then
        export api_server="${API_BASE_URL}"
        export username=$ADMIN_CLIENT_ID_preview
        export password=$ADMIN_CLIENT_SECRET_preview
    elif [ $ENVIRONMENT = "live" ]; then
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

function ImportTestSpeakers {
    echo "*** Import speakers ***"

    curl -X POST $api_server'/speakers/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$speakers"
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
        },
        {
            "id": "4",
            "name": "Online Event",
            "address": "Online",
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

function ImportTestVenues {
    echo "*** Import venues ***"

    curl -X POST $api_server'/venues/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$venues"
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

test_event=$(cat  << EOF
    [
        {
            "id": "1",
            "BookingCode": "xxx",
            "Approved": "y",
            "Type": "1",
            "Title": "Test event",
            "SubTitle": "Test subtitle",
            "Description": "Test preview",
            "venue": "1",
            "Speaker": "Sabine Leitner",
            "MultiDayFee": "0",
            "MultiDayConcFee": "0",
            "StartDate": "2021-05-20 19:30:00",
            "StartDate2": "0000-00-00 00:00:00",
            "StartDate3": "0000-00-00 00:00:00",
            "StartDate4": "0000-00-00 00:00:00",
            "EndDate": "0000-00-00 00:00:00",
            "Duration": "0",
            "Fee": "4",
            "ConcFee": "2",
            "ImageFilename": "events_image.png"
        }
    ]
EOF
)

function ImportTestEvents {
    echo "*** Import Test Events ***"

    curl -X POST $api_server'/events/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$test_event"
}

function setupTestEventID {
    TEST_EVENT_ID=$(curl $api_server'/events' \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TKN" | jq -r '.[0].id')

    echo "Setup TEST_EVENT_ID" $TEST_EVENT_ID
}

function UpdateTestEventApproved {
    echo "*** Update Test Event approved ***"

    TEST_EVENT_ID=$(curl $api_server'/events' \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TKN" | jq -r '.[0].id')

    curl -X POST $api_server'/event/'$TEST_EVENT_ID \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "{\"event_state\": \"approved\"}"
}

test_marketing=$(cat  << EOF
[{
    "id": "0",
    "marketingtxt": "Friend",
    "ordernum": "0",
    "visible": "1"
}]
EOF
)

function ImportTestMarketing {
    echo "*** Import test marketing ***"

    curl -X POST $api_server'/marketings/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$test_marketing"
}

test_member=$(cat  << EOF
[
    {
        "id": "1",
        "Name": "Test Member",
        "EmailAdd": "$TEST_SUBSCRIBER",
        "Active": "y",
        "CreationDate": "0000-00-00",
        "Marketing": "0",
        "IsMember": "n",
        "LastUpdated": "2021-01-01 20:00:00"
    }
]
EOF
)

function ImportTestMember {
    echo "*** Import test member ***"

    curl -X POST $api_server'/members/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$test_member"
}

test_event_update=$(cat  << EOF
    {
        "title": "Test title",
        "description": "Test description",
        "image_filename": "events_image_2.png"
    }
EOF
)

function UpdateTestEvent {
    echo "*** Update Test Event ***"

    curl -X POST $api_server'/event/'$TEST_EVENT_ID \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$test_event_update"
}

function PreviewTestEmail {
    echo "*** Preview test email ***"

    preview_test_email="%7B%22details%22%3A%20%22%3Cdiv%3ESome%20additional%20details%3C/div%3E%22%2C%20%22email_type%22%3A%20%22event%22%2C%20%22event_id%22%3A%20%22$TEST_EVENT_ID%22%2C%20%22extra_txt%22%3A%20%22%3Cdiv%3ESome%20more%20information%20about%20the%20event%3C/div%3E%22%2C%20%22replace_all%22%3A%20false%7D"

    curl -X GET $api_server'/email/preview?data='$preview_test_email \
    -H "Accept: application/json" > 'data/preview_test_email.html'

    open 'data/preview_test_email.html'
}

function CreateTestEmail {
    echo "*** Create test email ***"

test_email=$(cat  << EOF
    {
        "event_id": "$TEST_EVENT_ID",
        "details": "<div>Some additional details</div>",
        "extra_txt": "<div>Some more information about the event</div>",
        "replace_all": false,
        "email_type": "event"
    }
EOF
)

    curl -X POST $api_server'/email' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$test_email"
}

function SendTestEmail {
    echo "*** Send test email ***"

    TEST_EMAIL=$(curl $api_server'/emails/latest' \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TKN")

    TEST_EMAIL_ID=$(echo "$TEST_EMAIL" | jq -r '.[0].id')

    echo 'Sending '$TEST_EMAIL_ID

    curl $api_server'/email/send/'$TEST_EMAIL_ID \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function UpdateTestEmailToApproved {
    echo "*** Update test email to approved ***"

    TEST_EMAIL=$(curl $api_server'/emails/latest' \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TKN")

    TEST_EMAIL_ID=$(echo "$TEST_EMAIL" | jq -r '.[0].id')
    TEST_EVENT_ID=$(echo "$TEST_EMAIL" | jq -r '.[0].event_id')

    echo "Setup TEST_EMAIL_ID" $TEST_EMAIL_ID $TEST_EVENT_ID
update_test_email=$(cat  << EOF
    {
        "email_state": "approved", 
        "email_type": "event", 
        "event_id": "$TEST_EVENT_ID"
    }
EOF
)

    curl -X POST $api_server'/email/'$TEST_EMAIL_ID \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$update_test_email"
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
        "event_type_id":"596985c3-939e-47d0-8a31-a813d57e4076",
        "title": "Test title",
        "description": "Test description",
        "venue_id": "c9f4257e-e5c3-4fa8-9913-bfb9406da76a",
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

    curl -X POST $api_server"/event/$EVENT_ID" \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$event_update"
}

function UpdateEventRejected {
    echo "*** Update Event Rejected ***"

    curl -X POST $api_server"/event/$EVENT_ID" \
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

# CommunicateFeelings.jpg
# 22

article_1=$(cat  << EOF
{
    "image_filename": "CommunicateFeelings.jpg"
}
EOF
)

# Eclecticism.jpg
# 24
article_2=$(cat  << EOF
{
    "image_filename": "Eclecticism.jpg"
}
EOF
)

# Victor Schauberger.jpg
# 19

article_3=$(cat  << EOF
{
    "image_filename": "Victor_Schauberger.jpg"
}
EOF
)

# AlchemistsGold.jpg
# 8

article_4=$(cat  << EOF
{
    "image_filename": "AlchemistsGold.jpg"
}
EOF
)

# Modern Myth.jpg
# 2

article_5=$(cat  << EOF
{
    "image_filename": "Modern_Myth.jpg"
}
EOF
)

# Play Chess.jpg
# 18

article_6=$(cat  << EOF
{
    "image_filename": "Play_Chess.jpg"
}
EOF
)

# Unending Progress.jpg
# 26

article_7=$(cat  << EOF
{
    "image_filename": "Unending_Progress.jpg"
}
EOF
)


function UpdateArticleByOldId {
    echo "*** Update Article by Old ID ***"
    curl -X POST $api_server'/article/22' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$article_1"

    curl -X POST $api_server'/article/24' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$article_2"

    curl -X POST $api_server'/article/19' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$article_3"

    curl -X POST $api_server'/article/8' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$article_4"

    curl -X POST $api_server'/article/2' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$article_5"

    curl -X POST $api_server'/article/18' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$article_6"

    curl -X POST $api_server'/article/26' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$article_7"
}


function ImportBooks {
    echo "*** Import books ***"

    curl -X POST $api_server'/books/import' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d @data/books.json
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

magazine=$(cat  << EOF
{
    "title": "Test pdf",
    "filename": "test_Issue_0.pdf",
    "pdf_data": "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"
}
EOF
)

function CreateMagazine {
    echo "*** Create Magazine ***"

    curl -X POST $api_server'/magazine' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$magazine"
}

function GetUsers {
    echo "*** Get users ***"

    curl -X GET $api_server'/users' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" 
}

new_user=$(cat  << EOF
{
    "email": "$NEW_USER_EMAIL",
    "name": "$NEW_USER_NAME",
    "active": true,
    "access_area": "$NEW_USER_ACCESS"
}
EOF
)

function CreateUser {
    echo "*** Create user ***"

    curl -X POST $api_server'/user' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$new_user"
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
preview_basic_email="data={\"email_type\":\"basic\",\"name\":\"Test name\",\"message\":\"<a href='http://localhost:5000'>Test message 1</a>\"}"

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

    curl -X GET $api_server'/email/preview?data='$preview_email \
    -H "Accept: application/json" > 'data/preview_email.html'

    open 'data/preview_email.html'
}

function PreviewBasicEmail {
    echo "*** Preview basic email ***"

    curl --GET \
    --data-urlencode "$preview_basic_email" \
    $api_server'/email/preview' \
    -H "Accept: application/json" > 'data/preview_email.html'

    open 'data/preview_email.html'
}

function PreviewMagazineEmail {
    echo "*** Preview magazine email ***"

    curl --GET \
    --data-urlencode "data={\"title\": \"Issue 1\", \"email_type\": \"magazine\", \"magazine_id\": \"$MAGAZINE_ID\"}" \
    $api_server'/email/preview' \
    -H "Accept: application/json" > 'data/preview_email.html'

    open 'data/preview_email.html'
}

function SendEmailTest {
    echo "*** Send email test ***"

    curl -X GET \
    $api_server'/email/test' \
    -H "Authorization: Bearer $TKN" \
    -H "Accept: application/json"
}

function CreateEmail {
    echo "*** Create email ***"

    curl -X POST $api_server'/email' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$email"
}

email_provider=$(cat  << EOF
    {
        "name": "$EMAIL_PROVIDER_NAME",
        "daily_limit": $EMAIL_PROVIDER_DAILY_LIMIT,
        "hourly_limit": $EMAIL_PROVIDER_HOURLY_LIMIT,
        "api_key": "$EMAIL_PROVIDER_API_KEY",
        "api_url": "$EMAIL_PROVIDER_API_URL",
        "data_map": "$EMAIL_PROVIDER_DATA_MAP",
        "pos": $EMAIL_PROVIDER_POS,
        "headers": $EMAIL_PROVIDER_HEADERS,
        "as_json": $EMAIL_PROVIDER_AS_JSON,
        "smtp_server": "$EMAIL_PROVIDER_SMTP_SERVER",
        "smtp_user": "$EMAIL_PROVIDER_SMTP_USER",
        "smtp_password": "$EMAIL_PROVIDER_SMTP_PASSWORD"
    }
EOF
)

update_email_provider=$(cat  << EOF
    {
        "pos": $EMAIL_PROVIDER_POS
    }
EOF
)

function CreateEmailProvider {
    echo "*** Create email provider ***"

    curl -X POST $api_server'/email_provider' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$email_provider"
}

function UpdateEmailProvider {
    echo "*** Update email provider ***"

    curl -X POST $api_server"/email_provider/$EMAIL_PROVIDER_ID" \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" \
    -d "$update_email_provider"
}

function GetEmailProviders {
    echo "*** Get email providers ***"

    curl -X GET $api_server"/email_providers" \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
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

function GetApprovedEmails {
    echo "*** Get approved emails ***"

    curl -X GET $api_server'/emails/approved' \
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

function SendSocialStats {
    echo "*** Send social stats ***"

    curl -X GET $api_server'/stats/social' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function SendSubscribersSocialStats {
    echo "*** Send subscribers and social stats ***"

    curl -X GET $api_server'/stats/subscribers_and_social' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function SendEmailStats {
    echo "*** Send email stats ***"

    curl -X GET $api_server'/stats/emails/08/2020' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function SendSubscribersSocialStats {
    echo "*** Send subscribers and social stats ***"

    curl -X GET $api_server'/stats/subscribers_and_social' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN"
}

function SendEmailStats {
    echo "*** Send email stats ***"

    curl -X GET $api_server'/stats/emails/11/2020' \
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

sample_ipn="mc_gross=0.01&protection_eligibility=Ineligible&item_number1=$EVENT_ID&item_number2=delivery&tax=0.00&payer_id=XXYYZZ1&address_street=Flat+1%2C+1+Example+Street&payment_date=10%3A00%3A00+Jan+01%2C+2018+PST&option_name2_1=Date&option_selection1_1=Concession&payment_status=Completed&charset=windows-1252&address_zip=n1+5ds&mc_shipping=0.00&mc_handling=0.00&first_name=Test&mc_fee=0.01&address_country_code=GB&notify_version=3.8&custom=&payer_status=verified&business=seller%40newacropolisuk.org&address_country=United+Kingdom&num_cart_items=2&mc_handling1=0.00&address_city=London&verify_sign=XXYYZZ1.t.sign&payer_email=$ADMIN_USER&mc_shipping1=0.00&tax1=0.00&btn_id1=XXYYZZ1&option_name1_1=Type&txn_id=112233&payment_type=instant&option_selection2_1=1&last_name=User&item_name1=Get+Inspired+-+Discover+Philosophy&receiver_email=seller%40newacropolisuk.org&item_name2=UK&payment_fee=&quantity1=1&receiver_id=AABBCC1&txn_type=Cart&mc_gross_1=0.01&mc_currency=GBP&residence_country=GB&transaction_subject=&payment_gross=&ipn_track_id=112233"


function TestPaypalIPN {
    echo "*** Test paypal IPN ***"

    curl -X POST $api_server'/orders/paypal/ipn' \
    -H "Accept: application/x-www-form-urlencoded" \
    -d "$sample_ipn"
}

sample_ipn_delivery="_notify-validate&mc_gross=10.00&protection_eligibility=Eligible&address_status=confirmed&item_number1=$BOOK_ID&item_number2=$DELIVERY_ID&payer_id=XXYYZZ&address_street=Flat+1%2C+1+Test+Place&payment_date=14%3A45%3A55+Jan+10%2C+2021+PDT&option_name2_1=Course+Member+name&option_name2_2=Course+Member+name&option_selection1_1=Full&payment_status=Completed&option_selection1_2=Full&charset=windows-1252&address_zip=n1+1aa&mc_shipping=0.00&first_name=TestName&mc_fee=0.54&address_country_code=GB&address_name=Test+Name&notify_version=3.9&custom=&payer_status=unverified&business=test%40test.com&address_country=United+Kingdom&num_cart_items=2&mc_handling1=0.00&mc_handling2=0.00&address_city=London&verify_sign=AUl-w13NMy4f84hsUb1AfdPySBVSAn5cuQjLRnnAnlH2cpx64MuK5l34&payer_email=$ADMIN_USER&btn_id1=123456789&btn_id2=012345678&option_name1_1=Type&option_name1_2=Type&txn_id=1122334455&payment_type=instant&option_selection2_1=-&last_name=Test&address_state=&option_selection2_2=-&item_name1=Philosophy+Test&receiver_email=test%40example.com&item_name2=Test+Book&payment_fee=&shipping_discount=0.00&quantity1=1&insurance_amount=0.00&quantity2=1&receiver_id=11223344&txn_type=cart&discount=0.00&mc_gross_1=5.00&mc_currency=GBP&mc_gross_2=5.00&residence_country=GB&receipt_id=0000-1111-2222-3333&shipping_method=Default&transaction_subject=&payment_gross=&ipn_track_id=1122334455aa"

function GetOrder {
    echo "*** Get order with transaction ID ***"

    curl $api_server'/order/'$TXN_ID \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" 
}

function GetOrders {
    echo "*** Get orders ***"

    curl $api_server'/orders' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" 
}

function GetBooks {
    echo "*** Get books ***"

    curl $api_server'/books' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" 
}

function Logout {
    echo "*** Logout ***"

    curl -X DELETE $api_server'/auth/logout' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer $TKN" | jq .
}

setupURLS
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

        -imin) echo "Import minimal for email test"
            ImportEventTypes
            ImportTestVenues
            ImportTestSpeakers
            ImportTestEvents
            UpdateTestEventApproved
            ImportTestMarketing
            ImportTestMember
            setupTestEventID
            CreateEmailProvider
            CreateTestEmail
            UpdateTestEmailToApproved
        ;;

        -pvtest) echo "Preview test"
            setupTestEventID
            PreviewTestEmail
        ;;

        -uptest) echo "Update test event"
            setupTestEventID
            UpdateTestEvent
        ;;

        -sendtest) echo "Send test event email"
            
            SendTestEmail
        ;;

        -iall) echo "Import all"
            ImportVenues
            ImportEventTypes
            ImportSpeakers
            ImportEvents
            ImportArticles
            ImportMarketings
            ImportMembers
            ImportEmails
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

        -ib)
            ImportBooks
        ;;

        -ima)
            ImportMarketings
        ;;

        -ime)
            ImportMembers
        ;;

        -ie2m)
            ImportEmailToMembers $2
        ;;

        -ga)
            GetArticles
        ;;

        -gfe)
            GetFutureEmails
        ;;

        -gae)
            GetApprovedEmails
        ;;

        -gm)
            GetMarketings
        ;;

        -ss)
            SendSocialStats
        ;;

        -sss)
            SendSubscribersSocialStats
        ;;

        -ses)
            SendEmailStats
        ;;

        -gas)
            GetArticlesSummary
        ;;

        -uao)
            UpdateArticleByOldId
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

        -pbe)
            PreviewBasicEmail
        ;;

        -pme)
            PreviewMagazineEmail
        ;;

        -cem)
            CreateEmail
        ;;

        -sem)
            SendEmailTest
        ;;

        -cm)
            CreateMagazine
        ;;

        -cu)
            CreateUser
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

        -go)
            GetOrder
        ;;

        -gos)
            GetOrders
        ;;

        -gbs)
            GetBooks
        ;;

        -uema)
            UpdateEmailToApproved
        ;;

        -cep)
            CreateEmailProvider
        ;;

        -uep)
            UpdateEmailProvider
        ;;

        -gep)
            GetEmailProviders
        ;;

        -setup)
            setupURLS
            setupAccessToken
        ;;

        -x)
            Logout
        ;;

esac
