if [[ $1 = "rus-kaz" ]]; then
echo "==Russian->Kazakh===========================";
bash inconsistency1.sh rus-kaz > /tmp/rus-kaz.testvoc; bash inconsistency-summary1.sh /tmp/rus-kaz.testvoc rus-kaz
echo ""

fi
