#! /bin/bash

DIR=""
SL="es"
TL="ca"
INVERSE_PAIR=""
DEVELOPMENT_CORPUS=""
TEST_CORPUS=""
REMOVE_WW="no"

START_T="15"
END_T="2"
STEP_T="-1"

CORPUS_ID=""

FILTERING_OPTION="count"

GET_RESULT="yes"

CURDIR=`dirname $0`

TAGSEQUENCESANDGROUPSSUFFIX=""

PYTHONHOME=""

INPUTDIR=""

APERTIUM_SOURCES_FLAG=""
APERTIUM_SOURCES=""
APERTIUM_PREFIX_FLAG=""
APERTIUM_PREFIX=""

THRESHOLD_PROPORTION_FLAG=""

BOX_THRESHOLD="0"

SUBRULES="no"

GET_RESULT_FROM_BEAMSEARCH="no"

GENERALISATION_DIR_SUFFIX=""

FILTERING_DIR_PREFIX=""

ORIGINAL_TRAINING_CORPUS=""

PARALLELONLYONE=""

#-y option returns to classic ATS 
RICHATSFLAG="-c"

SHORT_RESTRICTIONS_INFIX=".shortrestrictions"
LFLAG=""

#Moved to another file
#subrule_fun()
#{
#	
#}
#export -f subrule_fun


usage()
{
cat << EOF
Bla bla bla	
	
EOF
}

while getopts “s:t:d:n:c:e:r:b:a:o:u:igwjx:h:p:f:lm:zk:qyv” OPTION
do
     case $OPTION in
         s)
             SL=$OPTARG
             ;;
         t)
             TL=$OPTARG
             ;;
         d)
             DIR=$OPTARG
             ;;
         n)
            INPUTDIR=$OPTARG
            ;;
         c)
             DEVELOPMENT_CORPUS=$OPTARG
             ;;
         e)
             TEST_CORPUS=$OPTARG
             ;;
         i)
             INVERSE_PAIR="-i"
             ;;
        w)
                REMOVE_WW="yes"
                ;;
        z)
                SUBRULES="yes"
                ;;
        r)
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
        g)
                GET_RESULT="no"
                ;;
        u)
                CORPUS_ID=$OPTARG
                ;;
        x)
                TAGSEQUENCESANDGROUPSSUFFIX=$OPTARG
                ;;
        h)
                PYTHONHOME=$OPTARG
                ;;
        p)
                APERTIUM_PREFIX_FLAG="-p $OPTARG"
                APERTIUM_PREFIX=$OPTARG
                ;;
        f)
                APERTIUM_SOURCES_FLAG="-u $OPTARG"
                APERTIUM_SOURCES=$OPTARG
                ;;
        l)
                SHORT_RESTRICTIONS_INFIX=""
                LFLAG="-l"
                ;;
        m)
                BOX_THRESHOLD=$OPTARG
                ;;
        j)
                FILTERING_DIR_PREFIX="joined-"
                ;;
        k)
               ORIGINAL_TRAINING_CORPUS=$OPTARG
               SUBRULES="yes"
               ;;
        q)
               PARALLELONLYONE="-j 1"
               ;;
        y)
		RICHATSFLAG=""
		;;
	v)
		GET_RESULT_FROM_BEAMSEARCH="yes"
		;;
         ?)
             usage
             exit
             ;;
     esac
done

if [ "$INPUTDIR" == "" ]; then
	INPUTDIR="$DIR"
fi

REMOVE_WW_FLAG=""
REMOVE_WW_COMMAND=" cat - "
if [ "$REMOVE_WW" == "yes" ]; then
REMOVE_WW_FLAG="-noww"
REMOVE_WW_COMMAND=" ${PYTHONHOME}python $CURDIR/removeLastATifWordForWord.py "
elif [ "$SUBRULES" == "yes" ]; then
	if [ "$ORIGINAL_TRAINING_CORPUS" == "" ]; then
		REMOVE_WW_FLAG="-subrules"
	else
		REMOVE_WW_FLAG="-optwer"
	fi
fi 

PAIR="${SL}-${TL}"
if [ "$INVERSE_PAIR" == "-i" ]; then
	PAIR="${TL}-${SL}"
fi

if [ "$PYTHONHOME" == "" ]; then
	PYTHONHOME_FLAG=""
else
	PYTHONHOME_FLAG="-h $PYTHONHOME"
fi

BOX_THRESHOLD_FLAG=""
if [ "$BOX_THRESHOLD" != 0 ]; then
	BOX_THRESHOLD_FLAG="-box$BOX_THRESHOLD"
fi

TUNING_ID="${FILTERING_OPTION}-${START_T}-${STEP_T}-${END_T}$REMOVE_WW_FLAG$CORPUS_ID$THRESHOLD_PROPORTION_FLAG$BOX_THRESHOLD_FLAG"

mkdir -p $DIR/tuning-$TUNING_ID

#if [ "$GET_RESULT_FROM_BEAMSEARCH" == "yes" ]; then
#	OUTPUT_DIR=$DIR/tuning-$TUNING_ID/
#	for treshold in `LC_ALL=C seq $START_T $STEP_T $END_T`; do
#		if [ ! -f $OUTPUT_DIR/result-f-${treshold}.gz ]; then
#			cp $INPUTDIR/maximise-score-$FILTERING_OPTION/result-f-${treshold}.gz $OUTPUT_DIR/result-f-${treshold}.gz
#		fi
#	done
#el

if [ "$GET_RESULT" == "yes" ]; then

	if [ "$SUBRULES" == "yes" ]; then
		# subchorizo
		#sort boxes
		OUTPUT_DIR=$DIR/tuning-$TUNING_ID/subrules
		mkdir -p $DIR/tuning-$TUNING_ID/subrules
		cat $INPUTDIR/generalisation$GENERALISATION_DIR_SUFFIX/finalboxesindex |  grep -v "^$"  | awk  '{split($2,splitted,"__"); print $1 "\t" $2 "\t" length(splitted)}' | sort -n -k3,3 | awk '{print $1}' > $DIR/tuning-$TUNING_ID/subrules/sortedboxesindex
		NUMBERS=`cat $DIR/tuning-$TUNING_ID/subrules/sortedboxesindex`
	else
		OUTPUT_DIR=$DIR/tuning-$TUNING_ID/		
		NUMBERS=`ls $INPUTDIR/${FILTERING_DIR_PREFIX}filtering-$FILTERING_OPTION/ats | awk -F"-" '{print $1}' | awk -F"." '{print $1}'  | LC_ALL=C sort | uniq`
	fi
	
	
	
	#for treshold in `LC_ALL=C seq $START_T $STEP_T $END_T | sed -r 's_\.?[0]+$__'`; do
	for treshold in `LC_ALL=C seq $START_T $STEP_T $END_T`; do
	
		if [ ! -f $OUTPUT_DIR/result-f-${treshold}.gz ]; then
		#rm -f $DIR/result-f-${treshold}-$FILTERING_OPTION$REMOVE_WW_FLAG
		#rm -f $DIR/result-f-${treshold}-$FILTERING_OPTION${REMOVE_WW_FLAG}.gz
		
		if [ "$GET_RESULT_FROM_BEAMSEARCH" == "yes" ]; then
		  if [ "$SUBRULES" == "yes" ]; then
			  # subchorizo
			  #sort boxes
			  for box in `cat $DIR/tuning-$TUNING_ID/subrules/sortedboxesindex`; do
			    zcat $INPUTDIR/maximise-score-$FILTERING_OPTION/rulesid-f-${treshold}.gz | grep "^$box\$" >>  $DIR/tuning-$TUNING_ID/subrules/sortedboxesindex-$treshold
			  done			  
			  NUMBERS=`cat $DIR/tuning-$TUNING_ID/subrules/sortedboxesindex-$treshold`
		  else
			  NUMBERS=`zcat $INPUTDIR/maximise-score-$FILTERING_OPTION/rulesid-f-${treshold}.gz`
		  fi
		
		fi
		
		TOTALNUMBERS=`echo "$NUMBERS" | wc -l`
		
		rm -f $DIR/tuning-$TUNING_ID/minimisationsummary-$treshold
		rm -f $DIR/tuning-$TUNING_ID/minimisationsummary-$treshold.gz
		
		BOXESWITHOUTSOLUTION=0
		BOXESWITHERROR=0
		
		for number in $NUMBERS; do
			VALIDNUMBER="yes"
			if [ "$BOX_THRESHOLD" != 0 ]; then
				BOX_FREQ=`zcat "$INPUTDIR/generalisation$GENERALISATION_DIR_SUFFIX/ats/${number}.bilphrases.gz" | cut -f 1 -d '|' | awk '{s+=$1} END {print s}'`
				if [ "$BOX_FREQ" -lt "$BOX_THRESHOLD" ]; then
					VALIDNUMBER="no"
				fi
			fi
			
			#get information about minimisation problem
			#PENALTYRESULT=`zcat $INPUTDIR/filtering-$FILTERING_OPTION/debug/${number}-f-${treshold}$THRESHOLD_PROPORTION_FLAG.result.debug.gz | sed -n '/Penalty =/,/BILINGUAL_PHRASES/p'`
			PENALTYRESULT=`zcat $INPUTDIR/${FILTERING_DIR_PREFIX}filtering-$FILTERING_OPTION/debug/${number}-f-${treshold}$THRESHOLD_PROPORTION_FLAG.result.debug.gz | tac | sed -e '/^Relaxed bilingual phrases:$/,$d' | tac | sed -e '/^BILINGUAL_PHRASES$/,$d'`
			PYTHONERRORRESULTLEN=`zcat $INPUTDIR/${FILTERING_DIR_PREFIX}filtering-$FILTERING_OPTION/debug/${number}-f-${treshold}$THRESHOLD_PROPORTION_FLAG.result.debug.gz | grep "^Traceback" | wc -l`
			
			LENGTHRESULT=`echo "$PENALTYRESULT" | wc -l`
			
			if [ $PYTHONERRORRESULTLEN -gt 0 ]; then
			  BOXESWITHERROR=`expr $BOXESWITHERROR + 1`
			  echo "$number : " >> $DIR/tuning-$TUNING_ID/minimisationsummary-$treshold
			  zcat $INPUTDIR/${FILTERING_DIR_PREFIX}filtering-$FILTERING_OPTION/debug/${number}-f-${treshold}$THRESHOLD_PROPORTION_FLAG.result.debug.gz >> $DIR/tuning-$TUNING_ID/minimisationsummary-$treshold
			elif [ $LENGTHRESULT -gt 3 ]; then
			    BOXESWITHOUTSOLUTION=`expr $BOXESWITHOUTSOLUTION + 1`
			    echo "$number : " >> $DIR/tuning-$TUNING_ID/minimisationsummary-$treshold
			    echo "$PENALTYRESULT" | head -n -1 | tail -n +2 >> $DIR/tuning-$TUNING_ID/minimisationsummary-$treshold
			fi
			
			
			if [ "$VALIDNUMBER" == "yes" ]; then
				zcat "$INPUTDIR/${FILTERING_DIR_PREFIX}filtering-$FILTERING_OPTION/ats/${number}-f-${treshold}$THRESHOLD_PROPORTION_FLAG.result.gz" | exec $REMOVE_WW_COMMAND | tee $OUTPUT_DIR/result-f-${treshold}-$number  >> $OUTPUT_DIR/result-f-${treshold}; 
				cat $OUTPUT_DIR/result-f-${treshold}-$number | sed "s:.*:$number:" >> $OUTPUT_DIR/boxes-f-${treshold}
				NUMRULESBOX=`cat $OUTPUT_DIR/result-f-${treshold}-$number | wc -l`
				echo "$number	$NUMRULESBOX" >> $OUTPUT_DIR/numrules-${treshold}
				rm $OUTPUT_DIR/result-f-${treshold}-$number
			fi
		done
		
		echo "Summary: infeasible problems: $BOXESWITHOUTSOLUTION / $TOTALNUMBERS" >> $DIR/tuning-$TUNING_ID/minimisationsummary-$treshold
		echo "Summary: error problems: $BOXESWITHERROR / $TOTALNUMBERS" >> $DIR/tuning-$TUNING_ID/minimisationsummary-$treshold
		
		gzip $DIR/tuning-$TUNING_ID/minimisationsummary-$treshold
		gzip $OUTPUT_DIR/result-f-${treshold}

		fi
	done
	

	if [ "$SUBRULES" == "yes" ]; then
		BILDICTIONARY=$APERTIUM_SOURCES/apertium-$PAIR/${SL}-$TL.autobil${SHORT_RESTRICTIONS_INFIX}.bin
		parallel $PARALLELONLYONE -i bash -c "if [ ! -f $DIR/tuning-$TUNING_ID/result-f-{}.gz ]; then mkdir -p $DIR/tuning-$TUNING_ID/subrules/{}; zcat $DIR/tuning-$TUNING_ID/subrules/result-f-{}.gz > $DIR/tuning-$TUNING_ID/subrules/{}/initialrules; ln -s  ../`basename $DIR/tuning-$TUNING_ID/subrules/boxes-f-{}` $DIR/tuning-$TUNING_ID/subrules/{}/boxes; bash $CURDIR/removeRedundantRules.sh $DIR/tuning-$TUNING_ID/subrules/{}/initialrules $DIR/tuning-$TUNING_ID/subrules/{}/boxes \"$CURDIR\" \"$SL\" \"$TL\" \"$APERTIUM_PREFIX\" \"$TAGSEQUENCESANDGROUPSSUFFIX\" \"$INPUTDIR/${FILTERING_DIR_PREFIX}filtering-$FILTERING_OPTION/debug\" \"-f-{}.result.debug.gz\" \"$BILDICTIONARY\" \"$PYTHONHOME\" \"$RICHATSFLAG\" \"$APERTIUM_SOURCES\" \"$ORIGINAL_TRAINING_CORPUS\" \"keep\" 2>&1 > $DIR/tuning-$TUNING_ID/subrules/{}-debug ; cp $DIR/tuning-$TUNING_ID/subrules/{}/initialrules.reduced.gz $DIR/tuning-$TUNING_ID/result-f-{}.gz; cp $DIR/tuning-$TUNING_ID/subrules/{}/initialrules.reduced.gz $DIR/tuning-$TUNING_ID/result-f-{}.gz; cp $DIR/tuning-$TUNING_ID/subrules/{}/summary.gz $DIR/tuning-$TUNING_ID/subrules/summary-f-{}.gz; cp $DIR/tuning-$TUNING_ID/subrules/{}/summary.debug.gz $DIR/tuning-$TUNING_ID/subrules/summary-f-{}.debug.gz ; rm -Rf $DIR/tuning-$TUNING_ID/subrules/{} ;  fi" -- `LC_ALL=C seq $START_T $STEP_T $END_T` 
	fi

fi


mkdir -p $DIR/tuning-$TUNING_ID/debug
mkdir -p $DIR/tuning-$TUNING_ID/queries


if [ "$DEVELOPMENT_CORPUS" != "" ]; then 
    echo "evaluating different thresholds"
    TUNING_FILE=$DIR/tuning-$TUNING_ID/tuning_data
    rm -f $TUNING_FILE
    for treshold in `LC_ALL=C seq $START_T $STEP_T $END_T`; do
            if [ ! -f  $DIR/tuning-$TUNING_ID/queries/dev-f-${treshold}/experiment/evaluation/evaluation_learnedrules ]; then
            bash $CURDIR/evaluate-experiment-linear-v5.sh $LFLAG -x "$TAGSEQUENCESANDGROUPSSUFFIX" -s $SL -t $TL $INVERSE_PAIR -f $DIR/tuning-$TUNING_ID/result-f-${treshold}.gz -z -d $DIR/tuning-$TUNING_ID -q dev-f-${treshold} -e $DEVELOPMENT_CORPUS $APERTIUM_SOURCES_FLAG $APERTIUM_PREFIX_FLAG $PYTHONHOME_FLAG $RICHATSFLAG 2> $DIR/tuning-$TUNING_ID/debug/debug-eval-dev-f-${treshold}
            tail -n 1 $DIR/tuning-$TUNING_ID/queries/dev-f-${treshold}/experiment/evaluation/evaluation_learnedrules | sed "s_^_$treshold\t_" >> $TUNING_FILE
            fi
    done
    
    #choose best threshold
    BEST_TRESHOLD=`cat $TUNING_FILE | sort -r  -k2,2 | head -n 1 | cut -f 1`
    echo "Best threshold afer tuning: $BEST_TRESHOLD"
else
    BEST_TRESHOLD=`LC_ALL=C seq $START_T $STEP_T $END_T | head -n 1`
    echo "No dev corpus defined. Using threshold: $BEST_TRESHOLD"
fi

echo "translating test corpus with the best threshold"
#evaluate
bash $CURDIR/evaluate-experiment-linear-v5.sh -y $LFLAG -x "$TAGSEQUENCESANDGROUPSSUFFIX" -s $SL -t $TL $INVERSE_PAIR -f $DIR/tuning-$TUNING_ID/result-f-${BEST_TRESHOLD}.gz -z -d $DIR/tuning-$TUNING_ID -q test-f-${BEST_TRESHOLD} -e "$TEST_CORPUS" $APERTIUM_SOURCES_FLAG $APERTIUM_PREFIX_FLAG $PYTHONHOME_FLAG $RICHATSFLAG 2> $DIR/tuning-$TUNING_ID/debug/debug-eval-test-f-${BEST_TRESHOLD}

if [ "$TEST_CORPUS" != "" ]; then

tail -n 1 $DIR/tuning-$TUNING_ID/queries/test-f-${BEST_TRESHOLD}/experiment/evaluation/evaluation_learnedrules > $DIR/tuning-$TUNING_ID/evaluation

#Create summary: BLEU, TER, BEST THRESHOLD and NUM RULES
cp $DIR/tuning-$TUNING_ID/evaluation $DIR/tuning-$TUNING_ID/summary
tail -n 1 $DIR/tuning-$TUNING_ID/queries/test-f-${BEST_TRESHOLD}/experiment/evaluation/ter_learnedrules >> $DIR/tuning-$TUNING_ID/summary
echo "$BEST_TRESHOLD" >> $DIR/tuning-$TUNING_ID/summary
zcat $DIR/tuning-$TUNING_ID/result-f-${BEST_TRESHOLD}.gz | wc -l >> $DIR/tuning-$TUNING_ID/summary
#tail -n 1 $DIR/tuning-$TUNING_ID/queries/test-f-${BEST_TRESHOLD}/experiment/evaluation/numrulesx >> $DIR/tuning-$TUNING_ID/summary
fi

if [ "$DEVELOPMENT_CORPUS" != "" ]; then

#Create plot for tuning data
cd $DIR/tuning-$TUNING_ID/
gnuplot -e "set term post eps; set output 'plot.tuningdata.eps'; plot 'tuning_data' with linespoints"

fi