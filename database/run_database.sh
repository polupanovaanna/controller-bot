#!/usr/bin/env bash
service postgresql start
/bin/bash
psql --username=unicorn_user --dbname=rainbow_database