#!/bin/sh

for i in `cat $1`; do
    if [ ! -d $i ]; then
	mkdir $i
	cd $i
	for j in contact.html db.html favicon.ico google9242b257cfec1cea.html idea.css images index.html robots.txt template.html whatfor.html; do
	    ln -s ../en/$j .
	done
	sed -s "s/open-tran/$i.open-tran/" < ../en/search.xml > search.xml
    else
	cd $i
	sed -s "s/open-tran/$i.open-tran/" < ../en/search.xml > search.xml
    fi
    cd ..
done
