
if [ $# != 1 ]
then 
  echo "USAGE: $(basename $0) <input_file>";
  exit 1;
fi

if [ ! -e $1 ] 
then 
  echo "ERROR: '$1' file not found";
  exit 1;
fi

$XMLLINT --dtdvalid $DTD --noout $1 && exit 0;
exit 1;
