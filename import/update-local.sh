#!/bin/bash

. /home/sliwers/open-tran/import/update.conf

export PYTHONPATH=$local_dir/lib

errfile="/tmp/import.err"
restfile="/tmp/import.rest"
logout="$log_dir/import.log"
errout="$log_dir/import.err"

echo -n "Starting import: " >> $logout
date >> $logout

if file "$local_dir/data" | grep "dataa"; then
    olddir="$local_dir/dataa"
    newdir="$local_dir/datab"
else
    olddir="$local_dir/datab"
    newdir="$local_dir/dataa"
fi

rm -rf $restfile $errfile

wget -o /dev/null -O $errfile http://ot.leonardof.org/log/import.err

if [ ! -f $errfile ]; then
    echo "wget failed" >> $logout
    exit 1
fi

cnt=`grep "^svn:" $errfile | wc -l`

if [ "$cnt" != 275 ]; then
    echo "strange number of errors: $cnt" >> $logout
    exit 1
fi

cat $errfile | grep -v "^svn:" | grep -v "No module named lxml" > $restfile

cnt=`cat $restfile | wc -l`

if [ "$cnt" == 0 ]; then
    wget -o /dev/null -O "$newdir/ten.db" http://ot.leonardof.org/data/ten.db
else
    echo "There were $cnt unexpected errors in the file." >> $errout
fi

if [ -f "$newdir/ten-zu.db" ]; then
    if [ `stat -c "%Z" $newdir/ten-zu.db` -le `stat -c "%Z" $newdir/ten.db` ]; then
	echo "nothing new here" >> $logout
	exit 0
    fi
fi

rm -f $newdir/ten-*.db

if [ ! -f "$newdir/ten.db" ]; then
    echo "no primary file in $newdir" >> $logout
    exit 1
fi

$local_dir/import/import_step2.py $newdir >> $logout 2>> $errout
$local_dir/import/import_step3.py $newdir >> $logout 2>> $errout
