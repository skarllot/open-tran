#!/bin/sh
#  Copyright (C) 2007, 2008 Jacek Śliwerski (rzyjontko)
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.  

set -e

dbname=$1
ofname=${dbname}-one.db
tfname=${dbname}-two.db

#createdb -E UNICODE "$dbname"
#createlang plpgsql "$dbname"
#psql "$dbname" < db.sql

touch $ofname
rm $ofname
sqlite3 $ofname < step1.sql

touch $tfname
rm $tfname
sqlite3 $tfname < step2.sql

