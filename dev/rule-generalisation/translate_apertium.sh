#! /bin/bash

APERTIUM_PATH=$1
MODE=$2

JOIN_LINES_OPTION=$3

FORMAT=$4
DATA_DIR=$5

UNKNOWN_FLAG="-u"

if [ "$6" == "--show_unknown" ]; then
  UNKNOWN_FLAG=""
fi


if [ "$FORMAT" == "" ]; then
        FORMAT="txt"
	FORMAT_STR=""
else
	FORMAT_STR="-f $FORMAT"
fi

if [ "$DATA_DIR" == "" ]; then
	DATA_STR=""
else
	DATA_STR="-d $DATA_DIR"
fi

SLASH_APERTIUM="/"
if [ "" == "$APERTIUM_PATH" ]; then
	SLASH_APERTIUM=""
fi


if [ "join" == "$JOIN_LINES_OPTION" ]; then

	sed -r 's_$_ 。._' | $APERTIUM_PATH${SLASH_APERTIUM}apertium $UNKNOWN_FLAG $DATA_STR $FORMAT_STR $MODE | sed -e '${/^$/d}' | sed -r 's_[ ]?\.\.$__' | sed -r 's_[ ]?。\.$__' #first sed does its job for zho-spa, since the starnge unicode dot is trasnlated into a standard dot, second sed does the job for the rest of languages
	#$APERTIUM_PATH${SLASH_APERTIUM}apertium -u $DATA_STR $FORMAT_STR $MODE | sed -e '${/^$/d}' 
	#$APERTIUM_PATH${SLASH_APERTIUM}apertium-des$FORMAT | sed -r 's_\[$_ THISISANUNKNOWNWORDWITHNOSENSE8906503465[_' | $APERTIUM_PATH${SLASH_APERTIUM}apertium $UNKNOWN_FLAG $DATA_STR -f none $MODE | apertium-re$FORMAT | sed -e '${/^$/d}' | sed -r 's_[ ]?THISISANUNKNOWNWORDWITHNOSENSE8906503465$__' 

else

while read line
do

output=`echo "$line" | $APERTIUM_PATH${SLASH_APERTIUM}apertium $UNKNOWN_FLAG $DATA_STR $FORMAT_STR $MODE`
echo "$output"

done

fi
