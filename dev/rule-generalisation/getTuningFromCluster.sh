#!/bin/bash

CURDIR=`dirname $0`

#shflags
. $CURDIR/shflags
DEFINE_string 'sizes' '1000' 'space-separated list of sizes of bilingual corpus' 'v'
DEFINE_string 'filtering_method' 'proportion_correct_bilphrases_thresholdrelaxabove2' 'Filtering method' 'f'
DEFINE_string 'source_language' 'es' 'Source language' 's'
DEFINE_string 'target_language' 'ca' 'Target language' 't'
DEFINE_string 'bilingual_phrases_id' 'markersoft-withcontradictions-smallalignmentmodel' 'Identifier of the starting bilingual phrases' 'b'
DEFINE_string 'dir' '/work/vmsanchez/rules/transfer-cluster/' 'Prefix of the directory in which results will be stored' 'd'
DEFINE_boolean 'use_beam_dir' 'false' 'directory for tuning after beam search' 'm'
FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

DIR=${FLAGS_dir}
FILTMETHOD=${FLAGS_filtering_method}
SL=${FLAGS_source_language}
TL=${FLAGS_target_language}
BILID=${FLAGS_bilingual_phrases_id}

BEAMDIR=""
if [ "${FLAGS_use_beam_dir}" == "${FLAGS_TRUE}" ]; then
  BEAMDIR="/beamresult"
fi

for SIZE in ${FLAGS_sizes} ; do
	echo "Processing size $SIZE"

	WORKDIRNOBEAM=$DIR/${SL}-${TL}/$BILID/$SIZE
	WORKDIR=$DIR/${SL}-${TL}/$BILID/$SIZE$BEAMDIR
	mkdir -p $WORKDIR
	pushd $WORKDIR
	scp euler.iuii.ua.es:/home/vmsanchez/results/experiments-linear-l5-${SL}-${TL}/$BILID/shuf$SIZE$BEAMDIR/tuning-$FILTMETHOD-*.tar.gz ./
	for file in `ls tuning-$FILTMETHOD-[!-]*.tar.gz`; do  
		tar xzf $file;
		dir=${file%.tar.gz}
		pushd $dir/queries/test-f-*/experiment
		cat ./modes/${SL}-${TL}_learned.mode | sed 's:/scratch/vmsanchez/[0-9]*/sources/Python-2.6.7/bin/::g'  | sed 's:/scratch/vmsanchez/[0-9]*/local/:/home/vmsanchez/rulesinteractive/local/:g' | sed 's:/scratch/vmsanchez/[0-9]*/sources:/home/vmsanchez/hybridmt/tools:g'  | sed "s:/scratch/vmsanchez/[0-9]*/experiments-linear-l5-${SL}-${TL}-v2/shuf$SIZE/:/work/vmsanchez/rules/transfer-cluster/${SL}-${TL}/$BILID/$SIZE$BEAMDIR:g" > ./modes/${SL}-${TL}_learned-fixed.mode
		PATH=/home/vmsanchez/rulesinteractive/local/bin:$PATH apertium-preprocess-transfer ./rules/rules.xml ./rules/rules.bin
		popd
	done
	for dir in `ls -d tuning-$FILTMETHOD-*/`; do T=`echo "$dir" | sed 's:^[^-]*-[^-]*-::' | sed 's:^-:MINUS:' | cut -f 1 -d '-' | sed 's:^MINUS:-:'`; echo "$T" | cat - $dir/queries/dev-f-$T/experiment/evaluation/evaluation_learnedrules | tr '\n' '\t' | sed 's_$_\n_' ; done > ./tuning_data_$FILTMETHOD
	BEST_TRESHOLD=`cat ./tuning_data_$FILTMETHOD | sort -r  -k2,2 | head -n 1 | cut -f 1`
	echo "Best threshold: $BEST_TRESHOLD"
	cat ./tuning-$FILTMETHOD-$BEST_TRESHOLD-1-$BEST_TRESHOLD-subrules/summary > ./result_$FILTMETHOD
	echo "Result for size $SIZE :"
	cat ./result_$FILTMETHOD
	
	popd
	
	pushd $WORKDIRNOBEAM
	
	#check errors in first step
	scp euler.iuii.ua.es:/home/vmsanchez/results/experiments-linear-l5-${SL}-${TL}/$BILID/shuf$SIZE/generalisation-*.tar.gz ./
	for file in `ls generalisation-*.tar.gz`; do
	  tar xzf $file
	done
	
	#get filtering too
	scp euler.iuii.ua.es:/home/vmsanchez/results/experiments-linear-l5-${SL}-${TL}/$BILID/shuf$SIZE/filtering-$FILTMETHOD-*.tar.gz ./
	for file in `ls filtering-$FILTMETHOD-*.tar.gz`; do
	  tar xzf $file
	done
	
	#por aqui me he quedado
	DEBUGFILE=./debug-generalisation
	rm -f $DEBUGFILE
	for NUMBER in `cat generalisation/finalboxesindex | cut -f 1`; do
	  echo "$NUMBER:" >> $DEBUGFILE
	  zcat generalisation/debug/debug-generalisation-$NUMBER.gz | grep -v -F "Reading Bilingual Phrases" |  grep -v -F " ....." |  grep -v -F "Time performing structural generalisation" | grep -v -F "Time performing lexical generalisation" | grep -v -F "Time removing wrong alignments"  | grep -v -F "Time computing correct and matching ATs" | grep -v -F "Time generating afterwards restrictions" >> $DEBUGFILE
	done
	
	popd
	
done