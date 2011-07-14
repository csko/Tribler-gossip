#!/bin/bash
#
# This script helps running Tribler .py files from the source tree. It is not meant to be used by the masses.
# If you have not already done so, build the Mac-specific libraries by executing
#    cd mac && make
# This will also create a 'lib' symlink to 'mac/build/lib' when finished. Alternatively, you can
# let it point to built libraries in a different source tree.
#
# Next to this, you need wxPython 2.8-unicode and Python 2.5 installed.

PYTHONVER=2.5
PYTHON=/usr/local/bin/python$PYTHONVER

DIRCHANGE=`dirname $0`

if [ $DIRCHANGE != "" ]
then
  cd $DIRCHANGE
fi

if [ ! -e "macbinaries" ]
then
  echo Please unpack macbinaries-`arch`.tar.gz here, so that the macbinaries directory will be created and filled with the binaries required for operation.
  exit -1
fi

export PYTHONPATH=`pwd`/macbinaries:`pwd`/lib/Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/
export DYLD_LIBRARY_PATH=`pwd`/macbinaries

# use a hardlink so the script is in the current directory, otherwise
# python will start to chdir all over the place
rm -f tmp.py
ln $1 tmp.py
shift
$PYTHON tmp.py $@

