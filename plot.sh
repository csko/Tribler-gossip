#!/bin/bash

export FNAME=$1
export OUTNAME=$2

gnuplot << gptend
set term png large nocrop enhanced 14 size 1280,1024
set output "$OUTNAME"

set style line 1 lt 1 lw 1 pt 3 lc rgb "red"
set style line 2 lt 1 lw 1 pt 3 lc rgb "blue"
set style line 3 lt 3 lw 1 pt 3 lc rgb "green"
set style line 4 lt 3 lw 1 pt 3 lc rgb "orange"

set logscale x
set xrange [*:*]
set yrange [*:*]

set title "$FNAME"

set ylabel "Average of 0-1 error over the whole network"
set xlabel "Seconds"

plot "$FNAME" using 1:3 with lines t 'max', \
     "$FNAME" using 1:4 with lines t 'avg', \
     "$FNAME" using 1:2 with lines t 'min'
gptend
