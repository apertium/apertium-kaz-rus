#Converts CSV noun file exported from KazNU rus→kaz data
#MLF 20141201

BEGIN{
FS="(\",\"|\"$)";  # record separators: "," and " at end of file: 
g[1]="m"; # gender
g[2]="f";
g[3]="n";
a[0]="nn"; # animacy
a[1]="nn";
a[4]="aa";
a[""]="nn";
} 

{print "<e><p><l>" $4 "<s n=\"n\"/></l><r>" $2  "<s n=\"n\"/><s n=\"" g[$5] "\"/><s n=\"" a[$8] "\"/></r></p></e>"}

