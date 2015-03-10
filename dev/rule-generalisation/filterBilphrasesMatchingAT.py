#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-

import sys, ruleLearningLib, argparse

if __name__=="__main__":
	DEBUG=False
	
	parser = argparse.ArgumentParser(description='Chooses alignment templates.')
	parser.add_argument('--alignment_template',required=True)
	parser.add_argument('--tag_groups_file_name',required=True)
	parser.add_argument('--emptyrestrictionsmatcheverything',action='store_true')
	args = parser.parse_args(sys.argv[1:])
	
	ruleLearningLib.AT_LexicalTagsProcessor.initialize(args.tag_groups_file_name,None)
	
	#parse AT
	myAT=ruleLearningLib.AlignmentTemplate()
	myAT.parse(args.alignment_template.decode('utf-8'))
	if DEBUG:
		print >> sys.stderr, "AT: "+ myAT.to_string()
	
	for line in sys.stdin:
		line=line.strip().decode('utf-8')
		bilphrase=ruleLearningLib.AlignmentTemplate()
		bilphrase.parse(u'|'.join(line.split(u'|')[1:]))
		bilphrase.add_explicit_restrictions()
		if DEBUG:
			print >> sys.stderr, "Checking: "+bilphrase.to_string()
		if myAT.is_subset_of_this(bilphrase,True,args.emptyrestrictionsmatcheverything):
			print line.encode('utf-8')
