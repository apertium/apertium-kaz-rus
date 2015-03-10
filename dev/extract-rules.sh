#! /bin/bash

MYFULLPATH=`readlink -f $0`
CURDIR=`dirname $MYFULLPATH`

#shflags
. $CURDIR/rule-generalisation/shflags

DEFINE_string 'source_language' 'es' 'source language language' 's'
DEFINE_string 'target_language' 'ca' 'target language' 't'
DEFINE_string 'corpus' '' 'prefix of files containing parallel corpus (suffixes are .SL and .TL)' 'c'
DEFINE_string 'giza_dir' '~/giza-pp/GIZA++-v2' 'Giza++ directory' 'g'
DEFINE_string 'data_dir' '' 'Directory where the source and compiled Apertium dictionaries can be found (default: /usr/local/share/apertium/apertium-SL-TL/)' 'd'
DEFINE_string 'apertium_prefix' '' 'Prefix where Apertium was installed (default: /usr/local/)' 'u'
######################
# (optional)
# Temporary directory where all the the files will be stored
# If not set, the script will create a new temporary directory under /tmp
######################
DEFINE_string 'tmp_dir' '' 'temporary directory' 'm'
DEFINE_boolean 'segment_by_marker' 'false' 'Segment SL corpus according to marker hypothesis' 'y'
DEFINE_string 'filtering_thresholds' '0 0.05 1' 'Thresholds for filtering alignment templates. Format is start step end, as in the seq command. A single threshold can also be defined' 'f'
DEFINE_string 'theta_threshold' '2' 'Number of bilphrases a GAT must reproduce' 'w'
DEFINE_string 'test_corpus' '' 'evaluation corpus prefix (suffixes are .SL and .TL)' 'e'
DEFINE_string 'dev_corpus' '' 'development corpus prefix (suffixes are .SL and .TL). It is used to choose the most appropriate threshold' 'v'

DEFINE_boolean 'transfer_tools_1' 'false' 'Use transfer tools 1.0' 'o'
DEFINE_boolean 'only_extract_bilingual_phrases' 'false' 'only extract bilingual phrases' 'x'

DEFINE_string 'corpus_head_size' '' 'size (in lines) of the prefix of the corpus to use' 'a'
DEFINE_boolean 'corpus_is_already_analysed' 'false' 'corpus is already analysed' 'n'
DEFINE_string 'inverse_analysed_corpus' '' 'inverse analysed corpus file' 'i'
DEFINE_boolean 'zens_extraction' 'false' 'use zens algorithm to extract bilingual phrases' 'z'
#DEFINE_boolean 'disable_struct_edges' 'false' 'disable struct edges when phrase extraction (deprecated)' 'u'
DEFINE_string 'variant' '' 'variant' 'r'
DEFINE_string 'extremes_variant' 'antiphrases' 'extremes variant' 'k'
DEFINE_boolean 'use_fixed_dictionary' 'false' 'use fixed bilingual dictionary' 'l'
DEFINE_boolean 'alignments_with_lemmas' 'false' 'use only lemms to learn alignment models and obtain Viterbi alignment' 'p'
DEFINE_boolean 'alignments_with_bildic' 'false' 'add bilingual dictionary to corpus for obtaining alignments' 'j'

DEFINE_boolean 'discard_a_fifth_of_corpus' 'false' 'discard a fifth part of the training corpus. It will be used for tuning' 'b'

DEFINE_boolean 'only_lexical_generalisation' 'false' 'dont generalise among unseen linguistic features' 'q'


#process parameters
FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

VARIANT=${FLAGS_variant}
EXTREMESVARIANT=${FLAGS_extremes_variant}

if [ "${FLAGS_tmp_dir}" == "" ]; then
	TMPDIR=`mktemp -d`
else
	TMPDIR=${FLAGS_tmp_dir}
	mkdir -p $TMPDIR
fi

MAX_LENGTH=5

SL=${FLAGS_source_language}
TL=${FLAGS_target_language}
PAIR="${SL}-${TL}"

CORPUS=${FLAGS_corpus}
CORPUS_INVERSE=${FLAGS_inverse_analysed_corpus}
GIZADIR=${FLAGS_giza_dir}
FULLRULELEARNINGDIR=`readlink -f $CURDIR/rule-generalisation`

THETA=${FLAGS_theta_threshold}

HEADCOMMAND="cat -"
if [ "${FLAGS_corpus_head_size}" != "" ]; then
  HEADCOMMAND="head -n ${FLAGS_corpus_head_size}"
fi

STRUCTMAKVAR="PAR_SAME_STRUCTURE=yes"
if [ "${FLAGS_disable_struct_edges}" == "${FLAGS_TRUE}" ]; then
  STRUCTMAKVAR=""
fi

CORPUSANALYSEDMAKVAR=""
if [ "${FLAGS_corpus_is_already_analysed}" == "${FLAGS_TRUE}" ]; then
  CORPUSANALYSEDMAKVAR="PAR_PROVIDED_ANALYSED_CORPUS=yes"
fi

LEMMATIZEDMAKVAR=""
if [ "${FLAGS_alignments_with_lemmas}" == "${FLAGS_TRUE}" ]; then
  LEMMATIZEDMAKVAR="PAR_GIZA_LEMMA=yes"
fi

ZENSMAKVAR=""
if [ "${FLAGS_zens_extraction}" == "${FLAGS_TRUE}" ]; then
  ZENSMAKVAR="PAR_EXTRACTION_ZENS=yes"
fi

if [ "${FLAGS_data_dir}" == "" ]; then
  DATADIR="/usr/local/share/apertium/apertium-$SL-$TL/"
else
  DATADIR="${FLAGS_data_dir}"
fi

APERTIUMPREFIX=${FLAGS_apertium_prefix}

FIXEDDICTMAKVAR=""
if [ "${FLAGS_use_fixed_dictionary}" == "${FLAGS_TRUE}" ]; then
  FIXEDDICTMAKVAR="PAR_FIXED_DICT=yes"
fi

ONLYLEXGENFLAG=""
if [ "${FLAGS_only_lexical_generalisation}" == "${FLAGS_TRUE}" ]; then
	ONLYLEXGENFLAG="-7"
fi

CANDIDATE2=""

BILDIXFORALIGNMAKVAR=""
BILDIXMAKVAR=""

if [ "${FLAGS_alignments_with_bildic}" == "${FLAGS_TRUE}" ]; then
	BILDIXFORALIGNMAKVAR="PAR_BILDIXFORALIGN=yes"
fi
  #try to find bilingual dictionary .dix file
  CANDIDATE1="$DATADIR/.deps/${SL}-${TL}.dix"
  if [ -f "$CANDIDATE1" ]; then
	BILDIXMAKVAR="PAR_BILDIX=$CANDIDATE1"
  else
	CANDIDATE2=`mktemp`
	xsltproc  $DATADIR/translate-to-default-equivalent.xsl $DATADIR/apertium-${SL}-${TL}.${SL}-${TL}.dix > $CANDIDATE2
	BILDIXMAKVAR="PAR_BILDIX=$CANDIDATE2"
  fi

 
#find monolingual .dix files
if [ -f $DATADIR/.deps/$SL.dix ] ; then
	MONODIXL1=$DATADIR/.deps/$SL.dix
elif [ -f $DATADIR/apertium-${SL}-${TL}.$SL.dix ]; then
	MONODIXL1=$DATADIR/apertium-${SL}-${TL}.$SL.dix
elif [ -f $DATADIR/apertium-${SL}-${TL}.$SL.dix ]; then
	MONODIXL1=$DATADIR/apertium-${SL}-${TL}.$SL.dixtmp1
else
	echo "MOnodix l1 not found"
	exit
fi



#find monolingual .dix files
if [ -f $DATADIR/.deps/$TL.dix ] ; then
	MONODIXL2=$DATADIR/.deps/$TL.dix
elif [ -f $DATADIR/apertium-${SL}-${TL}.$TL.dix ]; then
	MONODIXL2=$DATADIR/apertium-${SL}-${TL}.$TL.dix
elif [ -f $DATADIR/apertium-${SL}-${TL}.$TL.dixtmp1 ]; then
	MONODIXL2=$DATADIR/apertium-${SL}-${TL}.$TL.dixtmp1
else
	echo "MOnodix l2 not found"
	exit
fi

MONODIXL1MAKVAR="PAR_MONODIXL1=$MONODIXL1"
MONODIXL2MAKVAR="PAR_MONODIXL2=$MONODIXL2"

TEST_CORPUS=${FLAGS_test_corpus}
DEV_CORPUS=${FLAGS_dev_corpus}

echo "Temporary directory: $TMPDIR" 1>&2
echo "Checking whether 'lt-proc' is in the PATH: " 1>&2
which lt-proc
if [ "$?" != "0" ]; then
  echo "ERROR: not found" 1>&2
else
  echo "OK" 1>&2
fi

echo "Checking whether 'apertium-symmetrize-alignments' is in the PATH: " 1>&2
which apertium-symmetrize-alignments
if [ "$?" != "0" ]; then
  echo "ERROR: not found" 1>&2
else
  echo "OK" 1>&2
fi

echo "Checking whether needed GIZA++ executables are found in GIZA++ dir: " 1>&2
for myfile in plain2snt.out snt2plain.out "../mkcls-v2/mkcls" GIZA++ ; do
  if [ -e "$GIZADIR/$myfile" ]; then
    echo "$myfile OK" 1>&2
  else
    echo "ERROR: $myfile not found" 1>&2
  fi
done

ALIGNMENTSHEADMAKVAR=""
if [ "${FLAGS_discard_a_fifth_of_corpus}" == "${FLAGS_TRUE}" ]; then
	CORPUSLENGTH=`cat $CORPUS.$SL | $HEADCOMMAND | wc -l`
	PORTIONTODISCARD=`expr $CORPUSLENGTH / 5`
	PORTIONTOKEEP=`expr $CORPUSLENGTH - $PORTIONTODISCARD`
	ALIGNMENTSHEADMAKVAR="PAR_ALIGNMENTS_HEAD=$PORTIONTOKEEP"
elif [ "${FLAGS_alignments_with_bildic}" == "${FLAGS_TRUE}"  ]; then
	CORPUSLENGTH=`cat $CORPUS.$SL | $HEADCOMMAND | wc -l`
	ALIGNMENTSHEADMAKVAR="PAR_ALIGNMENTS_HEAD=$CORPUSLENGTH"
fi


if [ "${FLAGS_transfer_tools_1}" == "${FLAGS_TRUE}" ]; then

  #transfer tools 1.0 stuff
  
  #run dev experiments
  HIGHESTTHRESHOLD=9
  for treshold in `seq $HIGHESTTHRESHOLD -1 2`; do
	  if [ ! -d "$TMPDIR/dev-${treshold}-count" ]; then
		  mkdir -p $TMPDIR/dev-${treshold}-count
		  pushd $CURDIR/phrase-extraction/transfer-tools-scripts
			  bash linkToWorkDir.sh $TMPDIR/dev-${treshold}-count
		  popd
		  pushd $TMPDIR/dev-${treshold}-count
		  	 
		  	 PROVIDEDALIGNMENTSMAKVAR=""
		  	 
		  	 if [ "$treshold" != "$HIGHESTTHRESHOLD" ]; then
		  	 	PROVIDEDALIGNMENTSMAKVAR="PAR_PROVIDED_ALIGNMENTS=yes"
		  	 	cp ../dev-${HIGHESTTHRESHOLD}-count/alignments.${SL}-${TL}.gz ./
		  	 	cp ../dev-${HIGHESTTHRESHOLD}-count/alignments.${TL}-${SL}.gz ./
		  	 fi
		  
			  #get corpus
			  if [ "${FLAGS_corpus_is_already_analysed}" == "${FLAGS_TRUE}" ]; then
			    mkdir -p train-giza++-${SL}-${TL}
			    mkdir -p train-giza++-${TL}-${SL}
		    
			    cat $CORPUS.$SL | $HEADCOMMAND  > train-giza++-${SL}-${TL}/$SL.${SL}-${TL}.pos.txt
			    cat $CORPUS.$TL | $HEADCOMMAND  > train-giza++-${SL}-${TL}/$TL.${SL}-${TL}.pos.txt
		    
			    cat $CORPUS_INVERSE.$SL | $HEADCOMMAND  > train-giza++-${TL}-${SL}/$SL.${TL}-${SL}.pos.txt
			    cat $CORPUS_INVERSE.$TL | $HEADCOMMAND  > train-giza++-${TL}-${SL}/$TL.${TL}-${SL}.pos.txt
			  else
			    cat $CORPUS.$SL | $HEADCOMMAND | gzip > $SL.txt.gz
			    cat $CORPUS.$TL | $HEADCOMMAND | gzip > $TL.txt.gz
			    
			    if [ "$PORTIONTODISCARD" != "" ]; then
				zcat $SL.txt.gz | tail -n $PORTIONTODISCARD > devcorpus.${FLAGS_corpus_head_size}.$SL
				zcat $TL.txt.gz | tail -n $PORTIONTODISCARD > devcorpus.${FLAGS_corpus_head_size}.$TL
				
				DEV_CORPUS=`readlink -f devcorpus.${FLAGS_corpus_head_size}.$SL | sed "s:.$SL\$::"`
			    fi
			  fi
			  make PAR_NO_SHORT_RESTRICTIONS=yes PAR_TH_COUNT=$treshold PAR_ONLY_STANDARD=yes PAR_TESTCORPUS=$DEV_CORPUS PAR_L1=$SL PAR_L2=$TL PAR_CRITERION=count PAR_MAX=$MAX_LENGTH PAR_DISCARD_RULE=yes PAR_RULELEARNINGLIBDIR="$FULLRULELEARNINGDIR" PAR_GIZADIR="$GIZADIR"   $CORPUSANALYSEDMAKVAR $ZENSMAKVAR  $FIXEDDICTMAKVAR $LEMMATIZEDMAKVAR $ALIGNMENTSHEADMAKVAR $BILDIXMAKVAR $BILDIXFORALIGNMAKVAR $MONODIXL1MAKVAR $MONODIXL2MAKVAR $PROVIDEDALIGNMENTSMAKVAR 2>&1 > $TMPDIR/dev-${treshold}-count-debug
		  popd
	  fi
  done
  

  #get results
  rm -f $TMPDIR/tuning_data
  rm -f $TMPDIR/tuning_data_inv
  for treshold in `seq 9 -1 2`; do
	  cat $TMPDIR/dev-${treshold}-count/evaluation.${SL}-${TL} | grep "^NIST" | cut -f 9 -d ' ' | sed "s_^_$treshold\t_" >> $TMPDIR/tuning_data
	  cat $TMPDIR/dev-${treshold}-count/evaluation.${TL}-${SL} | grep "^NIST" | cut -f 9 -d ' ' | sed "s_^_$treshold\t_" >> $TMPDIR/tuning_data_inv
  done
  #choose best threshold
  BEST_TRESHOLD=`cat $TMPDIR/tuning_data | sort -r  -k2,2 | head -n 1 | cut -f 1`
  BEST_TRESHOLD_INV=`cat $TMPDIR/tuning_data_inv | sort -r  -k2,2 | head -n 1 | cut -f 1`

  if [ ! -d "$TMPDIR/test-${BEST_TRESHOLD}-count" ]; then
	  echo "translating test corpus with the best threshold"
	  mkdir -p $TMPDIR/test-${BEST_TRESHOLD}-count
	  pushd $CURDIR/phrase-extraction/transfer-tools-scripts
		  bash linkToWorkDir.sh $TMPDIR/test-${BEST_TRESHOLD}-count
	  popd
	  pushd $TMPDIR/test-${BEST_TRESHOLD}-count
	  	
	  	PROVIDEDALIGNMENTSMAKVAR="PAR_PROVIDED_ALIGNMENTS=yes"
		cp ../dev-${HIGHESTTHRESHOLD}-count/alignments.${SL}-${TL}.gz ./
		cp ../dev-${HIGHESTTHRESHOLD}-count/alignments.${TL}-${SL}.gz ./
	  	
		  #get corpus
		  if [ "${FLAGS_corpus_is_already_analysed}" == "${FLAGS_TRUE}" ]; then
		    mkdir -p train-giza++-${SL}-${TL}
		    mkdir -p train-giza++-${TL}-${SL}
		    
		    cat $CORPUS.$SL | $HEADCOMMAND  > train-giza++-${SL}-${TL}/$SL.${SL}-${TL}.pos.txt
		    cat $CORPUS.$TL | $HEADCOMMAND  > train-giza++-${SL}-${TL}/$TL.${SL}-${TL}.pos.txt
		    
		    cat $CORPUS_INVERSE.$SL | $HEADCOMMAND  > train-giza++-${TL}-${SL}/$SL.${TL}-${SL}.pos.txt
		    cat $CORPUS_INVERSE.$TL | $HEADCOMMAND  > train-giza++-${TL}-${SL}/$TL.${TL}-${SL}.pos.txt
		  else
		    cat $CORPUS.$SL | $HEADCOMMAND | gzip > $SL.txt.gz
		    cat $CORPUS.$TL | $HEADCOMMAND | gzip > $TL.txt.gz
		    
		    if [ "$PORTIONTODISCARD" != "" ]; then
			zcat $SL.txt.gz | tail -n $PORTIONTODISCARD > devcorpus.${FLAGS_corpus_head_size}.$SL
			zcat $TL.txt.gz | tail -n $PORTIONTODISCARD > devcorpus.${FLAGS_corpus_head_size}.$TL
		    fi
		    
		  fi
		  make PAR_NO_SHORT_RESTRICTIONS=yes PAR_TH_COUNT=${BEST_TRESHOLD} PAR_ONLY_STANDARD=yes PAR_TESTCORPUS=$TEST_CORPUS PAR_L1=$SL PAR_L2=$TL PAR_CRITERION=count PAR_MAX=$MAX_LENGTH PAR_DISCARD_RULE=yes PAR_RULELEARNINGLIBDIR="$FULLRULELEARNINGDIR" PAR_GIZADIR="$GIZADIR" $CORPUSANALYSEDMAKVAR $ZENSMAKVAR $FIXEDDICTMAKVAR $ALIGNMENTSHEADMAKVAR $BILDIXMAKVAR $BILDIXFORALIGNMAKVAR $PROVIDEDALIGNMENTSMAKVAR 2>&1 > $TMPDIR/test-${BEST_TRESHOLD}-count-debug
	  popd
  fi

  if [ ! -d "$TMPDIR/test-${BEST_TRESHOLD_INV}-count" ]; then
	  echo "translating test corpus with the best threshold inv"
	  mkdir -p $TMPDIR/test-${BEST_TRESHOLD_INV}-count
	  pushd $CURDIR/phrase-extraction/transfer-tools-scripts
		  bash linkToWorkDir.sh $TMPDIR/test-${BEST_TRESHOLD_INV}-count
	  popd
	  pushd $TMPDIR/test-${BEST_TRESHOLD_INV}-count
	  	  
	  	 PROVIDEDALIGNMENTSMAKVAR="PAR_PROVIDED_ALIGNMENTS=yes"
		 cp ../dev-${HIGHESTTHRESHOLD}-count/alignments.${SL}-${TL}.gz ./
		 cp ../dev-${HIGHESTTHRESHOLD}-count/alignments.${TL}-${SL}.gz ./
	  	  
		  #get corpus
		  if [ "${FLAGS_corpus_is_already_analysed}" == "${FLAGS_TRUE}" ]; then
		    mkdir -p train-giza++-${SL}-${TL}
		    mkdir -p train-giza++-${TL}-${SL}
		    
		    cat $CORPUS.$SL | $HEADCOMMAND  > train-giza++-${SL}-${TL}/$SL.${SL}-${TL}.pos.txt
		    cat $CORPUS.$TL | $HEADCOMMAND  > train-giza++-${SL}-${TL}/$TL.${SL}-${TL}.pos.txt
		    
		    cat $CORPUS_INVERSE.$SL | $HEADCOMMAND  > train-giza++-${TL}-${SL}/$SL.${TL}-${SL}.pos.txt
		    cat $CORPUS_INVERSE.$TL | $HEADCOMMAND  > train-giza++-${TL}-${SL}/$TL.${TL}-${SL}.pos.txt
		  else
		    cat $CORPUS.$SL | $HEADCOMMAND | gzip > $SL.txt.gz
		    cat $CORPUS.$TL | $HEADCOMMAND | gzip > $TL.txt.gz
		    
		    if [ "$PORTIONTODISCARD" != "" ]; then
			zcat $SL.txt.gz | tail -n $PORTIONTODISCARD > devcorpus.${FLAGS_corpus_head_size}.$SL
			zcat $TL.txt.gz | tail -n $PORTIONTODISCARD > devcorpus.${FLAGS_corpus_head_size}.$TL
		    fi
		  fi
		  make PAR_NO_SHORT_RESTRICTIONS=yes PAR_TH_COUNT=${BEST_TRESHOLD_INV} PAR_ONLY_STANDARD=yes PAR_TESTCORPUS=$TEST_CORPUS PAR_L1=$SL PAR_L2=$TL PAR_CRITERION=count PAR_MAX=$MAX_LENGTH PAR_DISCARD_RULE=yes PAR_RULELEARNINGLIBDIR="$FULLRULELEARNINGDIR" PAR_GIZADIR="$GIZADIR" $CORPUSANALYSEDMAKVAR $ZENSMAKVAR $LEMMATIZEDMAKVAR $ALIGNMENTSHEADMAKVAR $BILDIXMAKVAR $BILDIXFORALIGNMAKVAR $MONODIXL1MAKVAR $MONODIXL2MAKVAR $PROVIDEDALIGNMENTSMAKVAR 2>&1  >$TMPDIR/test-${BEST_TRESHOLD_INV}-count-debug
	  popd
  fi
  
  RESULT=`cat $TMPDIR/test-${BEST_TRESHOLD}-count/evaluation.${SL}-${TL} | grep "^NIST" | cut -f 9 -d ' ' | sed "s_^_$treshold\t_"`
  RESULT_INV=`cat $TMPDIR/test-${BEST_TRESHOLD_INV}-count/evaluation.${TL}-${SL} | grep "^NIST" | cut -f 9 -d ' ' | sed "s_^_$treshold\t_"`

  NUM_RULES=`wc -l $TMPDIR/test-${BEST_TRESHOLD}-count/alignment-templates-included-in-rules.${SL}-${TL} | cut -f 1 -d ' ' `
  NUM_RULES_INV=`wc -l $TMPDIR/test-${BEST_TRESHOLD}-count/alignment-templates-included-in-rules.${TL}-${SL} | cut -f 1 -d ' ' `

  echo "$RESULT $NUM_RULES $BEST_TRESHOLD" > $TMPDIR/result-${SL}-${TL}
  echo "$RESULT_INV $NUM_RULES_INV $BEST_TRESHOLD_INV" > $TMPDIR/result-${TL}-${SL}

else
  MARKERFLAG=""
  if [ ${FLAGS_segment_by_marker} == ${FLAGS_TRUE} ]; then
  MARKERFLAG="PAR_BILPHRASES_MARKER_SOFT=yes"
  fi

  NUMPARTS=`echo "${FLAGS_filtering_thresholds}" | wc -w`

  if [ "$NUMPARTS" == "1" ]; then
    THRESHOLD_START=${FLAGS_filtering_thresholds}
    THRESHOLD_STEP=1
    THRESHOLD_END=${FLAGS_filtering_thresholds}
  else
    THRESHOLD_START=`echo "${FLAGS_filtering_thresholds}" | cut -f 1 -d ' '`
    THRESHOLD_STEP=`echo "${FLAGS_filtering_thresholds}" | cut -f 2 -d ' '`
    THRESHOLD_END=`echo "${FLAGS_filtering_thresholds}" | cut -f 3 -d ' '`
  fi

  BILEXTRACTIONDIR=$TMPDIR/bilingualphrases

  if [ ! -e $BILEXTRACTIONDIR ]; then

  mkdir -p $BILEXTRACTIONDIR
  BILEXTRACTIONDIRFULL=`readlink -f $BILEXTRACTIONDIR`

  pushd $CURDIR/phrase-extraction/transfer-tools-scripts
  bash linkToWorkDir.sh $BILEXTRACTIONDIRFULL
  popd

  #get corpus
  if [ "${FLAGS_corpus_is_already_analysed}" == "${FLAGS_TRUE}" ]; then
    mkdir -p $BILEXTRACTIONDIR/train-giza++-${SL}-${TL}
    mkdir -p $BILEXTRACTIONDIR/train-giza++-${TL}-${SL}
    
    cat $CORPUS.$SL | $HEADCOMMAND  > $BILEXTRACTIONDIR/train-giza++-${SL}-${TL}/$SL.${SL}-${TL}.pos.txt
    cat $CORPUS.$TL | $HEADCOMMAND  > $BILEXTRACTIONDIR/train-giza++-${SL}-${TL}/$TL.${SL}-${TL}.pos.txt
    
    cat $CORPUS_INVERSE.$SL | $HEADCOMMAND  > $BILEXTRACTIONDIR/train-giza++-${TL}-${SL}/$SL.${TL}-${SL}.pos.txt
    cat $CORPUS_INVERSE.$TL | $HEADCOMMAND  > $BILEXTRACTIONDIR/train-giza++-${TL}-${SL}/$TL.${TL}-${SL}.pos.txt
    
    if [ "$PORTIONTODISCARD" != "" ]; then
	cat $DEV_CORPUS.$SL > $BILEXTRACTIONDIR/devcorpus.${FLAGS_corpus_head_size}.$SL
	cat $DEV_CORPUS.$TL > $BILEXTRACTIONDIR/devcorpus.${FLAGS_corpus_head_size}.$TL
    fi
    
  else
    cat $CORPUS.$SL | $HEADCOMMAND | gzip > $BILEXTRACTIONDIR/$SL.txt.gz
    cat $CORPUS.$TL | $HEADCOMMAND | gzip > $BILEXTRACTIONDIR/$TL.txt.gz
    
    if [ "$PORTIONTODISCARD" != "" ]; then
	zcat $BILEXTRACTIONDIR/$SL.txt.gz | tail -n $PORTIONTODISCARD > $BILEXTRACTIONDIR/devcorpus.${FLAGS_corpus_head_size}.$SL
	zcat $BILEXTRACTIONDIR/$TL.txt.gz | tail -n $PORTIONTODISCARD > $BILEXTRACTIONDIR/devcorpus.${FLAGS_corpus_head_size}.$TL
    fi
  fi

  #run makefile to extract bilingual phrases
  pushd $BILEXTRACTIONDIR
  make PAR_DONT_REMOVE_CONFLICTS=yes PAR_MAX=$MAX_LENGTH PAR_L1=$SL PAR_L2=$TL PAR_NO_SHORT_RESTRICTIONS=yes PAR_MY_EXTRACTING=yes $MARKERFLAG PAR_DATADIR="$DATADIR" PAR_RULELEARNINGLIBDIR="$FULLRULELEARNINGDIR" PAR_GIZADIR="$GIZADIR" PAR_ENDS_ALIGNED="ENDSALIGNED"  $STRUCTMAKVAR $CORPUSANALYSEDMAKVAR PAR_VARIANT="$VARIANT"  PAR_EXTREMES_VARIANT="$EXTREMESVARIANT" $ZENSMAKVAR $FIXEDDICTMAKVAR $LEMMATIZEDMAKVAR $ALIGNMENTSHEADMAKVAR $BILDIXMAKVAR $BILDIXFORALIGNMAKVAR $MONODIXL1MAKVAR $MONODIXL2MAKVAR
  popd

  else

  echo "Bilingual phrase extraction directory already exists. Omitting bilingual phrase extraction." 1>&2

  fi
  
  if [ "${FLAGS_corpus_is_already_analysed}" != "${FLAGS_TRUE}" ]; then
  if [ "$PORTIONTODISCARD" != "" ]; then
  	DEV_CORPUS=$BILEXTRACTIONDIR/devcorpus.${FLAGS_corpus_head_size}
  fi
  fi
  
  if [ "${FLAGS_only_extract_bilingual_phrases}" != "${FLAGS_TRUE}" ]; then

    #extract transfer rules from bilingual phrases

    #1. generate multiple alignment templates from each bilingual phrases
    if [ ! -e $TMPDIR/generalisation ]; then
    bash $CURDIR/rule-generalisation/run-experiment-linear-incremental-parallel-v8.sh -v -6 -d $TMPDIR  -f $BILEXTRACTIONDIR/alignmentTemplatesPlusLemmas.withalllemmas.onlyslpos.filtered-1-count.${SL}-${TL}.gz -i "." -x "_$PAIR" $ONLYLEXGENFLAG
    else
    echo "AT generalisation direrctory already exists. Omitting AT generalisation." 1>&2
    fi
    
    FILTERING_NAME=proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above$THETA
    
    #2. minimise alignment templates
    if [ ! -e $TMPDIR/filtering-$FILTERING_NAME ]; then
    bash $CURDIR/rule-generalisation/filter-and-linear-prog-incremental-parallel-v6.sh  -d $TMPDIR -i . -s $THRESHOLD_START -a $THRESHOLD_STEP -b $THRESHOLD_END -o $FILTERING_NAME -x "_$PAIR" -n 
    else
    echo "AT minimisation directory already exists. Omitting AT minimisation." 1>&2
    fi
   
    SOURCESDIR=`echo "$DATADIR" | sed 's,/*[^/]\+/*$,,'`
    PAIROFDATADIR=`basename $DATADIR | sed 's:^apertium-::'`
    
    APERTIUMPREFIXDATADIR="$APERTIUMPREFIX/share/apertium"
   
    #3. select the best sequences of lexical catgeories
    #first, create mode
    bash $CURDIR/rule-generalisation/createModeForBeamSearchEvaluation.sh  $APERTIUMPREFIXDATADIR/modes/${SL}-$TL.mode "" $CURDIR/phrase-extraction/transfer-tools-scripts/apertium-${PAIR}.posttransfer.ptx > $APERTIUMPREFIXDATADIR/modes/${TL}_lex_from_beam-${TL}.mode
    
    if  [ ! -e $TMPDIR/beamsearch-$FILTERING_NAME ]; then
    mkdir -p $TMPDIR/beamsearch-$FILTERING_NAME
    #do beam search
    for THRESHOLD in `LC_ALL=C seq $THRESHOLD_START  $THRESHOLD_STEP $THRESHOLD_END` ; do
    	bash $CURDIR/rule-generalisation/beamSearch.sh --target_language $TL --tag_groups_seqs_suffix "_$PAIR" --ats_filtering_dir $TMPDIR/filtering-$FILTERING_NAME/ats/ --dir $TMPDIR/beamsearch-$FILTERING_NAME/ --sentences $TMPDIR/bilingualphrases/alignments.${SL}-${TL}.gz.toBeam.gz  --ats_suffix "-f-$THRESHOLD.result.gz"  --apertium_data_dir $APERTIUMPREFIXDATADIR --final_boxes_index  $TMPDIR/generalisation/finalboxesindex
    done
    fi
    
    if  [ ! -e $TMPDIR/maximise-score-$FILTERING_NAME ]; then
    #select categories
    cp $TMPDIR/bilingualphrases/alignments.${SL}-${TL}.gz.toBeam.gz $TMPDIR/beamsearch-$FILTERING_NAME/sentences.gz
    for THRESHOLD in `LC_ALL=C seq $THRESHOLD_START $THRESHOLD_STEP $THRESHOLD_END` ; do
    	bash $CURDIR/rule-generalisation/selectRulesMaximiseScore.sh --target_language $TL --beam_search_dir $TMPDIR/beamsearch-$FILTERING_NAME  --dir $TMPDIR/maximise-score-$FILTERING_NAME --ats_suffix "-f-$THRESHOLD.result.gz"  --beam "yes" --final_boxes_index $TMPDIR/generalisation/finalboxesindex  --tag_groups_seqs_suffix "_$PAIR" --apertium_data_dir $APERTIUMPREFIXDATADIR --input_is_not_split
    done
    fi
    
    #4. convert alignment templates to Apertium rules and test them
    if [ "$PAIROFDATADIR" == "$PAIR" ]; then
    INVERSE_PAIR_TUNING_FLAG=""
    else
    INVERSE_PAIR_TUNING_FLAG="-i"
    fi

    if [ ! -e $TMPDIR/tuning-$FILTERING_NAME-${THRESHOLD_START}-${THRESHOLD_STEP}-${THRESHOLD_END}-subrules/summary ]; then
    bash $CURDIR/rule-generalisation/tune-experiment-linear-incremental-parallel-v8.sh -f $SOURCESDIR -p $APERTIUMPREFIX -s $SL -t $TL  -d $TMPDIR -c "$DEV_CORPUS" -e "$TEST_CORPUS" -r $THRESHOLD_START -a $THRESHOLD_STEP -b $THRESHOLD_END -o $FILTERING_NAME -x "_$PAIR" -z $INVERSE_PAIR_TUNING_FLAG -l -v
    else
    echo "Rule redundancy removal, tuning and testing directory already exists. Omitting rule redundancy removal, tuning and testing." 1>&2
    fi
 
 fi

fi

if [ "$CANDIDATE2" != "" ]; then
	rm "$CANDIDATE2"
fi
