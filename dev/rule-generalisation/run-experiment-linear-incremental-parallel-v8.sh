INPUTFILE=. 	
WORKDIR=../work-es-ca-transfertools-2M/linear-experiments
ID="shuf10"
CURDIR=`dirname $0`


#types of generalisation:
# -c : classic method. TL special attributes follow alignments. Do not use
# -c -n : new method. TL special attributes contain references to SL tags. Subproblems are split according to category and restrictions
# (nothing) : new method.TL special attributes contain references to SL tags and blingual dictionary Subproblems are split according to category
# -r : new method.TL special attributes contain references to SL tags and blingual dictionary. All the combinations of restrictions are explored. Subproblems are split according to category
# -g : new method.TL special attributes contain references to SL tags and blingual dictionary. Combinations of restrictions GD;ND, etc. are explored. Subproblems are split according to category
# -l : new method.TL special attributes contain references to SL tags and blingual dictionary. Combinations of restrictions combinations of restrictions GD;ND;mf;,etc are explored. Subproblems are split according to category

NUM_PARTS=1
CHOSEN_PART=1

COPY_EMPTY_TAGS=="no"

TAGSEQUENCESANDGROUPSSUFFIX=""
TAGGROUPSGENEMPTYSL=""
TAGGROUPSGENEMPTYTL=""

PYTHONHOME=""

STEP=""

PARALLELONLYONE=""

RICHATS="yes"
RICHATSFLAG="--rich_ats --ref_to_biling"
POWERSETFEATURESFLAG="--generalise_from_right_to_left"
RICHATSFLAGONLYGEN=""
DIFFERENTRESTRICTIONSFLAGP1=""
DIFFERENTRESTRICTIONSFLAGP2=""

GENATTRIBUTEINSTANCESTOGETHER=""

GENATTRIBUTESLIKEINPAPER=""

FIRSTMINIMISELEMMAS=""

UNLEXICALISEUNALIGNEDSLFLAG=""

ALT_INPUTFILE=""

ONLYLEXICALGENFLAG=""

usage()
{
cat << EOF
Bla bla bla	
	
EOF
}

while getopts “f:d:i:p:x:e:h:t:m:yqca:nrglvsubjkowz:567” OPTION
do
     case $OPTION in
        f)
             INPUTFILE=$OPTARG
             ;;
        z)
	     ALT_INPUTFILE=$OPTARG
	     ;;
        d)
             WORKDIR=$OPTARG
             ;;
        i)
	     ID=$OPTARG
             ;;
        x)
                TAGSEQUENCESANDGROUPSSUFFIX=$OPTARG
                ;;
        e)
                TAGGROUPSGENEMPTYSL=$OPTARG
                ;;
        h)
                PYTHONHOME=$OPTARG
                ;;
        t)
                STEP=$OPTARG
                ;;
        m)
                NUM_PARTS=`echo "$OPTARG" | cut -f 2 -d '-'` 
                CHOSEN_PART=`echo "$OPTARG" | cut -f 1 -d '-'` 
                ;;
        y)
                COPY_EMPTY_TAGS="yes"
                ;;
        q)
                PARALLELONLYONE="-j 1"
                ;;
        c)
               RICHATS="no"
               RICHATSFLAG=""
               ;;
        a)
                POWERSETFEATURESFLAG="--times_attributes_change $OPTARG" #generate all combinations of features to generalise
                ;;
        n)
		RICHATSFLAGONLYGEN="--rich_ats"
		;;
	r)
	        DIFFERENTRESTRICTIONSFLAGP1="--different_restriction_options"
	        ;;
	g)
	        DIFFERENTRESTRICTIONSFLAGP1="--different_restriction_options --only_to_be_determined_in_restriction"
	        ;;
	l)
	        DIFFERENTRESTRICTIONSFLAGP1="--different_restriction_options --only_to_be_determined_and_mf_in_restriction"
	        ;;
	s)
		DIFFERENTRESTRICTIONSFLAGP1="--different_restriction_options --only_to_be_determined_and_change_in_restriction"
	        ;;
	b)
		DIFFERENTRESTRICTIONSFLAGP1="--different_restriction_options --only_tags_triggering_diference_in_restriction"
		;;
	j)
		DIFFERENTRESTRICTIONSFLAGP1="--different_restriction_options --only_tags_triggering_diference_in_restriction --triggering_limited_length"
		;;
	k)
	       DIFFERENTRESTRICTIONSFLAGP1="--different_restriction_options --only_tags_triggering_diference_in_restriction --triggering_limited_length --triggering_no_good_discarded"
		;;
	o)
	       DIFFERENTRESTRICTIONSFLAGP1="--different_restriction_options --only_tags_triggering_diference_in_restriction --triggering_limited_length --discard_restrictions_not_improving"
	       ;;
	v)
	       DIFFERENTRESTRICTIONSFLAGP2="--add_restrictions_to_every_tag"
	       ;;
	u)
	      FIRSTMINIMISELEMMAS="yes"
	      ;;
	w)
	     UNLEXICALISEUNALIGNEDSLFLAG="--unlexicalise_unaligned_sl"
	     ;;
	5)
	     GENATTRIBUTEINSTANCESTOGETHER="--dont_generalise_all_instances_together"
	     ;;
	6)
	     GENATTRIBUTESLIKEINPAPER="--generalisable_attributes_like_in_paper"
	     ;;
	7)
	     ONLYLEXICALGENFLAG="--only_lexical"
	     ;;
        ?)
             usage
             exit
             ;;
     esac
done

DIFFERENTRESTRICTIONSFLAG="$DIFFERENTRESTRICTIONSFLAGP2 $DIFFERENTRESTRICTIONSFLAGP1"

if [ "COPY_EMPTY_TAGS" == "yes" ]; then
	TAGGROUPSGENEMPTYSL=`cat $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX | cut -f 1 -d ':' | tr '\n' ','`
	TAGGROUPSGENEMPTYTL=$TAGGROUPSGENEMPTYSL
fi

CHOSEN_PART_MINUS_ONE=`expr $CHOSEN_PART - 1`

TRUEWORKDIR="$WORKDIR/$ID"
mkdir -p $TRUEWORKDIR

mkdir -p $TRUEWORKDIR/generalisation/newbilphrases
mkdir -p $TRUEWORKDIR/generalisation-alt1/newbilphrases

#if [ ! -f $TRUEWORKDIR/alignmentTemplatesPLusLemmas.gz ]; then

BOXESINDEX="$TRUEWORKDIR/generalisation/boxesindex"

if [ "$STEP" == "1" -o  "$STEP" == "" ]; then

	rm -f $BOXESINDEX

	CURRENTID=1

	echo "Sorting input file" >&2

	RICHATSFLAGFORADD=""
	if [ "$RICHATS" == "yes" ]; then
		RICHATSFLAGFORADD="--rich_ats"
	fi

	#sort input by sl tags and restrictions
	zcat $INPUTFILE $ALT_INPUTFILE  | ${PYTHONHOME}python $CURDIR/addPosAndRestrictionsStr.py --tag_groups_file_name $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --tag_sequences_file_name $CURDIR/tagsequences$TAGSEQUENCESANDGROUPSSUFFIX $RICHATSFLAGFORADD | sed 's_ |_|_' | LC_ALL=C sort | ${PYTHONHOME}python $CURDIR/spreadBilphrases.py  > $BOXESINDEX

	zcat $INPUTFILE | ${PYTHONHOME}python $CURDIR/addPosAndRestrictionsStr.py --tag_groups_file_name $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --tag_sequences_file_name $CURDIR/tagsequences$TAGSEQUENCESANDGROUPSSUFFIX $RICHATSFLAGFORADD | sed 's_ |_|_' | LC_ALL=C sort | ${PYTHONHOME}python $CURDIR/spreadBilphrases.py --dir $TRUEWORKDIR/generalisation --dict $BOXESINDEX

	if [ "$ALT_INPUTFILE" != "" ]; then
		zcat  $ALT_INPUTFILE  | ${PYTHONHOME}python $CURDIR/addPosAndRestrictionsStr.py --tag_groups_file_name $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --tag_sequences_file_name $CURDIR/tagsequences$TAGSEQUENCESANDGROUPSSUFFIX $RICHATSFLAGFORADD | sed 's_ |_|_' | LC_ALL=C sort | ${PYTHONHOME}python $CURDIR/spreadBilphrases.py --dir $TRUEWORKDIR/generalisation-alt1 --dict $BOXESINDEX
	fi

fi

BOXESINDEXVAR=`cat $BOXESINDEX`


if [ "$STEP" == "2" -o  "$STEP" == "" ]; then

echo "Computing generalisations" >&2

#compute all generalisations
mkdir -p $TRUEWORKDIR/generalisation/ats
mkdir -p $TRUEWORKDIR/generalisation/debug

mkdir -p $TRUEWORKDIR/generalisation-alt1/ats
mkdir -p $TRUEWORKDIR/generalisation-alt1/debug

#rm -f $TRUEWORKDIR/generalisation/boxesofnewdata
#for file in `ls $TRUEWORKDIR/generalisation/newbilphrases`; do
#	BOXNAME=${file%.bilphrases.gz}
#	echo "$BOXNAME" >> $TRUEWORKDIR/generalisation/boxesofnewdata
#done

cat $BOXESINDEX | cut -f 2 | sed 's/__CLOSEWORD__/_a_CLOSEWORD_a_/g' |  awk -F"__" '{print NF"|"$0}' | LC_ALL=C sort -r -n -k1,1 -t '|' | sed 's_^[^|]*|__' | sed 's/_a_CLOSEWORD_a_/__CLOSEWORD__/g' > $TRUEWORKDIR/generalisation/boxesofnewdata.sorted.bylength.tmp
rm -f $TRUEWORKDIR/generalisation/boxesofnewdata.sorted.bylength
for line in `cat $TRUEWORKDIR/generalisation/boxesofnewdata.sorted.bylength.tmp`; do
	INDEXLINE=`echo "$BOXESINDEXVAR" | grep "	$line\$" `
	echo "$INDEXLINE" | cut -f 1 >> $TRUEWORKDIR/generalisation/boxesofnewdata.sorted.bylength
done

split -l 10000 $TRUEWORKDIR/generalisation/boxesofnewdata.sorted.bylength $TRUEWORKDIR/generalisation/boxesofnewdata.sorted.bylength.split
cat $BOXESINDEX > $TRUEWORKDIR/generalisation/finalboxesindex

if [ "$FIRSTMINIMISELEMMAS" == "" ]; then
  
  #[ \"\`expr \$INDEX \% $NUM_PARTS\`\" == \"$CHOSEN_PART_MINUS_ONE\" ]
  for file in $TRUEWORKDIR/generalisation/boxesofnewdata.sorted.bylength.split* ; do 
	  GENERALISATION_DIR=$TRUEWORKDIR/generalisation
	  #parallel $PARALLELONLYONE -i  bash -c "INDEX=\`echo \"{}\" | cut -f 2\`; NUMLINE=\`echo \"{}\" | cut -f 1\`;  if [ \"\`expr \$NUMLINE % $NUM_PARTS\`\" == \"$CHOSEN_PART_MINUS_ONE\" ] ; then  zcat \"$GENERALISATION_DIR/newbilphrases/\$INDEX.bilphrases.gz\" | ${PYTHONHOME}python $CURDIR/generateMultipleATsFromBilphrases.py --tag_groups_file_name $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --tag_sequences_file_name $CURDIR/tagsequences$TAGSEQUENCESANDGROUPSSUFFIX $RICHATSFLAG $RICHATSFLAGONLYGEN $POWERSETFEATURESFLAG $DIFFERENTRESTRICTIONSFLAG $UNLEXICALISEUNALIGNEDSLFLAG $GENATTRIBUTESLIKEINPAPER $ONLYLEXICALGENFLAG 2> \"$GENERALISATION_DIR/debug/debug-generalisation-\$INDEX\" | gzip > $GENERALISATION_DIR/ats/\$INDEX.ats.gz; gzip \"$GENERALISATION_DIR/debug/debug-generalisation-\$INDEX\"; fi;" -- `cat $file | awk '{printf "%d\t%s\n", NR, $0}'`
	  parallel $PARALLELONLYONE -i  bash -c "INDEX=\`echo \"{}\"\`;  if [ \"\`expr \$INDEX % $NUM_PARTS\`\" == \"$CHOSEN_PART_MINUS_ONE\" ] ; then  zcat \"$GENERALISATION_DIR/newbilphrases/\$INDEX.bilphrases.gz\" | ${PYTHONHOME}python $CURDIR/generateMultipleATsFromBilphrases.py --tag_groups_file_name $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --tag_sequences_file_name $CURDIR/tagsequences$TAGSEQUENCESANDGROUPSSUFFIX $RICHATSFLAG $RICHATSFLAGONLYGEN $POWERSETFEATURESFLAG $DIFFERENTRESTRICTIONSFLAG $UNLEXICALISEUNALIGNEDSLFLAG $GENATTRIBUTESLIKEINPAPER $ONLYLEXICALGENFLAG 2> \"$GENERALISATION_DIR/debug/debug-generalisation-\$INDEX\" | gzip > $GENERALISATION_DIR/ats/\$INDEX.ats.gz; gzip \"$GENERALISATION_DIR/debug/debug-generalisation-\$INDEX\"; fi;" -- `cat $file`
	  
	  if [ "$ALT_INPUTFILE" != "" ]; then
		GENERALISATION_DIR=$TRUEWORKDIR/generalisation-alt1
		parallel $PARALLELONLYONE -i  bash -c "INDEX=\`echo \"{}\" | cut -f 2\`; NUMLINE=\`echo \"{}\" | cut -f 1\`;  if [ \"\`expr \$NUMLINE % $NUM_PARTS\`\" == \"$CHOSEN_PART_MINUS_ONE\" ] ; then  zcat \"$GENERALISATION_DIR/newbilphrases/\$INDEX.bilphrases.gz\" | ${PYTHONHOME}python $CURDIR/generateMultipleATsFromBilphrases.py --tag_groups_file_name $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --tag_sequences_file_name $CURDIR/tagsequences$TAGSEQUENCESANDGROUPSSUFFIX $RICHATSFLAG $RICHATSFLAGONLYGEN $POWERSETFEATURESFLAG $DIFFERENTRESTRICTIONSFLAG $UNLEXICALISEUNALIGNEDSLFLAG $GENATTRIBUTESLIKEINPAPER $ONLYLEXICALGENFLAG 2> \"$GENERALISATION_DIR/debug/debug-generalisation-\$INDEX\" | gzip > $GENERALISATION_DIR/ats/\$INDEX.ats.gz; gzip \"$GENERALISATION_DIR/debug/debug-generalisation-\$INDEX\"; fi;" -- `cat $file | awk '{printf "%d\t%s\n", NR, $0}'`
	  fi
  done

else
 
  #TODO: make this work with alternative input files
 
  mkdir -p $TRUEWORKDIR/generalisation/onlylexicalats
  #Generate ATs changing lemmas
  for file in $TRUEWORKDIR/generalisation/boxesofnewdata.sorted.bylength.split* ; do 
	  parallel $PARALLELONLYONE -i  bash -c "INDEX=\`echo \"{}\" | cut -f 2\`; NUMLINE=\`echo \"{}\" | cut -f 1\`;  if [ \"\`expr \$NUMLINEX % $NUM_PARTS\`\" == \"$CHOSEN_PART_MINUS_ONE\" ] ; then rm \"$TRUEWORKDIR/generalisation/debug/debug-onlylexical-\$INDEX.gz\" ; zcat \"$TRUEWORKDIR/generalisation/newbilphrases/\$INDEX.bilphrases.gz\" | ${PYTHONHOME}python $CURDIR/generateMultipleATsFromBilphrases.py --tag_groups_file_name $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --tag_sequences_file_name $CURDIR/tagsequences$TAGSEQUENCESANDGROUPSSUFFIX --rich_ats --ref_to_biling --add_restrictions_to_every_tag --only_lexical $UNLEXICALISEUNALIGNEDSLFLAG $GENATTRIBUTESLIKEINPAPER 2> \"$TRUEWORKDIR/generalisation/debug/debug-onlylexical-\$INDEX\" | gzip > $TRUEWORKDIR/generalisation/onlylexicalats/\$INDEX.ats.gz; gzip \"$TRUEWORKDIR/generalisation/debug/debug-onlylexical-\$INDEX\"; fi;" -- `cat $file | awk '{printf "%d\t%s\n", NR, $0}'`
  done

  #Minimise
  for file in $TRUEWORKDIR/generalisation/boxesofnewdata.sorted.bylength.split* ; do 
	  parallel $PARALLELONLYONE -i  bash -c "INDEX=\`echo \"{}\" | cut -f 2\`; NUMLINE=\`echo \"{}\" | cut -f 1\`;  if [ \"\`expr \$NUMLINE % $NUM_PARTS\`\" == \"$CHOSEN_PART_MINUS_ONE\" ] ; then rm \"$TRUEWORKDIR/generalisation/debug/debug-onlylexical-\$INDEX.result.gz\" ; ${PYTHONHOME}python $CURDIR/chooseATs.py --tag_groups_file $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --tag_sequences_file $CURDIR/tagsequences$TAGSEQUENCESANDGROUPSSUFFIX --gzip $CONTRADICTORYORRELAX --read_generalised_bilphrases_from_dir \"$TRUEWORKDIR/generalisation/newbilphrases\"  --read_generalised_ats_from_file \"$TRUEWORKDIR/generalisation/onlylexicalats/\$INDEX\" --remove_third_restriction --relax_restrictions $GENATTRIBUTESLIKEINPAPER 2> \"$TRUEWORKDIR/generalisation/debug/debug-onlylexical-\$INDEX.result\" $GENATTRIBUTESLIKEINPAPER| gzip > \"$TRUEWORKDIR/generalisation/onlylexicalats/\$INDEX.ats.result.gz\"; gzip \"$TRUEWORKDIR/generalisation/debug/debug-onlylexical-\$INDEX.result\" ; fi;" -- `cat $file | awk '{printf "%d\t%s\n", NR, $0}'`
  done

  #Generate ATs with structural changes
  for file in $TRUEWORKDIR/generalisation/boxesofnewdata.sorted.bylength.split* ; do 
	  parallel $PARALLELONLYONE -i  bash -c "INDEX=\`echo \"{}\" | cut -f 2\`; NUMLINE=\`echo \"{}\" | cut -f 1\`;  if [ \"\`expr \$NUMLINE % $NUM_PARTS\`\" == \"$CHOSEN_PART_MINUS_ONE\" ] ; then  rm \"$TRUEWORKDIR/generalisation/debug/debug-generalisation-\$INDEX.gz\"; zcat \"$TRUEWORKDIR/generalisation/newbilphrases/\$INDEX.bilphrases.gz\" | ${PYTHONHOME}python $CURDIR/generateMultipleATsFromBilphrases.py --tag_groups_file_name $CURDIR/taggroups$TAGSEQUENCESANDGROUPSSUFFIX --tag_sequences_file_name $CURDIR/tagsequences$TAGSEQUENCESANDGROUPSSUFFIX $RICHATSFLAG $RICHATSFLAGONLYGEN $POWERSETFEATURESFLAG $DIFFERENTRESTRICTIONSFLAG $UNLEXICALISEUNALIGNEDSLFLAG $GENATTRIBUTESLIKEINPAPER --ats_with_allowed_lemmas_file \"$TRUEWORKDIR/generalisation/onlylexicalats/\$INDEX.ats.result.gz\"  2> \"$TRUEWORKDIR/generalisation/debug/debug-generalisation-\$INDEX\" | gzip > $TRUEWORKDIR/generalisation/ats/\$INDEX.ats.gz; gzip \"$TRUEWORKDIR/generalisation/debug/debug-generalisation-\$INDEX\"; fi;" -- `cat $file | awk '{printf "%d\t%s\n", NR, $0}'`
  done

fi

fi
