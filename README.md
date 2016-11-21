F5
====
As a SAS (Software As a Service), it is able to handle financial management for your project. 

Batch-creation of promo codes
=============================

To batch-create promo codes, first log in to [fpan admin](http://PROJECT.ir/fpan/admin/),
then go to `Promo types` and create one (e.g. `expo-mordad`).

Don't forget to create `Promo type - plan detail`s.
Each `Promo type plan detail` object specifies the final price
of a `plan`, when a code of a specific `type` is entered by the user.

So you'd normally want to create "3" `promo type plan detail` object. Or perhaps if you don't wanted to provide discount for a specific plan, you wouldn't create `promo type plan detail` for that plan.

Then run this command from your local machine

    ssh user@origin.FQDN "cd /app/f5; source .virtualenv/bin/activate; foreman run python batch-create-promo-code.py 1000 expo-mordad 'brand'" | tr '\n' '\n\r' > /tmp/codes.txt

where

*   `1000` is the number of codes to be generated,
*   `expo-mordad` is the type of the promo code
*   `brand` is the name of the partner

Don't forget to put the company name in quotes.

Dependencies
------------

These were installed in previous steps:

    foreman
    python and python-dev
    postgresql related packages
    git-deploy on local machine

Deploy
------

*   Add a remote to your local git clone

        git remote add origin user@host.FQDN:/app/f5

*   Initiate remote git remote and deploy hooks on the remote server

        git deploy setup -r origin

*   Push to remote (same tips about `production` branch apply here)

        git checkout production
        git merge master

    and then

        git push origin production:master
        git checkout master


    > *Note:*
    > The initial push to production would
    > *   export `Procfile` to upstart services
    > *   setup `virtualenv` and
    > *   start the app.

    > If the app was not listening on port 8005
    > run `deploy/setup` manually on the remote server to debug.

Project Plans
------
  PROJECT plans are stored in `initiate_PROJECT_data.py`

# Development

To run `F5` in development mode you have to set `DEVELOPMENT` environment variable:

    export DEVELOPMENT=1

A typical tmuxinator window would be like

    - fpan:
        pre:
          - sudo mkdir -p /var/log/f5 && sudo chown $USER /var/log/f5 && cd f5
          - source .virtualenv/bin/activate
        layout: main-horizontal
        panes:
          - foreman run deploy/setup
          - foreman run python manage.py runserver
          - foreman run python manage.py celery worker

'deploy/setup' will make up application environment as it need and 'F5' will be served on localhost:8005.
