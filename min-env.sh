export ENVIRONMENT=development
export JWT_SECRET=test

## local
export ADMIN_CLIENT_ID=test-admin
export ADMIN_CLIENT_SECRET=test-secret
export API_BASE_URL=http://localhost:5000

export EMAIL_DISABLED=
export DISABLE_STATS=1
export EMAIL_RESTRICT=1
export EMAIL_TOKENS='{"member_id":"member_id"}'
export EMAIL_UNSUB_SALT=test

export DATABASE_URL_development=postgresql://localhost/na_test

export FRONTEND_URL=http://localhost:8080
export IMAGES_URL="http://localhost:5000/static/images"

export EMAIL_PROVIDER_NAME="TestProvider"
export EMAIL_PROVIDER_POS=0
export EMAIL_PROVIDER_API_URL=""
export EMAIL_PROVIDER_API_KEY=""
export EMAIL_PROVIDER_DAILY_LIMIT=0
export EMAIL_PROVIDER_HOURLY_LIMIT=50
export EMAIL_PROVIDER_DATA_MAP=""
export EMAIL_PROVIDER_HEADERS=false
export EMAIL_PROVIDER_AS_JSON=false

export EMAIL_PROVIDER_SMTP_SERVER=
export EMAIL_PROVIDER_SMTP_USER=
export EMAIL_PROVIDER_SMTP_PASSWORD=

export TEST_SUBSCRIBER=
export TEST_EMAIL=

# integration test
export ADMIN_CLIENT_ID_development=$ADMIN_CLIENT_ID
export ADMIN_CLIENT_SECRET_development=$ADMIN_CLIENT_SECRET

