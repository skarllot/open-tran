#!/bin/sh

set -e

dbname=$1

#createdb -E UNICODE "$dbname"
#createlang plpgsql "$dbname"
#psql "$dbname" < db.sql

touch $dbname
rm $dbname
sqlite3 $dbname < db_sqlite.sql
