#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-

import sys,ruleLearningLib,argparse

parser = argparse.ArgumentParser(description='Sums frequencies')
parser.add_argument('--freq_at_the_beginning',action='store_true')
args = parser.parse_args(sys.argv[1:])


for line in sys.stdin:
	genlist=list()
	line=line.strip().decode('utf-8')
	parts=line.split(u" | ")
	if len(parts) > 1:
		freq=parts[0]
		wordssec=parts[1]
		words=wordssec.split()
		for word in words:
			wordclean=word.strip()
			tags=ruleLearningLib.remove_lemmas_one(wordclean)
			taglist=ruleLearningLib.parse_tags(tags)
			genlist.append(u"<"+taglist[0]+u">")
			genStr=u" ".join(genlist)
			partsoutput=list()
			if args.freq_at_the_beginning:
				partsoutput.extend(parts)
				partsoutput.append(genStr)
			else:
				partsoutput.append(genStr)
				partsoutput.extend(parts[1:])
				partsoutput.append(freq)
		print u" | ".join(partsoutput).encode('utf-8')
		
	

