#! /bin/bash

FULLFILE=`readlink -f $0`
CURDIR=`dirname $FULLFILE`

#shflags
. $CURDIR/../../rule-generalisation/shflags

DEFINE_string 'input' '' 'input alignments' 'i'
DEFINE_string 'output' '' 'output bilphrases' 'o'
DEFINE_string 'min' '1' 'minimum length' 'n'
DEFINE_string 'max' '5' 'maximum length' 'm'
DEFINE_boolean 'gzip' 'false' 'gzipped input and output' 'z'

#process parameters
FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

if [ "${FLAGS_min}" != "1" ]; then
  echo "ERROR: minimum length is currently not supported. Using 1 instead" >&2
fi

if [ "${FLAGS_gzip}" == "${FLAGS_TRUE}" ]; then
  READ_COMMAND="zcat ${FLAGS_input}"
  OUTPUT_COMMAND="gzip"
else
  READ_COMMAND="cat ${FLAGS_input}"
  OUTPUT_COMMAND="cat -"
fi


#convert alignments to Moses format
#$READ_COMMAND | sed 's:^[^|]*| *::' |  sed 's:\([^\]\)|:\1|||:g' | gzip > ${FLAGS_input}.mosesformat.gz

$READ_COMMAND | cut -f 2 -d '|' | sed 's:^ *::' | sed 's: *$::' > ${FLAGS_input}.mosesformat.sl
$READ_COMMAND | cut -f 3 -d '|' | sed 's:^ *::' | sed 's: *$::' > ${FLAGS_input}.mosesformat.tl
$READ_COMMAND | cut -f 4 -d '|' | sed 's:^ *::' | sed 's: *$::' | tr ':' '-'  > ${FLAGS_input}.mosesformat.alignments

#run Moses bilphrase extraction
apertium-xtract-bilingual-phrases-koehn-2003 ${FLAGS_input}.mosesformat.tl ${FLAGS_input}.mosesformat.sl ${FLAGS_input}.mosesformat.alignments ${FLAGS_output}.mosesformat ${FLAGS_max}

#fix format
cat ${FLAGS_output}.mosesformat | sed 's:|||[^|]*$:|||:'  | sed 's:|||:|:g' > ${FLAGS_output}.mosesformat.withoutals
cat ${FLAGS_output}.mosesformat | sed 's:|||:|:g' | cut -f 4 -d '|' | tr '-' ':'  > ${FLAGS_output}.mosesformat.als

paste -d '' ${FLAGS_output}.mosesformat.withoutals ${FLAGS_output}.mosesformat.als | $OUTPUT_COMMAND > ${FLAGS_output}
