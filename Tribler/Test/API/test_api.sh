#!/bin/sh -x
#
# WARNING: this shell script must use \n as end-of-line, Windows
# \r\n gives problems running this on Linux

PYTHONPATH=../../..:"$PYTHONPATH"
export PYTHONPATH

#python test_tdef.py
python test_seeding.py

