
BEGIN{
FS="(\",\"|\"$)";  # field separators: "," and " at end of file: 
} 

NR>1 { 
  print "\"" $3 "\",\"" $2 "ый\""; 
  print "\"" $3 "\",\"" $2 "ий\""; 
} 
