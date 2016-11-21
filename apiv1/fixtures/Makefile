ADMIN_USER=admin
ADMIN_PASS=password
API_URL=http://fpan.herokuapp.com/api/v1

API_SUBSCRIPTIONS_URL="${API_URL}/subscriptions/"

CURL=curl --user ${ADMIN_USER}:${ADMIN_PASS} -H "Content-Type: application/json"
new_subscription:
	 ${CURL} -X POST -d @subscribe_new_user.json ${API_SUBSCRIPTIONS_URL}
