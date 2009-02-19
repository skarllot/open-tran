#!/bin/bash

. update.conf

export LC_ALL=C
export PYTHONPATH=$toolkit_path:$data_root/../lib
export PATH=$PATH:$data_root/../import

log="$log_dir/import.log"
err="$log_dir/import.err"
audit="$log_dir/audit.txt"
status="$log_dir/status.txt"


echo "importing" > $status
rm -f $log $err $audit

date > $log

update () {
    script="./update-$1.sh"
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

update svn debian-installer svn://svn.d-i.alioth.debian.org/svn/d-i/trunk/packages/po
update gnome
update svn inkscape https://inkscape.svn.sourceforge.net/svnroot/inkscape/inkscape/trunk/po
update kde
update mozilla
update oo
update svn suse-i18n https://forgesvn1.novell.com/svn/suse-i18n/trunk
update xfce

echo "processing" > $status

import_step1.py $data_root >> $log 2>> $err
audit_step1.py $data_root > $audit 2>> $err
import_step2.py $data_root >> $log 2>> $err
import_step3.py $data_root >> $log 2>> $err

rm $status

