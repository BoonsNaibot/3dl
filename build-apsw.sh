#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -f $CACHEROOT/sqlite-amalgamation-3080301.zip ] ; then
	try curl -L http://sqlite.org/2014/sqlite-amalgamation-3080301.zip > $CACHEROOT/sqlite-amalgamation-3080301.zip
fi
if [ ! -d $TMPROOT/apsw ]; then
        try pushd $TMPROOT
        try git clone -b master https://github.com/rogerbinns/apsw
        try cd apsw
        try unzip $CACHEROOT/sqlite-amalgamation-3080301.zip
        try mv sqlite-amalgamation-3080301/* $TMPROOT/apsw
        try rm -rf sqlite-amalgamation-3080301
        try popd
fi

pushd $TMPROOT/apsw
OLD_CFLAGS="$CFLAGS"
OLD_LDSHARED="$LDSHARED"
export LDSHARED="$KIVYIOSROOT/tools/liblink"
export CFLAGS="$CFLAGS -DEXPERIMENTAL -DAPSW_USE_SQLITE_AMALGAMATION=\'sqlite3.c\'"

$HOSTPYTHON setup.py build_ext -v
$HOSTPYTHON setup.py install -O2

export LDSHARED="$OLD_LDSHARED"
export CFLAGS="$OLD_CFLAGS"
popd

bd=$TMPROOT/apsw/build/lib.macosx-*/
try $KIVYIOSROOT/tools/biglink $BUILDROOT/lib/libapsw.a $bd
deduplicate $BUILDROOT/lib/libapsw.a

echo '== APSW build is done'
