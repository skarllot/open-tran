#!/bin/bash

. update.conf

export PYTHONPATH=$toolkit_path:$data_root/../lib

log="$log_dir/import.log"
err="$log_dir/import.err"
audit="$log_dir/audit.txt"
status="$log_dir/status.txt"

update () {
    script="update-$1.sh"
    if test -z "$2"; then
	proj=$1
    else
	proj=$2
    fi
    echo $proj >> $status
    echo
    echo "===== UPDATING $proj ====" >> $log
    $script $data_root $2 $3 >> $log 2>> $err
}


rm -f $log $err $audit
date > $log
echo "importing" > $status

dayofweek=`date +%u`
if [[ $dayofweek < 3 ]]; then
    update svn debian-installer svn://svn.d-i.alioth.debian.org/svn/d-i/trunk/packages/po
    update gnome
    update xfce
    update fedora
else
    update svn inkscape https://inkscape.svn.sourceforge.net/svnroot/inkscape/inkscape/trunk/po
    update kde
    update mandriva
    update svn suse-i18n https://forgesvn1.novell.com/svn/suse-i18n/trunk
fi

rm -rf $data_root/../data/ten-$dayofweek.db*

echo "processing" >> $status

date >> $log

import_step1.py $data_root $dayofweek >> $log 2>> $err

date >> $log

rm $status
