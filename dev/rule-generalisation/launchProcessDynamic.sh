#! /bin/bash

#! /bin/bash

CURDIR=`dirname $0`

#shflags
. $CURDIR/shflags
DEFINE_string 'size' '500' 'Size of bilingual corpus' 'v'
DEFINE_string 'filtering_method' 'proportion_correct_bilphrases_thresholdrelaxabove2' 'Filtering method' 'f'
DEFINE_string 'source_language' 'es' 'Source language' 's'
DEFINE_string 'target_language' 'ca' 'Target language' 't'
DEFINE_string 'inverse_pair' '' 'INVERSE means that TL-SL is the name of the pair in Apertium' 'i'
DEFINE_string 'dev_corpus' 'consumer-eroski.dev' 'Development corpus' 'd'
DEFINE_string 'test_corpus' 'consumer-eroski.test' 'Test corpus' 'r'
DEFINE_string 'bilingual_phrases_id' 'marker-withcontradictions' 'Identifier of the starting bilingual phrases' 'b'
DEFINE_string 'num_parts_file' '20' 'Number of partitions of data' 'p'
DEFINE_string 'step' '' 'Step: 1= pregeneralisation, 2=generalisation 3=filtering, 4=tuning, empty=all'
DEFINE_string 'alg_version' 'NORMAL' '' 'o'
DEFINE_string 'beam_search' '' '' 'm'
DEFINE_boolean 'use_fixed_bildic' 'false' 'Use PAIR.autobil.fixed.bin dictionary' 'x'
DEFINE_boolean 'use_alt_set_of_bilphrases' 'false' 'Use alternative set of bilingual phrases and choose between them' 'a'

FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

if [ ${FLAGS_use_fixed_bildic} == ${FLAGS_TRUE} ]; then
  USE_FIXED_BILDIC_FLAG="--use_fixed_bildic"
else
  USE_FIXED_BILDIC_FLAG=""
fi

LOGSDIR=/home/vmsanchez/logs/
RESULTS_DIR=$HOME/results/experiments-linear-l5-${FLAGS_source_language}-${FLAGS_target_language}/${FLAGS_bilingual_phrases_id}/shuf${FLAGS_size}/

WAIT_INTERVAL=60
NUMGEN=`find  $RESULTS_DIR -name 'generalisation-*.tar.gz' | wc -l`
NUMPARTS=$((NUMGEN - 1))

NUMTHRESHOLDS=21

NUMPACKAGES=$((NUMPARTS * NUMTHRESHOLDS))

echo "Working with $NUMPARTS * $NUMTHRESHOLDS  = $NUMPACKAGES different packages"

THRESHOLDS_ARRAY=()
for THRESHOLD in `seq 1 -0.05 0`; do
	THRESHOLDS_ARRAY+=($THRESHOLD)
done

PACKAGE=0

RUNNINGJOBS=()
NUM_RUNNINGJOBS=0

CLUSTERIDS=()

while [ $NUM_RUNNINGJOBS -gt 0 -o $PACKAGE -lt $NUMPACKAGES ]; do

NUMPARALLEL=`cat ${FLAGS_num_parts_file}`
FREE_SLOTS=`expr $NUMPARALLEL - $NUM_RUNNINGJOBS`
echo "$FREE_SLOTS free slots"

#launch jobs to cover free slots
for i in `seq $FREE_SLOTS`; do
	
	if [ $PACKAGE -lt $NUMPACKAGES ]; then
		
		THRESHOLDINDEX=$((PACKAGE / NUMPARTS))
		THRESHOLD=${THRESHOLDS_ARRAY[THRESHOLDINDEX]}
		PART=$((PACKAGE % NUMPARTS))
		PARTP1=$((PART + 1))
		
		
		
		#launch job
		QSUBOUTPUT=`qsub $CURDIR/myExperiment-cluster-v5.sh --size "${FLAGS_size}" --filtering_method "${FLAGS_filtering_method}" --source_language "${FLAGS_source_language}" --target_language "${FLAGS_target_language}" --inverse_pair "${FLAGS_inverse_pair}" --dev_corpus "${FLAGS_dev_corpus}" --test_corpus "${FLAGS_test_corpus}" --bilingual_phrases_id "${FLAGS_bilingual_phrases_id}" --step "2" --touch_when_finished "$RESULTS_DIR/$PARTP1.filter.${FLAGS_filtering_method}.$THRESHOLD.finished" --part "${PARTP1}-${NUMPARTS}" --alg_version ${FLAGS_alg_version} $USE_FIXED_BILDIC_FLAG --only_one_threshold $THRESHOLD`
		
		JOBID=`echo $QSUBOUTPUT | cut -f 3 -d ' '`
		echo "Launched package $PACKAGE, part $PART, threshold $THRESHOLD, id $JOBID"
		CLUSTERIDS[PACKAGE]=$JOBID
		
		RUNNINGJOBS+=("$PACKAGE")
		
		PACKAGE=$((PACKAGE + 1))
	fi
done

#wait
sleep $WAIT_INTERVAL

echo "Checking finished jobs ..."
NEWRUNNINGJOBS=()
#check how many jobs have finished
for JOB in "${RUNNINGJOBS[@]}"; do
	
	THRESHOLDINDEX=$((JOB / NUMPARTS))
	THRESHOLD=${THRESHOLDS_ARRAY[THRESHOLDINDEX]}
	PART=$((JOB % NUMPARTS))
	PARTP1=$((PART + 1))
	
     if [ -f "$RESULTS_DIR/$PARTP1.filter.${FLAGS_filtering_method}.$THRESHOLD.finished" ]; then
     	echo "$JOB, part $PART, threshold $THRESHOLD finished"
     	JOBID=${CLUSTERIDS[JOB]}
     	
     	cp $LOGSDIR/myexperiment.$JOBID.err $RESULTS_DIR/log.$PARTP1.filter.${FLAGS_filtering_method}.$THRESHOLD.err
     	cp $LOGSDIR/myexperiment.$JOBID.out $RESULTS_DIR/log.$PARTP1.filter.${FLAGS_filtering_method}.$THRESHOLD.out
     	
     else
     	NEWRUNNINGJOBS+=("$JOB")
     fi
     
done
RUNNINGJOBS=(${NEWRUNNINGJOBS[@]})

echo "... done"

#we will launch the difference between the amount of running jobs and NUMPARALLEL
NUM_RUNNINGJOBS=${#RUNNINGJOBS[@]}

echo "$NUM_RUNNINGJOBS still running"

done
