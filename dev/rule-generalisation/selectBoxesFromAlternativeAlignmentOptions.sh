#! /bin/bash

CURDIR=`dirname $0`


#shflags
. $CURDIR/shflags

DEFINE_string 'beam_search_dir' '' 'directory where the ats are' 'a'
DEFINE_string 'ats_suffix' '' 'at file suffix' 'x'
DEFINE_string 'dir' '' 'directory where the new files and dirs will be created' 'd'
DEFINE_string 'python_home' '' 'dir of python interpreter' 'p'
DEFINE_string 'tag_groups_seqs_suffix' '' 'Tag groups and sequences suffix' 'g'

FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

echo "ATS suffix: ${FLAGS_ats_suffix}" 1>&2


mkdir -p ${FLAGS_dir}
RESULT_SUFFIX=`echo "${FLAGS_ats_suffix}" | sed 's:.result::'`
RULESID_FILE=${FLAGS_dir}/rulesid$RESULT_SUFFIX
RESULT_FILE=${FLAGS_dir}/result$RESULT_SUFFIX
SCORES_FILE=${FLAGS_dir}/allscores$RESULT_SUFFIX

rm -f $SCORES_FILE ${SCORES_FILE%.gz}

NUMBERS=`ls  ${FLAGS_beam_search_dir} | grep "^scores-" | awk -F"-" '{print $2}' | LC_ALL=C sort | uniq`
TOTALNUMBERS=`echo "$NUMBERS" | wc -l`
for number in $NUMBERS; do
	zcat "${FLAGS_beam_search_dir}/scores-${number}-${TOTALNUMBERS}${FLAGS_ats_suffix}" >> ${SCORES_FILE%.gz}
	echo "${number}:" >> ${SCORES_FILE}-debug
	cat "${FLAGS_beam_search_dir}/scores-${number}-${TOTALNUMBERS}${FLAGS_ats_suffix}-debug" | grep "ERROR" >> ${SCORES_FILE}-debug
done
gzip ${SCORES_FILE%.gz}

zcat ${SCORES_FILE%.gz} | ${FLAGS_python_home}python $CURDIR/selectFromAlternativeAtSets.py  --tag_groups_file_name $CURDIR/taggroups${FLAGS_tag_groups_seqs_suffix} --tag_sequences_file_name $CURDIR/tagsequences${FLAGS_tag_groups_seqs_suffix} --debug  2> ${RESULT_FILE}-debug | gzip > $RULESID_FILE

