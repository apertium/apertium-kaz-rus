#! /bin/bash

ORIGINAL_MODE=$1
TRANSFER_TOOLS_PATH=$2
POSTRANSFER_FILE=$3


SLASHTRANSFERTOOLS="/"
if [ "" == "$TRANSFER_TOOLS_PATH"  ]; then 
	SLASHTRANSFERTOOLS=""
fi

TOPRETRANSFER=`cat $ORIGINAL_MODE | awk -F"apertium-pretransfer" '{ print $1 }' | tr -d '\n' | sed 's_ *$__'`
FROMPRETRANSFER=`cat $ORIGINAL_MODE | awk -F"apertium-pretransfer" '{ print $2 }' | tr -d '\n'`

FROMTRANSFER=`cat $ORIGINAL_MODE | awk  '{print substr($0,index($0,"apertium-transfer")) }' | sed 's:^apertium-transfer::' | tr -d '\n'`

FROMSECONDLTPROC=`echo $FROMTRANSFER |  grep -o 'lt-proc.*$'  | tr -d '\n'` #awk -F"lt-proc" '{ print $2 }' | tr -d '\n'
APERTIUM_PATH=`echo $TOPRETRANSFER | awk -F"lt-proc" '{ print $1 }' | tr -d '\n'`

echo "sed 's_\^\([^#$]*\)#\([^<$]*\)\(<[^\$]*\)\\\$_^\\1\\3#\\2\$_g'  | ${TRANSFER_TOOLS_PATH}${SLASHTRANSFERTOOLS}apertium-posttransfer -x  ${POSTRANSFER_FILE} | ${APERTIUM_PATH}${FROMSECONDLTPROC}"

