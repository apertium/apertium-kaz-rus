#! /bin/bash

CURDIR=`dirname $0`

apertium-preprocess-transfer $CURDIR/test.rules.xml $CURDIR/test.rules.bin
lt-comp lr $CURDIR/apertium-es-ca.es-ca.dix $CURDIR/apertium-es-ca.es-ca.bin

echo '^el<det><def><f><sg>$ ^casa<n><f><sg>$ ^azul<adj><mf><sg>$ ^.<sent>$' | apertium-transfer $CURDIR/test.rules.xml $CURDIR/test.rules.bin $CURDIR/apertium-es-ca.es-ca.bin > $CURDIR/output
echo '^3<num>$[ <format> ]^rápidamente<adv>$[ </format> ]^.<sent>$' | apertium-transfer $CURDIR/test.rules.xml $CURDIR/test.rules.bin $CURDIR/apertium-es-ca.es-ca.bin > $CURDIR/output2

DIFF=`diff $CURDIR/output $CURDIR/reference`
DIFF2=`diff $CURDIR/output2 $CURDIR/reference2`

if [ "$DIFF" == "" -a "$DIFF2" == "" ]; then
  echo "Apertium is correctly patched"
else
  echo "Apertium is not correctly patched. Diffs: "
  echo "$DIFF"
  echo "$DIFF2"
fi


