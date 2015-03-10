#! /bin/bash

CURDIR=`dirname $0`


#shflags
. $CURDIR/shflags

DEFINE_string 'target_language' 'ca' 'target language' 't'
DEFINE_string 'beam_search_dir' '' 'directory where the ats are' 'a'
DEFINE_string 'ats_suffix' '' 'at file suffix' 'x'
DEFINE_string 'dir' '' 'directory where the new files and dirs will be created' 'd'
DEFINE_string 'python_home' '' 'dir of python interpreter' 'p'
DEFINE_string 'beam' '' 'do beam search instead of lin. prog' 'b'
DEFINE_string 'final_boxes_index' '' 'bxoes index' 'f'
DEFINE_string 'tag_groups_seqs_suffix' '' 'Tag groups and sequences suffix' 'g'
DEFINE_string 're_optimize_bleu' 'false' 'optimize bleu score again' 'e'
DEFINE_string 'apertium_data_dir' '' 'dir of python interpreter' 'u'
DEFINE_boolean 'input_is_not_split' 'false' 'Result of beam search is not split in blocks' 's'

FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

echo "ATS suffix: ${FLAGS_ats_suffix}" 1>&2

BEAM_FLAG="--only_n_first 1000"
if [ "${FLAGS_beam}" != "" ]; then
	#BEAM_FLAG="--beam --only_hyps_with_maximum_local --discard_sentences_all_maximum"
	BEAM_FLAG="--select_boxes_minimum --compute_key_segment_breaking_prob"
	if [ "${FLAGS_final_boxes_index}" != "" ]; then
	  BEAM_FLAG="$BEAM_FLAG --final_boxes_index ${FLAGS_final_boxes_index}"
	fi
fi

mkdir -p ${FLAGS_dir}
RESULT_SUFFIX=`echo "${FLAGS_ats_suffix}" | sed 's:.result::'`
RULESID_FILE=${FLAGS_dir}/rulesid$RESULT_SUFFIX
RESULT_FILE=${FLAGS_dir}/result$RESULT_SUFFIX
ALL_ATS_FILE=${FLAGS_beam_search_dir}/ats${FLAGS_ats_suffix}

if [ "${FLAGS_input_is_not_split}" == "${FLAGS_TRUE}" ]; then

SCORES_FILE=${FLAGS_beam_search_dir}/scores${FLAGS_ats_suffix}
ALL_SENTENCES_FILE=${FLAGS_beam_search_dir}/sentences.gz
ALL_SUPERSEGMENTS_FILE=${FLAGS_beam_search_dir}/supersegments${FLAGS_ats_suffix}

else

SCORES_FILE=${FLAGS_dir}/allscores$RESULT_SUFFIX
ALL_SENTENCES_FILE=${FLAGS_dir}/allsentences.gz
ALL_SUPERSEGMENTS_FILE=${FLAGS_dir}/allsupersegments$RESULT_SUFFIX

rm -f $SCORES_FILE ${SCORES_FILE%.gz}
rm -f ${ALL_SENTENCES_FILE} ${ALL_SENTENCES_FILE%.gz}
rm -f ${ALL_SUPERSEGMENTS_FILE} ${ALL_SUPERSEGMENTS_FILE%.gz}
NUMBERS=`ls  ${FLAGS_beam_search_dir} | grep "^scores-" | awk -F"-" '{print $2}' | LC_ALL=C sort | uniq`
TOTALNUMBERS=`echo "$NUMBERS" | wc -l`
for number in $NUMBERS; do
	zcat "${FLAGS_beam_search_dir}/scores-${number}-${TOTALNUMBERS}${FLAGS_ats_suffix}" >> ${SCORES_FILE%.gz}
	echo "${number}:" >> ${SCORES_FILE}-debug
	cat "${FLAGS_beam_search_dir}/scores-${number}-${TOTALNUMBERS}${FLAGS_ats_suffix}-debug" | grep "ERROR" >> ${SCORES_FILE}-debug
	
	zcat "${FLAGS_beam_search_dir}/supersegments-${number}-${TOTALNUMBERS}${FLAGS_ats_suffix}" >> ${ALL_SUPERSEGMENTS_FILE%.gz}
	echo "${number}:" >> ${ALL_SUPERSEGMENTS_FILE}-debug
	cat "${FLAGS_beam_search_dir}/supersegments-${number}-${TOTALNUMBERS}${FLAGS_ats_suffix}.debug" | grep "ERROR" >> ${ALL_SUPERSEGMENTS_FILE}-debug
	
	zcat "${FLAGS_beam_search_dir}/sentences.${number}-${TOTALNUMBERS}.gz" >> ${ALL_SENTENCES_FILE%.gz}
done
gzip ${SCORES_FILE%.gz}
gzip ${ALL_SENTENCES_FILE%.gz}
gzip ${ALL_SUPERSEGMENTS_FILE%.gz}

fi

#change to source code dir to allow python to find script
pushd $CURDIR

NUMSENTENCES=`zcat $ALL_SENTENCES_FILE | wc -l`
NUMSCORES=`zcat $SCORES_FILE | wc -l` 
NUMSUPERSEGMENTS=`zcat $ALL_SUPERSEGMENTS_FILE | wc -l`

if [ "$NUMSENTENCES" == "$NUMSCORES" -a "$NUMSENTENCES" == "$NUMSUPERSEGMENTS" ]; then 

zcat ${SCORES_FILE} | ${FLAGS_python_home}python $CURDIR/maximiseScore.py $BEAM_FLAG --target_language ${FLAGS_target_language} --tag_groups_file_name $CURDIR/taggroups${FLAGS_tag_groups_seqs_suffix} --tag_sequences_file_name $CURDIR/tagsequences${FLAGS_tag_groups_seqs_suffix} --alignment_templates $ALL_ATS_FILE --sentences ${ALL_SENTENCES_FILE}  --supersegments_with_maximum_score  $ALL_SUPERSEGMENTS_FILE --apertium_data_dir "${FLAGS_apertium_data_dir}"   2> ${RESULT_FILE}-debug | gzip > $RULESID_FILE
#SED_EXPR=`zcat $RULESID_FILE | sed 's:$:p:' | tr '\n' ';' | sed 's:;$::'`

#zcat $ALL_ATS_FILE | sed -n "$SED_EXPR" | gzip > $RESULT_FILE

else

echo "ERROR: Different length of sentences, scores and supersegments" >> ${RESULT_FILE}-debug

echo "" | gzip > $RULESID_FILE

fi

popd
