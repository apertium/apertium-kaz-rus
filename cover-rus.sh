DIX=/home/apertium/apertium-testing/apertium-rus/apertium-rus.rus.dix
BIN=/home/apertium/apertium-testing/apertium-kaz-rus/kaz-rus.automorf.bin
cat /home/apertium/apertium-testing/apertium-kaz-rus/texts/rus.txt | cut -f2 | grep -v '>(' | sed 's/&lt;/</g' | sed 's/&gt;/>/g' | apertium-destxt | lt-proc -w $BIN | apertium-retxt | sed 's/\$\W*\^/$\n^/g' > /tmp/rus.coverage.txt

EDICT=`cat $DIX | grep '<e lm' | wc -l`;
EPAR=`cat $DIX | grep '<pardef n' | wc -l`;
TOTAL=`cat /tmp/rus.coverage.txt | wc -l`
KNOWN=`cat /tmp/rus.coverage.txt | grep -v '*' | wc -l`
COV=`calc $KNOWN / $TOTAL`;
DATE=`date`;

echo -e $DATE"\t"$EPAR":"$EDICT"\t"$KNOWN"/"$TOTAL"\t"$COV >> history.log
tail -1 history.log
