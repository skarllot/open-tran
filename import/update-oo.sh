#!/bin/bash

TRASH_OFF=YES

data_root="/media/disk/sliwers/projekty/open-tran-data"
oo_l10n="$data_root/oo-l10n"
oo_po="$data_root/oo-po"

if [ -z "$1" ] || [ "$1" != "skip" ]; then
    cd $oo_l10n
    echo -n "up l10n..."
    cvs up > /dev/null 2> /dev/null
    echo "done."
fi

# cd $oo_po
# echo -n "clean..."
# rm -r *
# echo "done"

# echo -n "get en-US..."
# wget ftp://ftp.linux.cz/pub/localization/OpenOffice.org/latest/GSI/en-US.sdf
# echo "done."

cd $oo_l10n

for d in *; do
    if [ ! -f "$d/localize.sdf" ]; then
	continue
    fi

    echo -n "merging $d..."
    cat "$oo_po/en-US.sdf" > "$oo_po/full.sdf"
    sed '/^#/d' < "$d/localize.sdf" >> "$oo_po/full.sdf"
    echo "done."

    echo -n "converting %d..."
    oo2po --duplicates=merge -l $d "$oo_po/full.sdf" "$oo_po/$d"
    echo "done."
done

touch "$data_root/oo.stamp"
