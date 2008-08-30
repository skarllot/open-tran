#!/bin/bash

TRASH_OFF=YES

data_root="/media/disk/sliwers/projekty/open-tran-data"
mozilla_root="$data_root/mozilla"
mozilla_l10n="$data_root/mozilla-l10n"
mozilla_po="$data_root/mozilla-po"

cd $mozilla_root
echo -n "up mozilla..."
cvs up > /dev/null 2> /dev/null
echo "done."

cd $mozilla_l10n
echo -n "up l10n..."
cvs up > /dev/null 2> /dev/null
echo "done."

rm -r $mozilla_l10n/en-US
rm -r $mozilla_po/*

echo -n "en-US..."
cd $mozilla_root
make -f tools/l10n/l10n.mk create-en-US > /dev/null
echo "done."

cd $mozilla_l10n
for d in *; do
    if [ "$d" == "CVS" ] || [ "$d" == "en-US" ]; then
	continue
    fi
    cd $data_root
    echo -n "$d..."
    moz2po -t "$mozilla_l10n/en-US" "$mozilla_l10n/$d" "$mozilla_po/$d"
    echo "done."
done

touch "$data_root/mozilla.stamp"
