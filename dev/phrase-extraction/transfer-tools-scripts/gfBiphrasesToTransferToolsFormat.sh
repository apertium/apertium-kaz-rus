#/bin/bash

SL_FILE=$1
TL_FILE=$2
ALIGNMENTS_FILE=$3

TMP_SL_FILE=`mktemp`
TMP_TL_FILE=`mktemp`
TMP_ALIGNMENTS_FILE=`mktemp`

cat $SL_FILE | sed 's_\$ *\^_$^_g' | sed 's_^ *__' | sed 's_ *$__' | sed 's: :_:g' | sed 's_\$\^_$ ^_g' > $TMP_SL_FILE
cat $TL_FILE | sed 's_\$ *\^_$^_g' | sed 's_^ *__' | sed 's_ *$__' | sed 's: :_:g' | sed 's_\$\^_$ ^_g' > $TMP_TL_FILE
cat $ALIGNMENTS_FILE | sed 's_-_:_g' > $TMP_ALIGNMENTS_FILE

#TODO: deal with multiword entries
paste -d '|' $TMP_SL_FILE $TMP_TL_FILE $TMP_ALIGNMENTS_FILE | sed 's:|: | :g' | sed 's_^_1 | _g' | grep -v -F '$_^'

rm $TMP_ALIGNMENTS_FILE $TMP_SL_FILE $TMP_TL_FILE
