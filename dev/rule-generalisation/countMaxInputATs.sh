#! /bin/bash

GENERALISATION_DIR=$1
THRESHOLD=$2


MAX=0

pushd $GENERALISATION_DIR > /dev/null

for FILE in *.ats.gz ; do

	VALIDLINESF=`mktemp`
	zcat $FILE | python -c '
import sys
threshold=int(sys.argv[1])
for line in sys.stdin:
	line=line.strip()
	freq=int(line.split(" ")[0])
	if freq >= threshold:
		print line
' $THRESHOLD > $VALIDLINESF
	
	#zcat $FILE | while read LINE ; do
	#	FREQ=`echo $LINE | cut -f 1 -d ' '`
	#	if [ $FREQ -ge $THRESHOLD ]; then
	#		echo "$LINE"
	#	fi
	#done > $VALIDLINESF
	
	NUMVALID=`cat $VALIDLINESF | wc -l`
	
	rm "$VALIDLINESF"
	
	
	if [ $NUMVALID -gt $MAX ]; then
		MAX=$NUMVALID
	fi
done

popd > /dev/null

echo "$MAX"