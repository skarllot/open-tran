#!/bin/bash

data_root="/home/sliwers/projekty/open-tran-data"
gnome_root="$data_root/gnome-po"

gmodules=`wget -o /dev/null -O- http://svn.gnome.org/viewvc/ | grep 'a href="/viewvc/[^"]' | sed 's/.*\/viewvc\/\([^\/]*\)\/.*/\1/'`

for m in $gmodules; do
    cd $gnome_root
    if test -d $m; then
	cd $m
	echo -n "up $m..."
	svn up > /dev/null 2> /dev/null
	echo "done."
	cd ..
    else
	echo -n "co $m..."
	svn co http://svn.gnome.org/svn/$m/trunk/po $m > /dev/null 2> /dev/null
	echo "done."
    fi
done

touch "$data_root/gnome.stamp"
