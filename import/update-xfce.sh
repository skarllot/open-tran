#!/bin/bash

data_root="/media/disk/sliwers/projekty/open-tran-data"
xfce_root="$data_root/xfce"

cd $xfce_root

xmodules=`svn ls http://svn.xfce.org/svn/xfce/`
for m in $xmodules; do
    if test -d $m; then
	cd $m
	echo -n "up $m..."
	svn up > /tmp/xfce.svn.out 2> /tmp/xfce.svn.err
	echo "done."
	cd ..
    else
	echo -n "co $m..."
	svn co http://svn.xfce.org/svn/xfce/${m}trunk/po $m > /tmp/xfce.svn.out 2> /tmp/xfce.svn.err
	echo "done."
    fi
done

goodies=`wget -o /dev/null -O- http://svn.xfce.org/index.cgi/xfce-goodies | grep 'href="/index.cgi/xfce-goodies/browse' | sed 's/.*\/browse\/\([^"]*\)".*/\1/'`
for m in $goodies; do
    if test -d $m; then
	cd $m
	echo -n "up $m..."
	svn up > /tmp/xfce.svn.out 2> /tmp/xfce.svn.err
	echo "done."
	cd ..
    else
	echo -n "co $m..."
	svn co http://svn.xfce.org/svn/goodies/${m}/trunk/po $m > /tmp/xfce.svn.out 2> /tmp/xfce.svn.err
	echo "done."
    fi
done

touch "$data_root/xfce.stamp"
