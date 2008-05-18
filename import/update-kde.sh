#!/bin/bash

kde_root="/home/sliwers/projekty/open-tran-data/l10n-kde4"

cd $kde_root
for lang in `cat subdirs`; do
    echo -n "up $lang..."
    svn up $lang > /tmp/svn.out 2> /tmp/svn.err
    echo "done."
done
