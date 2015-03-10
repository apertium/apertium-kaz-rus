# /bin/bash

DIR="ERROR"
FILE="ERROR"
ID="ERROR"
CORPUS="ERROR"

CURDIR=`dirname $0`

ONLY_TABLE="no"

CURDIR=`dirname $0`

usage()
{
cat << EOF
Bla bla bla	
	
EOF
}
while getopts “d:t” OPTION
do
     case $OPTION in
		 d)
			DIR=$OPTARG
			;;
		 t)
			ONLY_TABLE="yes"
			;;
         ?)
             usage
             exit
             ;;
     esac
done

pushd $DIR/rules
ATS_FILE=`ls alignmentTemplates.txt.* | grep -v patterns | sort -n -r  -k3,3 -t '.' | head -n 1`
popd

if [ "$ONLY_TABLE" == "no" ]; then

#generating rules
apertium-gen-transfer-from-aligment-templates --input "$DIR/rules/$ATS_FILE" --attributes $CURDIR/taggroups --generalise --nodoublecheckrestrictions --usediscardrule | python $CURDIR/addDebugInfoToTransferRules-debug.py > "$DIR/rules/rules-extradebug.xml"

#compiling rules
apertium-preprocess-transfer "$DIR/rules/rules-extradebug.xml" "$DIR/rules/rules-extradebug.bin"

#creating modes 
mkdir -p $DIR/modes
bash $CURDIR/createModeWithLearnedRules.sh "/home/vmsanchez/rulesinteractive/local/share/apertium/modes/es-ca.mode" "" "$DIR/rules/rules-extradebug" "/work/vmsanchez/rules/transfer-tools-scripts-svn/apertium-es-ca.posttransfer.ptx" "/home/vmsanchez/hybridmt/tools/apertium-es-ca/es-ca.autobil.shortrestrictions.bin" "python $CURDIR/removeDebugInfoFromTransfer.py moredebug" > "$DIR/modes/es-ca-extradebug.mode"

#translating test corpus
cat $DIR/evaluation/source | apertium -d $DIR es-ca-extradebug > $DIR/evaluation/output-extradebug 2> $DIR/evaluation/debug-extradebug

cat "$DIR/evaluation/debug-extradebug" | grep -v "^0" | grep -v "^LOCALE:" > "$DIR/evaluation/debug-extradebug-clean"
cat "$DIR/evaluation/debug-extradebug-clean" |  grep -F "TARGET:" | sed 's_^TARGET: __' | sed 's_^$_EMPTY_' | /home/vmsanchez/rulesinteractive/local/bin/lt-proc -g /home/vmsanchez/rulesinteractive/local/share/apertium/apertium-es-ca/es-ca.autogen.bin | sed 's_\(.*\)_\n\1\n_' > "$DIR/evaluation/debug-extradebug-clean-tlsurface"
paste "$DIR/evaluation/debug-extradebug-clean" "$DIR/evaluation/debug-extradebug-clean-tlsurface" |  python /work/vmsanchez/rules/ruleLearning/collapseSourcetarget.py | LC_ALL=C sort | uniq -c > "$DIR/evaluation/debug-extradebug-clean-withtlsurface"

fi

#Create HTML table
NUM=`echo "$ATS_FILE" | cut -f 3 -d '.'`
cat $DIR/evaluation/report_rules_words_$NUM | bash $CURDIR/createHTMLTableFromFrequentRules.sh $DIR/evaluation/debug-extradebug-clean-withtlsurface > $DIR/evaluation/table.html


