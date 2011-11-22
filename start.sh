#!/bin/bash

N=0

export PYTHONPATH=.
export TSTATEDIR="/home/csko/TriblerConfigs/$N/"

TORRENTPORT=`expr 7760 + $N`
I2IPORT=`expr 57891 + $N`
VIDEOPORT=`expr 6875 + $N`

mkdir -p $TSTATEDIR

echo "Running: python Tribler/Main/tribler.py $TSTATEDIR $TORRENTPORT $I2IPORT $VIDEOPORT"

python2 Tribler/Main/tribler.py $TSTATEDIR $TORRENTPORT $I2IPORT $VIDEOPORT
