#! /bin/bash

sed 's:<[^>]*>::g' | sed 's:\^\$:^IAMANEMPTYLEXFORM$:g'  | sed 's:$ ^: :g' | sed 's:^^::' | sed 's:$$::' | sed 's:^\*::' | sed 's: \*: :g' | perl `dirname $0`/lowercase.perl