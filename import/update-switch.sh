#!/bin/sh

set -e

if [[ -z "$IMPORTDIR" ]]; then
    echo "IMPORTDIR is not defined.  It should point to the import directory."
    exit 1
fi

export PYTHONPATH="$IMPORTDIR/../lib"

if file "$IMPORTDIR/../data" | grep "dataa"; then
    olddir="dataa"
    newdir="datab"
else
    olddir="datab"
    newdir="dataa"
fi

$IMPORTDIR/audit_step1.py $IMPORTDIR/../$newdir > /tmp/projects.html
$IMPORTDIR/audit_step2.py $IMPORTDIR/../$newdir > /tmp/languages.html

cd "$IMPORTDIR/.."
rm data
ln -s "$newdir" "$IMPORTDIR/../data"
mv /tmp/projects.html server
mv /tmp/languages.html server
