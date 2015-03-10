function gen_xml_file {
  # $1=infile
  # $2=tstset|srcset|refset
  # $3=sysid

  echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
  echo "<!DOCTYPE mteval SYSTEM \"ftp://jaguar.ncsl.nist.gov/mt/resources/mteval-xml-v1.3.dtd\">" 
  echo "<mteval>" 

  echo "<"$2" setid=\"mteval-01\" srclang=\"Source\" trglang=\"Target\" refid=\""$4"\" sysid=\""$3"\">" 
  
  echo "<doc docid=\"01\" genre=\"genre\" sysid=\""$4"\">" 
  cat  $1 | sed -re "s/[*](\w+)/\1/g" | gawk 'BEGIN{id=1}{print "<p><seg id=\""id"\">"$0"</seg></p>"; id++}' 
  echo "</doc>" 
  echo "</"$2">" 
  
  echo "</mteval>" 
}

gen_xml_file "$1" "$2" "$3"