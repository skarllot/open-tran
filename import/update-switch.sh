#!/bin/sh

set -e

if [[ -z "$IMPORTDIR" ]]; then
    echo "IMPORTDIR is not defined.  It should point to the import directory."
    exit 1
fi

export PYTHONPATH="$IMPORTDIR/../lib"

if file "$IMPORTDIR/../data" | grep "dataa"; then
    olddir="$IMPORTDIR/../dataa"
    newdir="$IMPORTDIR/../datab"
else
    olddir="$IMPORTDIR/../datab"
    newdir="$IMPORTDIR/../dataa"
fi

$IMPORTDIR/audit_step1.py $newdir > /tmp/projects.html
$IMPORTDIR/audit_step2.py $newdir > /tmp/languages.html

rm "$IMPORTDIR/../data"
ln -s "$newdir" "$IMPORTDIR/../data"
mv /tmp/projects.html $IMPORTDIR/../server
mv /tmp/languages.html $IMPORTDIR/../server
