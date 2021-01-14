export ENVIRONMENT=development
export JWT_SECRET=test

## local
export ADMIN_CLIENT_ID=admin
export ADMIN_CLIENT_SECRET=test-secret
export API_BASE_URL=http://localhost:5000

export EMAIL_DISABLED=1
export DISABLE_STATS=1
export EMAIL_RESTRICT=1

export DATABASE_URL_development=postgresql://localhost/na_test

export FRONTEND_URL=http://localhost:8080
export IMAGES_URL="http://localhost:5000/static/images"

# integration test
export ADMIN_CLIENT_ID_development=$ADMIN_CLIENT_ID
export ADMIN_CLIENT_SECRET_development=$ADMIN_CLIENT_SECRET

