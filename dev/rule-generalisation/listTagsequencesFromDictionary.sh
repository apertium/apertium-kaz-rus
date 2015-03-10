#! /bin/bash

CURDIR=`dirname $0`

#shflags
. $CURDIR/shflags

DEFINE_string 'dictionary' '' '.dix file' 'd'
DEFINE_boolean 'generation' 'false' 'Generate lexical forms used in generation isntead of analysis' 'g'
#process parameters
FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

DIRECTION1="<"
DIRECTION2=">"
if [ "${FLAGS_generation}" == "true" ]; then
  DIRECTION1=">"
  DIRECTION2="<"
fi

lt-expand ${FLAGS_dictionary} |  grep -v -F ":$DIRECTION1:" | sed "s_:$DIRECTION2:_:_" | awk -F":" '{print $2 ;}' | LC_ALL=C sort | uniq | sed 's_^_^_' | sed 's_$_$_'  | apertium-pretransfer | sed 's:\$ \^:$\n^:g' | sed 's:^[^<]*<:<:' | sed 's:\$$::' | LC_ALL=C sort | uniq
