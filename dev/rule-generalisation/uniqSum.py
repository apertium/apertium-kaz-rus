#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-

import sys,argparse

parser = argparse.ArgumentParser(description='Sums frequencies')
parser.add_argument('--freq_at_the_beginning',action='store_true')
parser.add_argument('--max',action='store_true')
args = parser.parse_args(sys.argv[1:])

prevContent=u""
prevSum=0

for line in sys.stdin:
	line=line.decode('utf-8').strip()
	parts=line.split(u" | ")
	if args.freq_at_the_beginning:
		freq=int(parts[0])
		content=u" | ".join(parts[1:])
	else:
		freq=int(parts[-1])
		content=u" | ".join(parts[:-1])
	if content == prevContent:
		if args.max:
			if freq > prevSum:
				prevSum=freq
		else:
			prevSum+=freq
	else:
		if prevContent!=u"":
			print str(prevSum).zfill(8)+" | "+prevContent.encode('utf-8')
		prevContent=content
		prevSum=freq

if prevContent!=u"":
			print str(prevSum).zfill(8)+" | "+prevContent.encode('utf-8')

	
