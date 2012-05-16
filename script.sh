#!/bin/bash

N=$1
NUMPEERS=$2
PORT=`expr 20000 + $N`
MEMBER=M`expr 1 + $N`
STATE="states/`expr 1 + $N`/"

mkdir -p experiment/logs/
mkdir -p "$STATE"
mkdir -p logs

export PYTHONPATH=.
export ARGS="hardcoded_member=$MEMBER,database=spambase,num_peers=$NUMPEERS"
CMD="python2 Tribler/Main/dispersy.py --script gossiplearningframework-observe --script-args $ARGS --port=$PORT --statedir=$STATE"
echo $CMD
$CMD >logs/$N.log 2>logs/$N-error.log
