#!/bin/bash

N=$1

rm -rf states/
mkdir -p logs

for i in `seq 1 $N`;
do
    J=`expr $i - 1`
    screen -dmS "M$J" ./script.sh $J
done