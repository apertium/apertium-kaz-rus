#!/bin/sh

sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<n><f><sg>[$])/^\1<det><def><f><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<n><f><sp>[$])/^\1<det><def><f><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<n><m><sg>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<n><m><sp>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<adj><f><sg>[$])/^\1<det><def><f><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<adj><m><sg>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<adj><ind><m><sg>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<adj><ind><f><sg>[$])/^\1<det><def><f><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<vblex><pp><m><sg>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<vblex><pp><f><sg>[$])/^\1<det><def><f><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<num>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<vblex><inf>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<adj><mf><sg>[$])[ ]+([\^][[:alnum:]]+<n><f><sg>[$])/^\1<det><def><f><sg>$ \2 \3/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<adj><mf><sg>[$])[ ]+([\^][[:alnum:]]+<n><m><sg>[$])/^\1<det><def><m><sg>$ \2 \3/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<prn><tn><m><sg>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<prn><tn><f><sg>[$])/^\1<det><def><f><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<n><acr><f><sg>[$])/^\1<det><def><f><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<n><acr><m><sg>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<adj><mf><sg>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<n><mf><sg>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<n><acr><f><sp>[$])/^\1<det><def><f><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:]_]+<n><acr><m><sp>[$])/^\1<det><def><m><sg>$ \2/g" |\
sed -re "s/[\^]([Ll]e)<det><def><mf><sg>[$][ ]+([\^][[:alnum:],.]+<num>[$])/^\1<det><def><m><sg>$ \2/g"
