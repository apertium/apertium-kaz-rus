#Create HTML table

EXAMPLES_FILE=$1
ATS_FILE=$2

echo "<html><head>  <meta name=\"bla\" content=\"text/html;\" http-equiv=\"content-type\" charset=\"utf-8\"></head><body><table border=\"1\"><tr> <th>Freq</th> <th>AT</th> <th>Most freq examples</th> </tr>"
while read line; do
	FREQ=`echo "$line" | cut -f 1 -d ' '`
	#AT=`echo "$line"  | sed 's_^[^|]*| __' | sed 's_<_\&lt;_g' | sed 's_<_\&gt;_g'`
	AT=`echo "$line"  | sed 's_^[^|]*| __' | sed 's_><_._g' | sed 's_<_._g' | sed 's_>__g'`
	AT_OLD_ID=`echo "$line" | cut -f 4 -d ' '`
	AT_ID=`cat $ATS_FILE | nl |  grep -F "$AT_OLD_ID" | cut -f 1 | sed 's_^ *__'`
	echo "<tr><td>$FREQ</td><td>$AT</td>"
	
	echo "<td><table border=\"1\" width=\"100%\">"
	
	cat $EXAMPLES_FILE | grep -F " $AT_ID |"  | sed 's_ [0-9]* | __' | sed 's_^ *__' | sort -r -n -k1,1 -t ' ' | head -n  5 | {	
	while read secondline; do
		EXAMPLE=`echo "$secondline" | sed 's_^[0-9]*__' | sed 's_><_._g' | sed 's_<_._g' | sed 's_>__g'`
		EXAMPLE_FREQ=`echo "$secondline" | cut -f 1 -d ' '`
		#EXAMPLE="hola"
		echo "<tr><td>$EXAMPLE_FREQ</td><td>$EXAMPLE</td></tr>"
	done
	}
	
	#FIRST_EXAMPLE_LINE=`cat $DIR/evaluation/debug-extradebug-clean-withtlsurface | grep -F " $AT_ID |"  | sed 's_ [0-9]* | __' | sed 's_^ *__' | sort -r -n -k1,1 -t ' ' | head -n 1`
	#EXAMPLE=`echo "$FIRST_EXAMPLE_LINE" | sed 's_^[0-9]*__' | sed 's_><_._g' | sed 's_<_._g' | sed 's_>__g'`
	#EXAMPLE_FREQ=`echo "$FIRST_EXAMPLE_LINE" | cut -f 1 -d ' '`
	echo "<tr><td>$EXAMPLE_FREQ</td><td>$EXAMPLE</td></tr>"
		
	echo "</table></td></tr>"
	
	
done
echo "</table></body></html>"
