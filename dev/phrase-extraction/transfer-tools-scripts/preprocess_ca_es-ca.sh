#!/bin/sh
sed -re "s/([\^])anar<vblex><pri>((<[a-z0-9]+>)+[$])[ ]+([\^][[:alnum:]]+)(<vblex><inf>|<vbmod><inf>|<vbser><inf>|<vbhaver><inf>[$])/\1anar<vaux>\2 \4\5/g" |\
./preprocess_ca.sh
