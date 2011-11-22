#!/bin/bash

N=0

PORT=`expr 20000 + $N`
MEMBER=M`expr 1 + $N`
STATE="states/`expr 1 + $N`/"

mkdir -p "$STATE"

export PYTHONPATH=.
CMD="python2 Tribler/Main/dispersy.py --script gossiplearningframework-observe --script-args hardcoded_member=$MEMBER --port=$PORT --statedir=$STATE"
echo $CMD
$CMD
