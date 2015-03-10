#! /bin/bash

CURDIR=`dirname $0`


#shflags
. $CURDIR/shflags

DEFINE_string 'selection_result' '' 'result of selecting the AT boxes from the alternative alignment options' 'f'
DEFINE_string 'ats_suffix' '' 'at file suffix' 'x'
DEFINE_string 'primary_input_dir' '' 'primary filtering dir' 'o'
DEFINE_string 'secondary_input_dir' '' 'secondary filterinf dir' 't'
DEFINE_string 'dir' '' 'directory where the new files and dirs will be created' 'd'
DEFINE_string 'final_boxes_index' '' 'boxes index file' 'i'

FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

echo "ATS suffix: ${FLAGS_ats_suffix}" 1>&2

DIR=${FLAGS_dir}
mkdir -p $DIR
ATSUFFIX=${FLAGS_ats_suffix}
DEBUGSUFFIX=`echo "${FLAGS_ats_suffix}" | sed 's:.result:.result.debug:'`
RULESID_FILE=${FLAGS_selection_result}
BOXESINDEX=${FLAGS_final_boxes_index}

SOURCE_DIRS[0]=${FLAGS_primary_input_dir}
SOURCE_DIRS[1]=${FLAGS_secondary_input_dir}

cat $BOXESINDEX | cut -f 1 | egrep -v "^[[:space:]]*$" | sort > $DIR/allboxes.sorted

#copy boxes according to selection result
mkdir -p $DIR/ats
mkdir -p $DIR/debug

zcat $RULESID_FILE | while read PAIR ; do
	BOXID=`echo "$PAIR" | cut -f 1`
	ALTAT=`echo "$PAIR" | cut -f 2`
	SRC_DIR=${SOURCE_DIRS[$ALTAT]}
	
	cp $SRC_DIR/ats/$BOXID$ATSUFFIX $DIR/ats/
	cp $SRC_DIR/debug/$BOXID$DEBUGSUFFIX $DIR/debug/
	
	echo "$BOXID" >> $DIR/copiedboxesfromresult
done

cat $DIR/copiedboxesfromresult | sort > $DIR/copiedboxesfromresult.sorted

#copy boxes we don't have information about from first AT alternative set
comm -13 $DIR/copiedboxesfromresult.sorted $DIR/allboxes.sorted > $DIR/boxesnotinkeysegments

for BOXID in `cat $DIR/boxesnotinkeysegments` ; do
	SRC_DIR=${SOURCE_DIRS[0]}
	if [ -f $SRC_DIR/ats/$BOXID$ATSUFFIX ] ; then
		cp $SRC_DIR/ats/$BOXID$ATSUFFIX $DIR/ats/
		cp $SRC_DIR/debug/$BOXID$DEBUGSUFFIX $DIR/debug/
	fi
done

