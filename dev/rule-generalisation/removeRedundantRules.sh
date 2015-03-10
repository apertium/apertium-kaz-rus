#! /bin/bash

RULES_FILE=$1
BOXES_FILE=$2
CURDIR=$3
MYDIR=`dirname $RULES_FILE`
SL=$4
TL=$5
APERTIUM_PREFIX=$6
TAGSEQUENCESANDGROUPSSUFFIX=$7
BILPHRASES_DIR=$8
DEBUGINFOFILESUFFIX=$9
BILDICTIONARY=${10}
PYTHONHOME=${11}
RICHATSMARK=${12}
APERTIUM_SOURCES=${13}
#-c = rich ats
#empty = classic ats

RICHATSFLAG=""
if [ "$RICHATSMARK" == "-c" ]; then
	RICHATSFLAG="--emptyrestrictionsmatcheverything"
fi

ANALYSED_PARALLEL_CORPUS="${14}"
USE_CORPUS=false

KEEPTMPDIRS=false
if [ "${15}" == "keep" ]; then
	KEEPTMPDIRS=true
fi



if [ "$ANALYSED_PARALLEL_CORPUS" != "" ]; then
	USE_CORPUS=true
fi

if $USE_CORPUS ; then
	#get TL side of corpus and clean spaces
	zcat $ANALYSED_PARALLEL_CORPUS.${TL}.gz | sed -r 's_^ *\^_^_' | sed -r 's_\$ *\^_$ ^_g' | sed -r 's_ *$__'  > $MYDIR/referenceCorpus.${TL}
fi

if [ "$APERTIUM_PREFIX" != "" ]; then
  TRANSFERTOOLSPATH="LD_LIBRARY_PATH=$APERTIUM_PREFIX/lib $APERTIUM_PREFIX/bin/"
  APERTIUMPATH="$APERTIUM_PREFIX/bin/"
else
  TRANSFERTOOLSPATH=""
  APERTIUMPATH=""
fi

cat $RULES_FILE | gzip > ${RULES_FILE}.1.upper.gz
echo -n  "" | gzip > ${RULES_FILE}.1.lower.gz
ITERATION="1"

LINE=`zcat ${RULES_FILE}.${ITERATION}.upper.gz | wc -l`
while [ "$LINE" -gt "0" ]
do
      BOXNUMBER=`cat $BOXES_FILE | head -n $LINE | tail -n 1`
      mkdir -p $MYDIR/queries/$ITERATION/experiment
      
      if $USE_CORPUS ; then
		  mkdir -p $MYDIR/queries/${ITERATION}-ref/experiment
		 NUMATS=`zcat ${RULES_FILE}.${ITERATION}.upper.gz ${RULES_FILE}.${ITERATION}.lower.gz  | wc -l `
		  
		  zcat ${RULES_FILE}.${ITERATION}.upper.gz ${RULES_FILE}.${ITERATION}.lower.gz | { 
		  CURAT=$NUMATS
		  while read line
		  do 
			  echo "$CURAT | $line"
			  CURAT=`expr $CURAT - 1`
		  done }  > $MYDIR/queries/${ITERATION}-ref/experiment/alignmentTemplatesGeneralisedResult.txt
		  
		  zcat ${RULES_FILE}.${ITERATION}.upper.gz |  head -n -1 | gzip | zcat - ${RULES_FILE}.${ITERATION}.lower.gz | { 
		  CURAT=$NUMATS
		  while read line
		  do 
			  echo "$CURAT | $line"
			  CURAT=`expr $CURAT - 1`
		  done }  > $MYDIR/queries/${ITERATION}/experiment/alignmentTemplatesGeneralisedResult.txt
		  
		  
      else
		  NUMATS=`zcat ${RULES_FILE}.${ITERATION}.upper.gz ${RULES_FILE}.${ITERATION}.lower.gz | head -n -1 | wc -l `
		  zcat ${RULES_FILE}.${ITERATION}.upper.gz | head -n -1 | gzip | zcat - ${RULES_FILE}.${ITERATION}.lower.gz | { 
		  CURAT=$NUMATS
		  while read line
		  do 
			  echo "$CURAT | $line"
			  CURAT=`expr $CURAT - 1`
		  done }  > $MYDIR/queries/$ITERATION/experiment/alignmentTemplatesGeneralisedResult.txt	
      fi
      
      AT=`zcat ${RULES_FILE}.${ITERATION}.upper.gz | tail -n 1`
      
      
      if $USE_CORPUS ; then
		ITERATIONSDIRS="$ITERATION ${ITERATION}-ref"
      else
        ITERATIONSDIRS="$ITERATION"
      fi
      
      PREVITERATION=`expr $ITERATION - 1 `
      for ITERATIONVAR in $ITERATIONSDIRS ; do
      	  
      	  ITERATIONVARCONTAINSREF=`echo "$ITERATIONVAR" | grep "-ref" | wc -l`
      	  
      	  if [ "$USE_CORPUS" == "false" -o  "$ITERATIONVAR" == "1-ref" -o "$ITERATIONVARCONTAINSREF" == "0" ] ; then
      	  
			  #create apertium rules
			  #no uso variables
			  
			  
			  EXPQUERIESDIR=$MYDIR/queries/$ITERATIONVAR/experiment/
			  TAGGROUPS=$CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX
			  mkdir -p $EXPQUERIESDIR/rules
			  
			  cp $EXPQUERIESDIR/alignmentTemplatesGeneralisedResult.txt $EXPQUERIESDIR/alignmentTemplatesGeneralised.txt
			  #sort ATs to be processed by the module which encodes them as Apertium rules
			  cat $EXPQUERIESDIR/alignmentTemplatesGeneralised.txt | ${PYTHONHOME}python $CURDIR/addGeneralisedLeftSide.py | LC_ALL=C sort -r | ${PYTHONHOME}python $CURDIR/uniqSum.py | awk -F"|" '{print $2"|"$1"|"$3"|"$4"|"$5"|"$6}' | sed 's_^ __' | sed 's_|\([0-9]\)_| \1_' |  LC_ALL=C sort -r | ${PYTHONHOME}python $CURDIR/removeExplicitEmptuTagsFromPatternTLandRest.py | awk -F"|" '{print $2"|"$3"|"$4"|"$5"|"$6}' | sed 's_^ __' > $EXPQUERIESDIR/rules/alignmentTemplates.txt
			  cat $EXPQUERIESDIR/rules/alignmentTemplates.txt | cut -f 1 -d '|' | uniq > $EXPQUERIESDIR/rules/alignmentTemplates.txt.patterns

			  #create Apertium rules. NO VARS
			  TMPFILE1=`mktemp`
			  TMPFILE2=`mktemp`
			  echo "${TRANSFERTOOLSPATH}apertium-gen-transfer-from-aligment-templates --input $EXPQUERIESDIR/rules/alignmentTemplates.txt --attributes $TAGGROUPS --generalise --nodoublecheckrestrictions --usediscardrule --novarsdetermined $RICHATSFLAG 2> $TMPFILE2 | ${PYTHONHOME}python $CURDIR/addDebugInfoToTransferRules.py > $EXPQUERIESDIR/rules/rules.xml" > $TMPFILE1
			  bash $TMPFILE1
			  rm $TMPFILE1
			  #output log
			  cat $TMPFILE2
			  rm $TMPFILE2

			  #compile rules
			  ${APERTIUMPATH}apertium-preprocess-transfer $EXPQUERIESDIR/rules/rules.xml $EXPQUERIESDIR/rules/rules.bin
			  
			
			  MODEDIR="$MYDIR/queries/$ITERATIONVAR/experiment/modes"
			  mkdir -p $MODEDIR
			  
			  #create mode with learned rules
			  bash $CURDIR/createModeWithLearnedRules.sh  $APERTIUM_PREFIX/share/apertium/modes/${SL}-${TL}.mode  "$TRANSFERTOOLSPATH" "$MYDIR/queries/$ITERATIONVAR/experiment/rules/rules" blabla $BILDICTIONARY  "" "" > $MODEDIR/${SL}-${TL}_nonworking.mode
			  
			  MODEFILE="${SL}-${TL}_nonworking.mode"
			  MODEFILELONG="$MODEDIR/$MODEFILE"
			  LEXICALMODEFILE="lexical-$MODEFILE"
			  LEXICALMODE="${LEXICALMODEFILE%%.mode}"
			  cat $MODEFILELONG | awk -F"apertium-pretransfer" '{print $2}' | sed 's_^[^|]*|__' | awk -F" sed 's_" '{print $1}' | sed 's_|[^|]*$__' > $MODEDIR/$LEXICALMODEFILE

		  fi
      	  
		  if $USE_CORPUS ; then
			
			
			if [ "$ITERATIONVAR" == "1-ref" -o "$ITERATIONVARCONTAINSREF" == "0" ] ; then
			
			 #translate bilingual corpus
			 mkdir -p $MYDIR/translations_${ITERATION}
			 zcat  $ANALYSED_PARALLEL_CORPUS.${SL}.gz | sed 's_$_^.<sent>$_' | sed 's:_: :g' | PATH=$PATH:$APERTIUMPATH bash $CURDIR/translate_apertium.sh "" $LEXICALMODE join "none" "$MYDIR/queries/$ITERATIONVAR/experiment" | ${APERTIUMPATH}apertium-pretransfer | sed 's_\^\*executedtule[0-9]*\$__g' | sed 's_\^\*isolatedword\$__g' | sed 's_\^.<sent>\$ *$__' |  sed -r 's_^ *\^_^_' | sed -r 's_\$ *\^_$^_g' | sed -r 's_ *$__' | sed 's: :_:' | sed 's_$^_$ ^_g'  > $MYDIR/translations_${ITERATION}/translation.${ITERATIONVAR}	 
			 #the sequence of seds removes initial and final spaces, ensures that there is  a single space between words and that multiwords contain _
			 
			 #compute WER
			 perl $CURDIR/calc-wer.pl -t $MYDIR/translations_${ITERATION}/translation.${ITERATIONVAR} -r $MYDIR/referenceCorpus.${TL} |  grep "WER" | sed 's_^[^:]*: __' | sed 's_ %__' | sed 's_,_._' > $MYDIR/translations_${ITERATION}/wer.${ITERATIONVAR}
			 
			else
			 #If we are here, ITERATIONVAR contains -ref
			 cp $MYDIR/translations_$PREVITERATION/translation.best $MYDIR/translations_${ITERATION}/translation.${ITERATIONVAR}
			 cp $MYDIR/translations_$PREVITERATION/wer.best $MYDIR/translations_${ITERATION}/wer.${ITERATIONVAR}
			fi
			 
		  else
		  
			  #Get bilphrases
			  zcat $BILPHRASES_DIR/$BOXNUMBER$DEBUGINFOFILESUFFIX | tac | sed -e '/^BILINGUAL_PHRASES$/,$d' | tac | sed -e '/^END_BILINGUAL_PHRASES$/,$d' | ${PYTHONHOME}python $CURDIR/filterBilphrasesMatchingAT.py --tag_groups_file_name $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --alignment_template "$AT" $RICHATSFLAG | cut -f 1,2,3,4 -d '|' | sed 's:<empty_tag_[^>]*>::g' | sed -r 's_> ([^|])_>$ ^\1_g' |  sed -r 's_> [|]_>$ |_g' | sed -r 's_[|] ([^^])_| ^\1_' |  sed -r 's_[|] ([^^])_| ^\1_' | gzip > $MYDIR/bilingualPhrases.${ITERATION}.gz
			  
			  #Translate bilphrases and check..
			  mkdir -p $MYDIR/translations_${ITERATION}
			  zcat $MYDIR/bilingualPhrases.${ITERATION}.gz | cut -f 1,2 -d '|' | sed 's_^_[_' | sed 's_ | _] _' | sed 's:_: :g'  > $MYDIR/translations_${ITERATION}/test.source
			  zcat $MYDIR/bilingualPhrases.${ITERATION}.gz | cut -f 1,3 -d '|' | sed 's_^_[_' | sed 's_ | _] _' | sed 's:_: :g'  > $MYDIR/translations_${ITERATION}/test.reference
			  
			  #translate
			  cat  $MYDIR/translations_${ITERATION}/test.source | sed 's_$_^.<sent>$_' | PATH=$PATH:$APERTIUMPATH bash $CURDIR/translate_apertium.sh "" $LEXICALMODE join "none" "$MYDIR/queries/$ITERATIONVAR/experiment" | ${APERTIUMPATH}apertium-pretransfer  > $MYDIR/translations_${ITERATION}/test.translation.raw
			  cat $MYDIR/translations_${ITERATION}/test.translation.raw | sed 's_\^\*executedtule[0-9]*\$__g' | sed 's_\^\*isolatedword\$__g' | sed 's_\^.<sent>\$ *$__' > $MYDIR/translations_${ITERATION}/test.translation
			  cat $MYDIR/translations_${ITERATION}/test.translation.raw | sed 's:$:VMSANCHEZNEWLINEMARK:'  |  grep -Eo 'VMSANCHEZNEWLINEMARK|\^\*executedtule[0-9]*\$|\^\*isolatedword\$' | sed 's:\^\*isolatedword\$:-1:g' | sed 's:\^\*executedtule\([0-9]*\)\$:\1:g'  | tr '\n' ' ' | sed 's:VMSANCHEZNEWLINEMARK:\n:g' > $MYDIR/translations_${ITERATION}/test.translation.appliedrules
			  
			  #Evaluate	
			  echo "Running diff"
			  #normalise whitespaces before comparing
			  cat $MYDIR/translations_${ITERATION}/test.reference | sed 's:^ *::' | sed 's: *$::' | sed 's:\$ *\^:$ ^:g' > $MYDIR/translations_${ITERATION}/test.reference.normalised
			  cat $MYDIR/translations_${ITERATION}/test.translation | sed 's:^ *::' | sed 's: *$::' | sed 's:\$ *\^:$ ^:g' > $MYDIR/translations_${ITERATION}/test.translation.normalised
			  diff -i $MYDIR/translations_${ITERATION}/test.reference.normalised $MYDIR/translations_${ITERATION}/test.translation.normalised > $MYDIR/translations_${ITERATION}/test.diff  
		  fi
	  done
	
	if [ ! $KEEPTMPDIRS ]; then
	  rm -Rf $MYDIR/translations_$PREVITERATION/
	fi
		      
      CANREMOVE="yes"
      
      if $USE_CORPUS ; then      
		  WER_WITHOUT_RULE=`cat $MYDIR/translations_${ITERATION}/wer.${ITERATION}`
		  WER_WITH_RULE=`cat $MYDIR/translations_${ITERATION}/wer.${ITERATION}-ref`
		  
		  if [ "`echo "$WER_WITHOUT_RULE > $WER_WITH_RULE" | bc -l`" == "1" ]; then
			 CANREMOVE="no"
			 ln -s ./translation.${ITERATION}-ref  $MYDIR/translations_${ITERATION}/translation.best
			 ln -s ./wer.${ITERATION}-ref $MYDIR/translations_${ITERATION}/wer.best
		  else
			 ln -s ./translation.${ITERATION}  $MYDIR/translations_${ITERATION}/translation.best
			 ln -s ./wer.${ITERATION} $MYDIR/translations_${ITERATION}/wer.best
		  fi
		  
		  #some debug information
		  diff $MYDIR/translations_${ITERATION}/translation.${ITERATION}-ref $MYDIR/translations_${ITERATION}/translation.${ITERATION} >> $MYDIR/summary.debug.inverse
		  echo "Output diff ( < with; > without ) :" >> $MYDIR/summary.debug.inverse
		  echo "WER change (with -> without): $WER_WITH_RULE -> $WER_WITHOUT_RULE" >> $MYDIR/summary.debug.inverse
		  echo "Removing AT: $AT" >> $MYDIR/summary.debug.inverse
		  echo "$AT : $WER_WITH_RULE -> $WER_WITHOUT_RULE" >> $MYDIR/summary.inverse
		  
	  else
		  if [ -s $MYDIR/translations_${ITERATION}/test.diff ] ; then
			  CANREMOVE="no"
		  fi
		  
		  #Compute proportion of the total bilingual phrases which are incorrectly translated
		  TOTAL_BILPHRASES=`zcat $MYDIR/bilingualPhrases.${ITERATION}.gz | awk -F'|' '{s+=$1} END {print s}'`
		  INCORRECTLY_TRANSLATED=`cat $MYDIR/translations_${ITERATION}/test.diff | grep  "^<" | awk -F'[' '{print $2}' | awk -F']' '{s+=$1} END {print s}' | sed 's_^$_0_'`
		  PROPINCORRECT=`echo "$INCORRECTLY_TRANSLATED / $TOTAL_BILPHRASES" | bc -l`
		  echo "$PROPINCORRECT | $AT" >> $MYDIR/summary.inverse
		  cat $MYDIR/translations_${ITERATION}/test.diff >> $MYDIR/summary.debug.inverse
		  echo "Wrongly translated: " >> $MYDIR/summary.debug.inverse
		  #paste -d '|' $MYDIR/translations_${ITERATION}/test.source $MYDIR/translations_${ITERATION}/test.reference >> $MYDIR/summary.debug.inverse
		  paste -d '|' $MYDIR/translations_${ITERATION}/test.source $MYDIR/translations_${ITERATION}/test.reference $MYDIR/translations_${ITERATION}/test.translation.appliedrules | while read myline ; do
		    rm -f $MYDIR/translations_${ITERATION}/rulesApplied
		    FIRSTFIELD=`echo "$myline" | cut -f 1 -d '|'`
		    if [ "$FIRSTFIELD" != "" ]; then
		      RULESID=`echo "$myline" | cut -f3 -d '|'`
		      index=0
		      for RULEID in $RULESID ; do
			  if [ "$RULEID" != "-1" ]; then
			    cat $MYDIR/queries/$ITERATIONVAR/experiment/rules/alignmentTemplates.txt | head -n $RULEID | tail -n 1 | sed 's:^:\t:' >> $MYDIR/translations_${ITERATION}/rulesApplied
			  else
			    echo  "	WORDFORWORD" >> $MYDIR/translations_${ITERATION}/rulesApplied
			  fi
		      done
		      cat $MYDIR/translations_${ITERATION}/rulesApplied | tac >> $MYDIR/summary.debug.inverse
		      echo "$myline" | cut -f1,2 -d '|' >> $MYDIR/summary.debug.inverse
		    fi
		  done
		  
		  echo "BILPHRASES FOR AT: $AT" >> $MYDIR/summary.debug.inverse
	  fi    
      
      NEWITERATION=`expr $ITERATION + 1`
      
      zcat ${RULES_FILE}.${ITERATION}.upper.gz | head -n -1 | gzip > ${RULES_FILE}.${NEWITERATION}.upper.gz
      if [ "$CANREMOVE" == "yes" ]; then
	      cp ${RULES_FILE}.${ITERATION}.lower.gz ${RULES_FILE}.${NEWITERATION}.lower.gz
      else
	      zcat ${RULES_FILE}.${ITERATION}.upper.gz | tail -n 1 | gzip | zcat - ${RULES_FILE}.${ITERATION}.lower.gz | gzip > ${RULES_FILE}.${NEWITERATION}.lower.gz
      fi
      
      ITERATION=$NEWITERATION
      LINE=`zcat ${RULES_FILE}.${ITERATION}.upper.gz | wc -l`
      
done


tac < $MYDIR/summary.inverse | gzip > $MYDIR/summary.gz
tac < $MYDIR/summary.debug.inverse | gzip > $MYDIR/summary.debug.gz

ln -s ./`basename ${RULES_FILE}.${ITERATION}.lower.gz` ${RULES_FILE}.reduced.gz
