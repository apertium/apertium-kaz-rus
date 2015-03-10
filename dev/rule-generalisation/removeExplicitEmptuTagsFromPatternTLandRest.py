#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-

import sys,re,argparse

parser = argparse.ArgumentParser(description='Bla bla.')
parser.add_argument('--short',action='store_true')
parser.add_argument('--emptyrestrictionsmatcheverything',action='store_true')
args = parser.parse_args(sys.argv[1:])

if args.short:
	requiredLength=5
	partsToSubstitute=[2,4]
else:
	requiredLength=6
	if args.emptyrestrictionsmatcheverything:
		partsToSubstitute=[0,3]
	else:
		partsToSubstitute=[0,3,5]
	#partsToSubstitute=[0,3,6]
	
for line in sys.stdin:
	line=line.strip().decode('utf-8')
	parts=line.split(u'|')
	if len(parts)==requiredLength:
		for partindex in partsToSubstitute:
			parts[partindex] = re.sub(r'<empty_tag_[^>]*>', '', parts[partindex])
			
	print u'|'.join(parts).encode('utf-8')
