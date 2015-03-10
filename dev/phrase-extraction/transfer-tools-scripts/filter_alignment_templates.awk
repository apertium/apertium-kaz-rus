#!/usr/bin/awk -f 

#author: Felipe Sánchez Martínez 

function trim(palabra,resultado,i,liminf,limsup)
{
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

function is_open_word(word) {
  return (index(word, "<")==1);
}


BEGIN{
  FS=" \\| ";
}
{

  count=$1;
  source=trim($2);
  target=trim($3);
  align=trim($4);
  restrictions=trim($5);

  skeep=0;
    
  #Do not consider ATs including unknown words
  if ((index(source, "__UNKNOWN__")>0)||(index(target, "__UNKNOWN__")>0))
    skeep=1;

  #Do not consider ATs including puntuation marks
  if ((index(source, "<sent>")>0)||(index(target, "<sent>")>0)||
      (index(source, "<cm>")>0)||(index(target, "<cm>")>0)||
      (index(source, "<rpar>")>0)||(index(target, "<rpar>")>0)||
      (index(source, "<lpar>")>0)||(index(target, "<lpar>")>0))
    skeep=1;

  if (!skeep)
     print $0;
}
