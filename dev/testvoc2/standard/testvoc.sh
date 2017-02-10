#!/bin/bash

# A script to run the standard (=full) testvoc.
#
# Assumes the pair is compiled.
# Expands the source language dictionary/transducer MONODIX and passes the
# result of the expansion through the translator (=inconsistency.sh script).
# Produces 'testvoc-summary.tat-rus.txt' file using the inconsistency-summary.sh.
#
# Usage: [TMPDIR=/path/to/tmpdir] ./testvoc.sh

if [ -z $TMPDIR ]; then
	TMPDIR="/tmp"
fi

export TMPDIR

# With Tatar transducer being trimmed to the bilingual dictionary, it is
# possible to run the full testvoc in a reasonable time (at least now, in the
# beginning, when the bidix is small) *ON ONE CONDITION* -- we do not include
# (cyclic) digits stuff in the .deps/tat-rus.automorf.trimmed.
# In order to trim them, we have to comment out the following line in tat-rus.dix
# <e>       <re>[â%]?[0-9]+([.,][0-9]+)*[.,]*</re><p><l><s n="num"/></l><r> ...
# and then compile:
cd ../../
#!/bin/bash

# A script to run the standard (=full) testvoc.
#
# Assumes the pair is compiled.
# Expands the source language dictionary/transducer MONODIX and passes the
# result of the expansion through the translator (=inconsistency.sh script).
# Produces 'testvoc-summary.tat-rus.txt' file using the inconsistency-summary.sh.
#
# Usage: [TMPDIR=/path/to/tmpdir] ./testvoc.sh

if [ -z $TMPDIR ]; then
	TMPDIR="/tmp"
fi

export TMPDIR

# With Tatar transducer being trimmed to the bilingual dictionary, it is
# possible to run the full testvoc in a reasonable time (at least now, in the
# beginning, when the bidix is small) *ON ONE CONDITION* -- we do not include
# (cyclic) digits stuff in the .deps/tat-rus.automorf.trimmed.
# In order to trim them, we have to comment out the following line in tat-rus.dix
# <e>       <re>[â%]?[0-9]+([.,][0-9]+)*[.,]*</re><p><l><s n="num"/></l><r> ...
# and then compile:
cd ../../
sed -i 's_^<e>       <re>\[â.*$_<!--&-->_' apertium-kaz.kaz.lexc
make
cd /home/apertium/apertium-testing/apertium-kaz/

function expand_monodix {
    hfst-fst2strings $MONODIX | sort -u | cut -d':' -f2 | \
    sed 's/^/^/g' | sed 's/$/$ ^.<sent>$/g'
}

#-------------------------------------------------------------------------------
# Kazakh->English testvoc
#-------------------------------------------------------------------------------

MONODIX=.deps/kaz.automorf.trimmed

echo "===Kazakh->English==========================="

expand_monodix |
bash inconsistency.sh kaz-eng > $TMPDIR/kaz-eng.testvoc
bash inconsistency-summary.sh $TMPDIR/kaz-eng.testvoc kaz-eng
make
cd /../apertium-testing/apertium-eng-kaz/dev/testvoc2/

function expand_monodix {
    hfst-fst2strings $MONODIX | sort -u | cut -d':' -f2 | \
    sed 's/^/^/g' | sed 's/$/$ ^.<sent>$/g'
}

#-------------------------------------------------------------------------------
# Kazakh->English testvoc
#-------------------------------------------------------------------------------

MONODIX=.deps/kaz.automorf.trimmed

echo "==Kazakh->English==========================="

expand_monodix |
bash inconsistency.sh kaz-eng > $TMPDIR/kaz-eng.testvoc
bash inconsistency-summary.sh $TMPDIR/kaz-eng.testvoc kaz-eng
