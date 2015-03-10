#! /bin/bash

INPUTFILE=$1
BILDICTIONARY=$2
OUTPUTFILE=$3

BILDICFROMLEXSELECTION=$4

WDIR=`dirname $1`

if [ "$OUTPUTFILE" == "" ]; then
	OUTPUTFILE=$INPUTFILE.toBeam.gz
fi

zcat $INPUTFILE | sed 's:\^\$:^*unknown$:g' | sed 's:^[^|]*| ::'  | sed 's:\^:| ^:'   |  sed 's:| *\^:| ':g | sed 's:\$ *|: |:g' | sed 's:\$ *\^: :g' | sed 's:^| ::' | gzip > $OUTPUTFILE.step1.gz

if [ "$BILDICFROMLEXSELECTION" != "" ]; then
	cat $BILDICFROMLEXSELECTION > $OUTPUTFILE.bildic.gz
else

#the last sed removes multiple entries
zcat $OUTPUTFILE.step1.gz | cut -f 1 -d '|'  | sed  's:^ *::' | sed  's_ *$__' | sed -r 's_ _\t_g' | sed -r 's:_: :g'  | apertium-apply-biling --biling $BILDICTIONARY --withqueue | sed 's:/[^\t]*::g' | gzip > $OUTPUTFILE.bildic.gz

fi

zcat $OUTPUTFILE.bildic.gz  | sed 's:<[^\t]*::g' | sed 's: :_:g' | sed 's:\t: :g' > $OUTPUTFILE.tllemmas

zcat $OUTPUTFILE.bildic.gz  | sed 's:^[^<\t]*:LEMMAPLACEHOLDER:' | sed 's:\t[^<\t]*:\tLEMMAPLACEHOLDER:g' | sed 's:LEMMAPLACEHOLDER<:<:g' | sed 's:LEMMAPLACEHOLDER:__EMPTYRESTRICTION__:g' | sed 's:\t: :g' > $OUTPUTFILE.restrictions

zcat $OUTPUTFILE.step1.gz | paste -d '|' - $OUTPUTFILE.restrictions $OUTPUTFILE.tllemmas | gzip > $OUTPUTFILE