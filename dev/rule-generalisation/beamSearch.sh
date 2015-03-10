#! /bin/bash

CURDIR=`dirname $0`

#two modes of getting the ATs:
# ats_file: compressed file containing all the ats
# ats_dir: dir where the ats are found

#generates:

# $dir/scores${FLAGS_result_infix}${FLAGS_ats_suffix}
#
# infix is usually "-$PART" and suffix is usually "-f-$THRESHOLD.result.gz"
#

#shflags
. $CURDIR/shflags

DEFINE_string 'target_language' 'ca' 'target language' 't'
DEFINE_string 'ats_file' '' 'file containing the alignment templates' 'f'
DEFINE_string 'ats_filtering_dir' '' 'directory where the ats are' 'a'
DEFINE_string 'alternative_ats_filtering_dir' '' 'directory where the ats are' 'm'
DEFINE_string 'ats_suffix' '' 'at file suffix' 'x'
DEFINE_string 'dir' '' 'directory where the new files and dirs will be created' 'd'
DEFINE_string 'sentences' '' 'file contining the sentences to be evaluated' 's'
DEFINE_string 'tag_groups_seqs_suffix' '' 'file containing the sentences to be evaluated' 'g'
DEFINE_string 'result_infix' '' 'string added in the middle of the result filename' 'i'
DEFINE_string 'python_home' '' 'dir of python interpreter' 'p'
DEFINE_string 'apertium_data_dir' '' 'dir of python interpreter' 'u'
DEFINE_string 'final_boxes_index' 'NONE' 'Boxes index' 'n'
DEFINE_boolean 'debug' 'false' 'Debug information' 'b'

FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

echo "ATS suffix: ${FLAGS_ats_suffix}" 1>&2

DEBUG_FLAG=""

if [ "${FLAGS_debug}" == "${FLAGS_TRUE}" ]; then
 DEBUG_FLAG="--debug"
fi

#get ATs
if [ "${FLAGS_ats_file}" != "" ]; then
	ATS_FILE=${FLAGS_ats_file}
else
	ATS_FILE=${FLAGS_dir}/ats${FLAGS_ats_suffix}
	rm -f ${ATS_FILE%.gz}
	NUMBERS=`ls  ${FLAGS_ats_filtering_dir} | awk -F"-" '{print $1}' | awk -F"." '{print $1}'  | LC_ALL=C sort | uniq`
	for number in $NUMBERS; do
		zcat "${FLAGS_ats_filtering_dir}${number}${FLAGS_ats_suffix}" >> ${ATS_FILE%.gz}
	done
	gzip ${ATS_FILE%.gz}
	
	if [ "${FLAGS_alternative_ats_filtering_dir}" != "" ]; then
		ALTATSSUFFIX="-alt1"
		ALT_ATS_FILE="${FLAGS_dir}/ats$ALTATSSUFFIX${FLAGS_ats_suffix}"
		ALT_ATS_FLAG="--alternative_alignment_templates $ALT_ATS_FILE"
		rm -f ${ALT_ATS_FILE%.gz}
		NUMBERS=`ls  ${FLAGS_alternative_ats_filtering_dir} | awk -F"-" '{print $1}' | awk -F"." '{print $1}'  | LC_ALL=C sort | uniq`
		for number in $NUMBERS; do
			zcat "${FLAGS_alternative_ats_filtering_dir}${number}${FLAGS_ats_suffix}" >> ${ALT_ATS_FILE%.gz}
		done
		gzip ${ALT_ATS_FILE%.gz}
	fi
fi

BOXESFLAG=""
BOXESFLAGSEC=""
if [ "${FLAGS_final_boxes_index}" != "NONE" ] ; then
  BOXESFLAG="--final_boxes_index ${FLAGS_final_boxes_index} --minimum_covered_words --allow_incompatible_rules"
  BOXESFLAGSEC="--final_boxes_index ${FLAGS_final_boxes_index}"
fi



#change to source code dir to allow python to find script
pushd $CURDIR

zcat ${FLAGS_sentences} | ${FLAGS_python_home}python $CURDIR/beamSearch.py --target_language ${FLAGS_target_language} --alignment_templates $ATS_FILE $ALT_ATS_FLAG --tag_groups_file_name $CURDIR/taggroups${FLAGS_tag_groups_seqs_suffix} --tag_sequences_file_name $CURDIR/tagsequences${FLAGS_tag_groups_seqs_suffix} --apertium_data_dir "${FLAGS_apertium_data_dir}" $BOXESFLAG $DEBUG_FLAG --beam_size 2000 2> ${FLAGS_dir}/scores${FLAGS_result_infix}${FLAGS_ats_suffix}-debug | awk -F"[|][|][|]"  '{ print $1; }' | gzip > ${FLAGS_dir}/scores${FLAGS_result_infix}${FLAGS_ats_suffix}

if [ "$ALT_ATS_FILE" == "" ]; then
	zcat ${FLAGS_dir}/scores${FLAGS_result_infix}${FLAGS_ats_suffix} | ${FLAGS_python_home}python $CURDIR/computeSupersetsOfKeySegments.py --tag_groups_file_name $CURDIR/taggroups${FLAGS_tag_groups_seqs_suffix} --tag_sequences_file_name $CURDIR/tagsequences${FLAGS_tag_groups_seqs_suffix} $BOXESFLAGSEC --alignment_templates $ATS_FILE --sentences ${FLAGS_sentences} --target_language ${FLAGS_target_language} --apertium_data_dir "${FLAGS_apertium_data_dir}" 2>${FLAGS_dir}/supersegments${FLAGS_result_infix}${FLAGS_ats_suffix}.debug | gzip  > ${FLAGS_dir}/supersegments${FLAGS_result_infix}${FLAGS_ats_suffix}
fi

popd
