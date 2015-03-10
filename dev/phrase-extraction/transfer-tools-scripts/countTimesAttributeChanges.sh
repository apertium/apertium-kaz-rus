#! /bin/bash

BILDIC=$1
RULELEARNINGDIR=$2
INVERSE=$3
PAIR=$4

if [ "$INVERSE" == "" ]; then
	lt-expand $BILDIC | grep -v -F ":<:" | sed 's/:>:/:/' | tr ":" "\t" | python $RULELEARNINGDIR/countTimesAttributeChanges.py --tag_groups_file_name $RULELEARNINGDIR/taggroups_$PAIR --tag_sequences_file_name $RULELEARNINGDIR/tagsequences_$PAIR
else
	lt-expand $BILDIC | grep -v -F ":>:" | sed 's/:<:/:/' | tr ":" "\t" | python $RULELEARNINGDIR/countTimesAttributeChanges.py --tag_groups_file_name $RULELEARNINGDIR/taggroups_$PAIR --tag_sequences_file_name $RULELEARNINGDIR/tagsequences_$PAIR
fi

