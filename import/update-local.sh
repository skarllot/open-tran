#!/bin/bash

set -e

local_dir=/home/sliwers/open-tran
log_dir=/var/log

export PYTHONPATH=$local_dir/lib

logout="$log_dir/import.log"
errout="$log_dir/import.err"

echo -n "########## Starting import: " >> $logout
date >> $logout

if file "$local_dir/data" | grep "dataa"; then
    olddir="$local_dir/dataa"
    newdir="$local_dir/datab"
else
    olddir="$local_dir/datab"
    newdir="$local_dir/dataa"
fi

echo -n "########## Downloading the database: " >> $logout
date >> $logout

wget -o /dev/null -O $newdir/ten.db http://ot.leonardof.org/data/ten.db
rm -f $newdir/ten-*.db

echo -n "########## Copying Mozilla and OO.o phrases: " >> $logout
date >> $logout

(cat <<EOF
attach database '$local_dir/dataa/mo.db' as 'mo';

insert into projects
select * from mo.projects;

insert into phrases
select * from mo.phrases;
EOF
) | sqlite3 $newdir/ten.db

echo -n "########## Moving phrases: " >> $logout
date >> $logout
$local_dir/import/import_step2.py $newdir >> $logout 2>> $errout

echo -n "########## Moving words: " >> $logout
date >> $logout
$local_dir/import/import_step3.py $newdir >> $logout 2>> $errout

echo -n "########## Finished " >> $logout
date >> $logout
