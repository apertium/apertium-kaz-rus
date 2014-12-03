#Converts CSV noun file exported from KazNU rus→kaz data
#MLF 20141201

BEGIN{
FS="(\",\"|\"$)";  # record separators: "," and " at end of file: 
g[1]="m"; # gender
g[2]="f";
g[3]="nt";
a[0]="nn"; # animacy
a[1]="nn";
a[4]="aa";
a[""]="nn";
} 

# We export only nouns that have some gender ("rod" in $5) and
# avoid exporting the first line which is a header
# Avoid empty lemmas too
NR>1 {if ($5~/[0-9]+/) print "<e><p><l>" $4 "<s n=\"n\"/></l><r>" $2  "<s n=\"n\"/><s n=\"" g[$5] "\"/><s n=\"" a[$8] "\"/></r></p></e>"}

