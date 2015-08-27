TMPDIR=/tmp

DIR=$1

SED=sed

if [[ $DIR = "rus-kaz" ]]; then

#lt-expand ../../apertium-eng-kaz.eng.dix | grep -v -e '<compound-' -e 'DUE_TO_LT_PROC_HANG' | grep -v '<prn><enc>' | grep -v 'REGEX' | grep -v ':<:' | $SED 's/:>:/%/g' | $SED 's/:/%/g' | cut -f2 -d'%' |  $SED 's/^/^/g' | $SED 's/$/$ ^.<sent>$/g' | tee $TMPDIR/$DIR.tmp_testvoc1.txt |

# Run the bilingual dictionary before to make sure we are only checking things we have.
lt-expand ~/apertium-testing/apertium-rus/apertium-rus.rus.dix | grep -v '<prn><enc>' | grep -v 'REGEX' | grep -v ':<:' | $SED 's/:>:/%/g' | $SED 's/:/%/g' | cut -f2 -d'%' |  $SED 's/^/^/g' | $SED 's/$/$ ^.<sent>$/g' | apertium-pretransfer | lt-proc -b ~/apertium-testing/apertium-kaz-rus/rus-kaz.autobil.bin | grep -v '/@' | cut -f1 -d'/' | $SED 's/$/$ ^.<sent>$/g' | tee $TMPDIR/$DIR.tmp_testvoc1.txt |\
        apertium-pretransfer|\
	lt-proc -b ~/apertium-testing/apertium-kaz-rus/rus-kaz.autobil.bin | tee $TMPDIR/$DIR.tmp_testvoc2.txt |\
        apertium-transfer -b ~/apertium-testing/apertium-kaz-rus/apertium-kaz-rus.rus-kaz.t1x  ~/apertium-testing/apertium-kaz-rus/rus-kaz.t1x.bin |\
        apertium-interchunk ~/apertium-testing/apertium-kaz-rus/apertium-kaz-rus.rus-kaz.t2x  ~/apertium-testing/apertium-kaz-rus/rus-kaz.t2x.bin |\
        apertium-postchunk ~/apertium-testing/apertium-kaz-rus/apertium-kaz-rus.rus-kaz.t3x ~/apertium-testing/apertium-kaz-rus/rus-kaz.t3x.bin |\
        apertium-transfer -n ~/apertium-testing/apertium-kaz-rus/apertium-kaz-rus.rus-kaz.t4x  ~/apertium-testing/apertium-kaz-rus/rus-kaz.t4x.bin | tee $TMPDIR/$DIR.tmp_testvoc3.txt |\
        hfst-proc -d ~/apertium-testing/apertium-kaz-rus/rus-kaz.autogen.hfst > $TMPDIR/$DIR.tmp_testvoc4.txt
paste -d _ $TMPDIR/$DIR.tmp_testvoc1.txt $TMPDIR/$DIR.tmp_testvoc2.txt $TMPDIR/$DIR.tmp_testvoc3.txt $TMPDIR/$DIR.tmp_testvoc4.txt| $SED 's/\^.<sent>\$//g' | $SED 's/_/   --------->  /g'


else
	echo "bash inconsistency1.sh <direction>";
fi
