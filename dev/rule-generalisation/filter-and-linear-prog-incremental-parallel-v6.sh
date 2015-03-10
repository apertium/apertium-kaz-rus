#!/bin/bash

function do_filter {
TRUEWORKDIR=$1
FILTERING_OPTION=$2
number=$3
START_T=$4
STEP_T=$5
END_T=$6
CURDIR=$7
PYTHONHOME=$8
TRUEINPUTWORKDIR=$9
TAGSEQUENCESANDGROUPSSUFFIX=${10}
DIRSUFFIX=${11}


PERFORM_ACTUAL_FILTERING="yes"

#DEBUG
#echo "filtering $number" >&2

SOURCEOFATS="$TRUEINPUTWORKDIR/generalisation$DIRSUFFIX/ats"


if [[ $FILTERING_OPTION == *contrabefore* ]]; then
	SOURCEOFATS="$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/nocontra"
	mkdir -p $TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/nocontra
	python $CURDIR/chooseATs.py --tag_groups_file $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --tag_sequences_file $CURDIR/tagsequences$TAGSEQUENCESANDGROUPSSUFFIX --gzip  --remove_contradictory_ats --read_generalised_bilphrases_from_dir "$TRUEINPUTWORKDIR/generalisation$DIRSUFFIX/ats" --read_generalised_ats_from_file "$TRUEINPUTWORKDIR/generalisation$DIRSUFFIX/ats/$number" --only_filter "$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/nocontra/$number" 2> "$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/debug/$number.contrabefore.debug" | gzip > "$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/nocontra/$number.ats.gz"
	gzip "$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/debug/$number.contrabefore.debug"
fi


SECOND_FILTERING="cat -"
if [[ $FILTERING_OPTION == *above[0-9]* ]]; then
	MIN=`echo "$FILTERING_OPTION" | sed 's_.*above\([0-9]*\)$_\1_'`
	SECOND_FILTERING="${PYTHONHOME}python $CURDIR/filterAlignmentTemplates.py --min_count $MIN --criterion count"
fi

MAX="NONE"
if [[ $FILTERING_OPTION == *boxposrest* ]]; then
	if [[ $FILTERING_OPTION == propmax* ]]; then
		MAX=`zcat "$SOURCEOFATS/${number}.ats.gz" | sort -t '|' -k 1,1 -n -r | head -n 1 | cut -f 1 -d '|' | sed 's_ *$__'`
	elif [[ $FILTERING_OPTION == proptotal* ]]; then
		MAX=`zcat "$TRUEINPUTWORKDIR/generalisation$DIRSUFFIX/newbilphrases/${number}.bilphrases.gz" | cut -f 1 -d '|' | awk '{s+=$1} END {print s}'`
	else
		echo "ERROR"
	fi

#esto no funciona bien
elif [[ $FILTERING_OPTION == *boxonlypos* ]]; then
	POSSEQ=`zcat "$SOURCEOFATS/${number}.ats.gz" | head -n 1 | cut -f 2 -d '|' | sed 's_[^ <]*\(<[^>]*>\)[^ ]* _\1 _g' | sed 's_^ __' | sed 's_ $__'`
	if [[ $FILTERING_OPTION == propmax* ]]; then
		MAX=`zcat $TRUEINPUTWORKDIR/generalisation$DIRSUFFIX/boxonlypos.max.gz | grep "| $POSSEQ\$" | cut -f 1 -d '|' | sed 's_ $__'`
	elif [[ $FILTERING_OPTION == proptotal* ]]; then
		MAX=`zcat $TRUEINPUTWORKDIR/generalisation$DIRSUFFIX/boxonlypos.total.gz | grep "| $POSSEQ\$" | cut -f 1 -d '|' | sed 's_ $__'`
	else
		echo "ERROR"
	fi
elif [[ $FILTERING_OPTION == count* ]]; then
	MAX=1
fi

PERFORM_FIRST_FILTERING="yes"
if [ "$MAX" == "NONE" ]; then
	PERFORM_FIRST_FILTERING="no"
fi

#different output files depending whether the filtering in this step
#uses the threshold (first filtering = uses threshold)

MYFILE="$SOURCEOFATS/${number}.ats.gz"
if [ "$PERFORM_FIRST_FILTERING" == "no" ]; then
	OUTPUT_FILE="$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/ats/${number}.ats.gz"
	if [ "$SECOND_FILTERING" == "cat -" ]; then
		ln -s `readlink -f "$MYFILE"` `readlink -f "$OUTPUT_FILE"`
	else
		zcat "$MYFILE"  | exec $SECOND_FILTERING | gzip >  "$OUTPUT_FILE"
	fi
else
	for treshold in `LC_ALL=C seq $START_T $STEP_T $END_T`; do
		zcat "$MYFILE" | ${PYTHONHOME}python $CURDIR/filterAlignmentTemplates.py --min_count $treshold --criterion proportion --proportion_max $MAX  | exec $SECOND_FILTERING | gzip >  "$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/ats/${number}-f-${treshold}.ats.gz"
	done
fi
	
}
export -f do_filter

WORKDIR=../work-es-ca-transfertools-2M/linear-experiments
ID="shuf10"
CURDIR=`dirname $0`

START_T="15"
END_T="2"
STEP_T="-1"

FILTERING_OPTION="count"

TAGSEQUENCESANDGROUPSSUFFIX=""

PYTHONHOME=""

INPUTWORKDIR=""

THRESHOLD_PROPORTION=""

ONLY_FILTERING="no"
ONLY_LINEAR="no"

FILTERING_IN_LINEAR="no"

PARALLELONLYONE=""

DIRSUFFIX=""

usage()
{
cat << EOF
Bla bla bla	
	
EOF
}



while getopts “d:i:s:b:a:o:x:h:w:t:flnqm” OPTION
do
     case $OPTION in

         d)
             WORKDIR=$OPTARG
             ;;
         m)
	    DIRSUFFIX="-alt1"
	    ;;
         
         w)
			 INPUTWORKDIR=$OPTARG
			 ;;
         i)
			 ID=$OPTARG
			 ;;
		 s)
		     START_T=$OPTARG
		     ;;
		 b)
		     END_T=$OPTARG
		     ;;
		 a)
		     STEP_T=$OPTARG
		     ;;
		 o)
		     FILTERING_OPTION=$OPTARG
			 ;;
		 x)
			 TAGSEQUENCESANDGROUPSSUFFIX=$OPTARG
			 ;;
		 h)
			 PYTHONHOME=$OPTARG
			 ;;
		 t)
			 THRESHOLD_PROPORTION=$OPTARG
			 ;;
		 f)
			 ONLY_FILTERING="yes"
			 ;;
		 l)
			 ONLY_LINEAR="yes"
			 ;;
		 n)
			FILTERING_IN_LINEAR="yes"
			;;
		 q)
			PARALLELONLYONE="-j 1"
			;;
         ?)
             usage
             exit
             ;;
     esac
done

if [ "$INPUTWORKDIR" == "" ]; then
	INPUTWORKDIR="$WORKDIR"
fi

TRUEWORKDIR="$WORKDIR/$ID"
TRUEINPUTWORKDIR="$INPUTWORKDIR/$ID"
mkdir -p $TRUEWORKDIR

THRESHOLD_PROPORTION_FLAG_FILENAME=""
THRESHOLD_PROPORTION_FLAG_ARGUMENT=""

if [ "$THRESHOLD_PROPORTION" != "" ]; then
THRESHOLD_PROPORTION_FLAG_ARGUMENT="--proportion_correct_bilphrases_threshold $THRESHOLD_PROPORTION"
THRESHOLD_PROPORTION_FLAG_FILENAME="-t$THRESHOLD_PROPORTION"
fi

FILTERING_IN_LINEAR_FLAG_PREFIX=""
if [ "$FILTERING_IN_LINEAR" == "yes" ]; then
	FILTERING_IN_LINEAR_FLAG_PREFIX=`echo "$FILTERING_OPTION" | sed -r 's:(extendedrange)?(relax)?(nocontra)?(symmdiff)?(firstrestrictions)?(dontaddznorest)?(dynamic[0-9]+)?(above[0-9]+)?$::'`
    FILTERING_IN_LINEAR_FLAG_PREFIX="--$FILTERING_IN_LINEAR_FLAG_PREFIX "
fi



#filter by freq

#treshold_to_test=`seq $START_T $STEP_T $END_T | tail -n 1 | sed 's_,_._'`

echo "Filtering ATs" >&2

mkdir -p $TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/ats
mkdir -p $TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/debug

ls  $TRUEINPUTWORKDIR/generalisation$DIRSUFFIX/ats | awk -F"." '{print $1}' | LC_ALL=C sort | uniq > $TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/boxesforfiltering
split -l 10000 $TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/boxesforfiltering $TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/boxesforfiltering.split

if [ "$ONLY_LINEAR" != "yes" ]; then

for file in $TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/boxesforfiltering.split* ; do
parallel -i  bash -c " do_filter \"$TRUEWORKDIR\" \"$FILTERING_OPTION\" \"{}\" \"$START_T\" \"$STEP_T\" \"$END_T\" \"$CURDIR\" \"$PYTHONHOME\" \"$TRUEINPUTWORKDIR\" \"$TAGSEQUENCESANDGROUPSSUFFIX\" \"$DIRSUFFIX\" " -- `cat $file`
done

fi

if [ "$ONLY_FILTERING" != "yes" ]; then

echo "Running linear programming" >&2
#run linear programming
for treshold in `LC_ALL=C seq $START_T $STEP_T $END_T`; do
	rm -f "$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/debug/statuses-${treshold}$THRESHOLD_PROPORTION_FLAG_FILENAME"
	
	ATS_DIR="$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/ats"
	ATS_SUFFIX="-f-${treshold}"
	if [ "$FILTERING_IN_LINEAR_FLAG_PREFIX" != "" ]; then
		ATS_SUFFIX=""
	fi
	
	CONTRADICTORYORRELAX="--remove_contradictory_ats"
	if [[ $FILTERING_OPTION == *relaxnocontra* ]]; then
		CONTRADICTORYORRELAX="--remove_contradictory_ats --relax_restrictions"
	elif [[ $FILTERING_OPTION == *relax* ]]; then
		CONTRADICTORYORRELAX="--relax_restrictions"
	fi
	tresholdForLinear="$treshold"
	if [[ $FILTERING_OPTION == relax_weight* ]]; then
		tresholdForLinear="math.pow(10,${treshold})*len(at_list)"
	fi
	
	SYMDIFFLAG=""
	if [[ $FILTERING_OPTION == *symmdiff* ]]; then
		SYMDIFFLAG="--symmetric_difference"
	fi
	
	RESTRICTIONMINIMISATIONFLAG=""
	if [[ $FILTERING_OPTION == *firstrestrictions* ]]; then
		RESTRICTIONMINIMISATIONFLAG="--first_select_restrictions"
	fi
	
	ADDZNORESTFLAG=""
	if [[ $FILTERING_OPTION == *firstrestrictionsdontaddznorest* ]]; then
		ADDZNORESTFLAG="--dont_add_znorest"
	fi
	
	DYNAMICFLAG=""
	if [[ $FILTERING_OPTION == *dynamic* ]]; then
		NUMBER=`echo "$FILTERING_OPTION" | sed 's_.*dynamic\([0-9]*\)above.*$_\1_'`
		DYNAMICFLAG="--dynamic_theta $NUMBER"
	fi
	
	
	for file in $TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/boxesforfiltering.split* ; do
		STARTTIME=`date +'%s'` 
		parallel $PARALLELONLYONE -i  bash -c " rm -f \"$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/debug/{}-f-${treshold}$THRESHOLD_PROPORTION_FLAG_FILENAME.result.debug.gz\"; FILTERING_IN_LINEAR_FLAG=\"\"; if [ \"$FILTERING_IN_LINEAR_FLAG_PREFIX\" != \"\" ]; then FILTERING_IN_LINEAR_FLAG=\"$FILTERING_IN_LINEAR_FLAG_PREFIX $tresholdForLinear\"; fi; ${PYTHONHOME}python $CURDIR/chooseATs.py --tag_groups_file $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --tag_sequences_file $CURDIR/tagsequences$TAGSEQUENCESANDGROUPSSUFFIX --gzip \$FILTERING_IN_LINEAR_FLAG $CONTRADICTORYORRELAX --read_generalised_bilphrases_from_dir \"$TRUEINPUTWORKDIR/generalisation$DIRSUFFIX/newbilphrases\"  $THRESHOLD_PROPORTION_FLAG_ARGUMENT --read_generalised_ats_from_file \"$ATS_DIR/{}$ATS_SUFFIX\" --remove_third_restriction $SYMDIFFLAG $ADDZNORESTFLAG $RESTRICTIONMINIMISATIONFLAG $DYNAMICFLAG 2> \"$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/debug/{}-f-${treshold}$THRESHOLD_PROPORTION_FLAG_FILENAME.result.debug\"  |  grep  \"<[^>]*>\" | gzip > \"$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/ats/{}-f-${treshold}$THRESHOLD_PROPORTION_FLAG_FILENAME.result.gz\"; cat \"$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/debug/{}-f-${treshold}$THRESHOLD_PROPORTION_FLAG_FILENAME.result.debug\" | grep -F \"Status:\" | sed 's_^_{}_' >> \"$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/debug/statuses-${treshold}$THRESHOLD_PROPORTION_FLAG_FILENAME\" ; gzip -f \"$TRUEWORKDIR/filtering-$FILTERING_OPTION$DIRSUFFIX/debug/{}-f-${treshold}$THRESHOLD_PROPORTION_FLAG_FILENAME.result.debug\" " -- `cat $file`
		ENDTIME=`date +'%s'` 
		DURATION=$((ENDTIME-STARTTIME))
		echo "  Finished $file . Took $DURATION seconds" >&2
	done
	
	echo "Finished linear programming $treshold" >&2
done

fi
