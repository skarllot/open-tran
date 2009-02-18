#!/bin/bash

data_root="$1"
xfce_root="$data_root/xfce"

if [ ! -d $xfce_root ]; then
    mkdir $xfce_root
fi

cd $xfce_root

xmodules=`svn ls http://svn.xfce.org/svn/xfce/`
for m in $xmodules; do
    if test -d $m; then
	cd $m

	echo -n "cleanup $m..."
	svn cleanup > /dev/null || true
	echo "done."

	echo -n "up $m..."
	svn up > /dev/null || true
	echo "done."

	cd ..
    else
	echo -n "co $m..."
	svn co http://svn.xfce.org/svn/xfce/${m}trunk/po $m > /dev/null || true
	echo "done."
    fi
done

goodies=`wget -o /dev/null -O- http://svn.xfce.org/index.cgi/xfce-goodies | grep 'href="/index.cgi/xfce-goodies/browse' | sed 's/.*\/browse\/\([^"]*\)".*/\1/'`
for m in $goodies; do
    if test -d $m; then
	cd $m
	echo -n "up $m..."
	svn up > /dev/null || true
	echo "done."
	cd ..
    else
	echo -n "co $m..."
	svn co http://svn.xfce.org/svn/goodies/${m}/trunk/po $m > /dev/null || true
	echo "done."
    fi
done

