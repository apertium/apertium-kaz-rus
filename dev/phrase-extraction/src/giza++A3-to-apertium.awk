
# This script reads GIZA++ alignment and proccess them giving
# as an output a more human (and machine) readable format with the
# same information. From this new format it's easier to construct an
# aligment matrix between source and target sentences.
#
#
# Ouput format:
#     alignment_score | source_sentence | target_sentence | alignment
#
# Example:
#     5.07501e-05 | Reanudación del período de sesiones | Resumption of the session | 0:0 1:2 3:1 4:3
#
# Open question: What do we do with NULL words?
#                In this version they're ignored
#
# author: Felipe Sánchez-Martínez


function process_alignment(str) {
  source_sentence="";
  alignment="";

  ntokens=split(str, tokens, " }) ");
 
  sl_pos=0;

  for(i=1; i<=ntokens; i++) {
    if (length(tokens[i])==0)
      continue;

    nwa=split(tokens[i], wa, " ");
    if (nwa<2) {
      print "Error while processing the alignment information at input line " line > "/dev/stderr";
      exit 1;
    }

    if (wa[1] == "NULL") # NULL is ignored
      continue;

    if(length(source_sentence)>0) {
      source_sentence = source_sentence " ";
    } 
    source_sentence = source_sentence wa[1];

    for (j=3; j<=nwa; j++) {
      if (length(alignment)>0) {
	alignment = alignment " ";
      }
      alignment = alignment sl_pos ":" wa[j]-1;
    }

    sl_pos++;
  }
}

function trim(w) {
   for(i=1;i<=length(w);i++){
     if(substr(w,i,1)~/[ \t\r\n]/);
     else break;
   }
   liminf=i;

   for(i=length(w);i>=1;i--){
     if(substr(w,i,1)~/[ \t\r\n]/);
     else break;
   }

   limsup=i;

   return substr(w,liminf,limsup-liminf+1);
}

BEGIN {
  line=0;
  alignment_score=0;
  target_sentence="";
  source_sentence="";
  alignment="";
  reading_al=0;
}
{  
  line++; 
  if (reading_al==0)
    alignment_score=$NF;
  else if (reading_al==1)
    target_sentence=$0;
  else {
    process_alignment($0);
    print alignment_score " | " trim(source_sentence) " | " trim(target_sentence) " | " alignment;
  }

  reading_al++;
  if (reading_al>2)
    reading_al=0;
}
