#!/bin/bash

PORT=20000
MEMBER=M1

export PYTHONPATH=.
CMD="python2 Tribler/Main/dispersy.py --script gossiplearningframework-observe --script-args hardcoded_member=$MEMBER --port=$PORT"
echo $CMD
$CMD
