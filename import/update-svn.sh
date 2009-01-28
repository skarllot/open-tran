#!/bin/bash

set -e

data_root="$1"
proj_name="$2"
url="$3"
svn_root="$data_root/$proj_name"

if test -d $svn_root; then
    cd $svn_root
    echo -n "up $proj_name..."
    svn up > /dev/null 
    echo "done."
else
    echo -n "co $proj_name..."
    cd $data_root
    svn co $url $svn_root > /dev/null
    echo "done."
fi
