#!/bin/bash

SERVERDIR=`dirname $0`
export PYTHONPATH=$SERVERDIR/../lib

if [[ -f $SERVERDIR/server.pid ]]; then
    RUNNING=`cat $SERVERDIR/server.pid`
    if kill -0 $RUNNING 2> /dev/null; then
	exit 0
    fi
fi

nohup authbind python $SERVERDIR/server.py > /tmp/ot.out 2> /tmp/ot.err &
