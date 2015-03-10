# ! /bin/bash

#BILDIC=$1
#OUTPUTCORPUS=$2
#INVERSE=$3
#
#if [ "$INVERSE" == "" ]; then
#	lt-expand $BILDIC | grep -v -F ":<:" | sed 's/:>:/:/' | cut -f 1 -d ':' | sed 's:^:^:'  | sed 's:$:$:' | apertium-pretransfer | apertium-preprocess-corpus-transfer-at  > $OUTPUTCORPUS.sl
#	lt-expand $BILDIC | grep -v -F ":<:" | sed 's/:>:/:/' | cut -f 2 -d ':' | sed 's:^:^:'  | sed 's:$:$:' | apertium-pretransfer | apertium-preprocess-corpus-transfer-at  > $OUTPUTCORPUS.tl
#else
#	lt-expand $BILDIC | grep -v -F ":>:" | sed 's/:<:/:/' | cut -f 1 -d ':' | sed 's:^:^:'  | sed 's:$:$:' | apertium-pretransfer | apertium-preprocess-corpus-transfer-at  > $OUTPUTCORPUS.tl
#	lt-expand $BILDIC | grep -v -F ":>:" | sed 's/:<:/:/' | cut -f 2 -d ':' | sed 's:^:^:'  | sed 's:$:$:' | apertium-pretransfer | apertium-preprocess-corpus-transfer-at  > $OUTPUTCORPUS.sl
#fi

BINBILDIC=$1
SLMONODIX=$2
OUTPUTCORPUS=$3

TMPS=`mktemp`
TMPT=`mktemp`
TMPJ=`mktemp`

lt-expand $SLMONODIX | grep -v -F ":<:" | sed 's/:>:/:/' | cut -f 2 -d ':' | sed 's:^:^:' | sed 's:$:$:' | apertium-pretransfer | sed 's:\$ \^:$\n^:g'  | LC_ALL=C sort | LC_ALL=C uniq > $TMPS

cat $TMPS |  sed 's:^^::' | sed 's:$$::' | apertium-apply-biling --biling $BINBILDIC --withqueue | cut -f 1 -d '/' | sed 's:^:^:' | sed 's:$:$:' > $TMPT

paste $TMPS $TMPT | grep -v -F "	^@" > $TMPJ

cut -f 1 $TMPJ | apertium-preprocess-corpus-transfer-at > $OUTPUTCORPUS.sl
cut -f 2 $TMPJ | apertium-preprocess-corpus-transfer-at > $OUTPUTCORPUS.tl

rm $TMPF $TMPT $TMPJ