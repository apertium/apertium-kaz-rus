#!/bin/sh

sed -re "s/[\^]([[:alnum:]]+)<det><(def|pos|ord|qnt)><sp>[$][ ]+([\^][[:alnum:]]+<n>(<acr>)?<sg>[$])/^\1<det><\2><sg>$ \3/g" |\
sed -re "s/[\^]([[:alnum:]]+)<det><(def|pos|ord|qnt)><sp>[$][ ]+([\^][[:alnum:]]+<n>(<acr>)?<sp>[$])/^\1<det><\2><sg>$ \3/g" |\
sed -re "s/[\^]([[:alnum:]]+)<det><(def|pos|ord|qnt)><sp>[$][ ]+([\^][[:alnum:]]+<n>(<acr>)?<pl>[$])/^\1<det><\2><pl>$ \3/g" |\
sed -re "s/[\^]([[:alnum:]]+)<det><(def|pos|ord|qnt)><sp>[$][ ]+([\^][[:alnum:]]+<num>[$])/^\1<det><\2><sg>$ \3/g" |\
sed -re "s/[\^]([[:alnum:]]+)<det><(def|pos|ord|qnt)><sp>[$][ ]+([\^][[:alnum:]]+<adj>(<sint>)?[$])[ ]+([\^][[:alnum:]]+<n>(<acr>)?<sg>[$])/^\1<det><\2><sg>$ \3 \5/g" |\
sed -re "s/[\^]([[:alnum:]]+)<det><(def|pos|ord|qnt)><sp>[$][ ]+([\^][[:alnum:]]+<adj>(<sint>)?[$])[ ]+([\^][[:alnum:]]+<n>(<acr>)?<pl>[$])/^\1<det><\2><pl>$ \3 \5/g" |\
sed -re "s/[\^]([[:alnum:]]+)<det><(def|pos|ord|qnt)><sp>[$][ ]+([\^][[:alnum:],.]+<num>[$])/^\1<det><\2><sg>$ \3/g" 
