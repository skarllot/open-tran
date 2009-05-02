#!/bin/sh

set -e

if [[ -z "$IMPORTDIR" ]]; then
    echo "IMPORTDIR is not defined.  It should point to the import directory."
    exit 1
fi

export PYTHONPATH="$IMPORTDIR/../lib"

$IMPORTDIR/audit_step1.py $IMPORTDIR > /tmp/projects.html
$IMPORTDIR/audit_step2.py $IMPORTDIR > /tmp/languages.html

if file "$IMPORTDIR/../data" | grep "dataa"; then
    olddir="$IMPORTDIR/../dataa"
    newdir="$IMPORTDIR/../datab"
else
    olddir="$IMPORTDIR/../datab"
    newdir="$IMPORTDIR/../dataa"
fi

rm "$IMPORTDIR/../data"
ln -s "$newdir" "$IMPORTDIR/../data"
mv /tmp/projects.html $IMPORTDIR/../server
mv /tmp/languages.html $IMPORTDIR/../server
