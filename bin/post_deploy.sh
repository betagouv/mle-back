#!/bin/env bash

python manage.py migrate --settings=config.settings.production
python manage.py sync_perms --settings=config.settings.production
