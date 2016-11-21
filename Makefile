export MANDRILL_USER=dummy_username
export MANDRILL_PASSWORD=dummy_password
export DATABASE_URL:= sqlite:///foo.sqlite3
export DJANGO_SETTINGS_MODULE:=fpan.settings

all: test lettuce

test:
	python manage.py test plans apiv1

lettuce-ff:
	# python manage.py harvest --port 6462 -v2
	python manage.py harvest -T --no-server --failfast -a plans

lettuce:
	python manage.py harvest -T --no-server -v1 -a plans
	# python manage.py harvest -T --no-server

lettuce-me:
	python manage.py harvest -T --no-server -tme -a plans
