#!/bin/bash

. update.conf

import_success=1

rm -f $log $err

update () {
    script="./update-$1.sh"
    if test -z "$2"; then
	proj=$1
    else
	proj=$2
    fi
    echo "===== UPDATING $proj ====" >> $log
    $script $data_root $2 $3 >> $log 2>> $err
    if [ $? != 0 ]; then
	import_success=0
    fi
}

update svn debian-installer svn://svn.d-i.alioth.debian.org/svn/d-i/trunk/packages/po
update gnome
update svn inkscape https://inkscape.svn.sourceforge.net/svnroot/inkscape/inkscape/trunk/po
update svn l10n-kde4 svn://anonsvn.kde.org/home/kde/trunk/l10n-kde4
update mozilla
update oo
update svn suse-i18n https://forgesvn1.novell.com/svn/suse-i18n/trunk
update xfce

