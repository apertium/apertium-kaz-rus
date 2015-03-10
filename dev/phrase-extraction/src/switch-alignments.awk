
# Switches SL and TL sides of the aligment, aligment information 
# is also switched.
#
# Felipe Sánchez Martínez

BEGIN{FS=" [|] "}
{
  alignment="";
  nalig=split($4, alig, " ");
  for (i=1; i<=nalig; i++) {
    n=split(alig[i], al, ":");
    if (n!=2) {
      print "Error: while reading alignment" > "/dev/stderr";
      exit 1;
    }
    if (length(alignment)>0)
      alignment = alignment " ";
    alignment = alignment al[2] ":" al[1];
  }
  
  print $1 " | " $3 " | " $2 " | " alignment;
}
