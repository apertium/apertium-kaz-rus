
# This script reads a corpus that has been analysed. It preprocess the corpus 
# before training the word alignments using GIZA++.
# 
# It remove all character not belonging to apertium words and replace each 
# space within apertium words by the character '_'.
# 
# Example of input:
# 
# Example of output:
#
# author: Felipe Sánchez-Martínez

function trim(palabra) {
   for(i=1;i<=length(palabra);i++){
     if(substr(palabra,i,1)~/[ \t\r\n]/);
     else break;
   }
   liminf=i;

   for(i=length(palabra);i>=1;i--){
     if(substr(palabra,i,1)~/[ \t\r\n]/);
     else break;
   }

   limsup=i;

   return substr(palabra,liminf,limsup-liminf+1);
}

BEGIN{FS="\\$"}
{
  c="";
  for (j=1; j<=NF; j++) {
    w=trim($j);
    w=substr(w,index(w,"^"));
    
    if ((length(w)>0) && (index(w,"^")>0)) {
      gsub(" ", "_", w);    
    
      if (length(c)>0)
        c = c " ";
      
      c = c w "$";
    }
  }
  #if (length(c)>0)
  print c;
}
