
BEGIN{
FS="(\",\"|\"$)";  # field separators: "," and " at end of file: 
} 

NR>1 { 
  print $2 "ый"; 
  print $2 "ий"; 
} 
