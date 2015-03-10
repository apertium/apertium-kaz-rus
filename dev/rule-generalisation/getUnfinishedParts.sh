#! /bin/bash

ORIGINAL_DIR=$1
FILTERING_METHOD=$2

SEPARATED_BY_THRESHOLD=$3

pushd $ORIGINAL_DIR > /dev/null

NUMGENF=`ls generalisation-*.tar.gz | wc -l` 
NUMPARTS=$((NUMGENF - 1))

for i in `seq $NUMPARTS`; do
	PARTUNFINISHED=false
	if [ "$SEPARATED_BY_THRESHOLD" == "" ]; then
		if [ ! -f "filtering-$FILTERING_METHOD-$i-$NUMPARTS.tar.gz" ]; then
			PARTUNFINISHED=true
		fi
	else
		if [ `ls filtering-$FILTERING_METHOD-$i-$NUMPARTS-f-*.tar.gz | wc -l` != 21 ] ; then
			PARTUNFINISHED=true
		fi
	fi
	
	if [ $PARTUNFINISHED == true ]; then
		if [ -f partswillfinish ]; then
			GREPEXPR="^$i$"
			if [ "`cat partswillfinish | grep "$GREPEXPR" | wc -l`" == "0" ]; then
				echo "$i"
			fi
		else
			echo "$i"
		fi
	fi
done

popd > /dev/null