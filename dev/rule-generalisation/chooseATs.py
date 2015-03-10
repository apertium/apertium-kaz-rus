#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-

import sys, ruleLearningLib, re, copy, random, argparse, tsort, random, cPickle, gzip
from pulp import *
from time import time

if __name__=="__main__":
	DEBUG=False
	
	parser = argparse.ArgumentParser(description='Chooses alignment templates.')
	parser.add_argument('--tag_groups_file_name',required=True)
	parser.add_argument('--tag_sequences_file_name',required=True)
	parser.add_argument('--read_generalised_ats_from_file',required=True)
	parser.add_argument('--print_num_correct_unfiltered_bilphrases',action='store_true')
	parser.add_argument('--read_generalised_bilphrases_from_dir')
	parser.add_argument('--gzip',action='store_true')
	parser.add_argument('--up_one_dir',action='store_true')
	parser.add_argument('--debug',action='store_true')
	parser.add_argument('--remove_contradictory_ats',action='store_true')
	parser.add_argument('--relax_restrictions',action='store_true')
	parser.add_argument('--relax_weight',default='len(at_list)+2')
	parser.add_argument('--proportion_correct_bilphrases_threshold',default='0.00')
	parser.add_argument('--lambda_for_combining',default='0.00')
	parser.add_argument('--remove_third_restriction',action='store_true')
	parser.add_argument('--symmetric_difference',action='store_true')
	parser.add_argument('--first_select_restrictions',action='store_true')
	parser.add_argument('--dont_add_znorest',action='store_true')
	parser.add_argument('--more_specific_less_frequent',action='store_true')
	parser.add_argument('--dont_group_bilphrases',action='store_true')
	parser.add_argument('--dynamic_theta')
	#value = dir in which bilphrases will be written
	#ATs = std output
	parser.add_argument('--only_filter')
	
	args = parser.parse_args(sys.argv[1:])
	print >> sys.stderr, args
	
	if args.debug:
		DEBUG=True
		ruleLearningLib.DEBUG=True
		
	removeContradictoryATs=args.remove_contradictory_ats
	intermediate_input_file=args.read_generalised_ats_from_file
	read_generalised_bilphrases_from_dir=args.read_generalised_bilphrases_from_dir
	
	printNumCorrectUnfilteredBilphrases=args.print_num_correct_unfiltered_bilphrases
	proportionCorrectBilphrasesThreshold=float(args.proportion_correct_bilphrases_threshold)
	lambdaForCombining=float(args.lambda_for_combining)

	gzip_files=args.gzip
	uponedir_files=args.up_one_dir
	
	relaxRestrictions=args.relax_restrictions
	relaxWeight=args.relax_weight
	
	ruleLearningLib.AT_LexicalTagsProcessor.initialize(args.tag_groups_file_name,args.tag_sequences_file_name)
	
	fileToWriteBilphrases=None
	if args.only_filter:
		fileToWriteBilphrases=args.only_filter

				
	parts_int=intermediate_input_file.split("-")
	if  "/" in parts_int[-1]:
		intermediate_input_file_only_number=intermediate_input_file
	else:
		intermediate_input_file_only_number="-".join(parts_int[:-2])
	intermediate_input_file_only_number_aux=intermediate_input_file_only_number
	
	if uponedir_files:
		parts_slash=intermediate_input_file_only_number.split("/")
		parts_slash=parts_slash[:-2]+["ats"]+parts_slash[-1:]
		intermediate_input_file_only_number_aux="/".join(parts_slash)
	elif read_generalised_bilphrases_from_dir:
		parts_slash=intermediate_input_file_only_number.split("/")
		intermediate_input_file_only_number_aux=read_generalised_bilphrases_from_dir+"/"+parts_slash[-1]
	
	
	gzipSuffix=""
	if gzip_files:
		gzipSuffix=".gz"
	
	#Read ATs
	finalAlignmentTemplates=ruleLearningLib.AlignmentTemplateSet()
	atsFileName=intermediate_input_file+".ats"+gzipSuffix
	if gzip_files:
		file=gzip.open(atsFileName,'r')
	else:
		file=open(atsFileName,'r')
	id=0
	
	atsByFreq=dict()
	
	for line in file:
		line=line.strip().decode('utf-8')
		parts = line.split(u" | ")
		at = ruleLearningLib.AlignmentTemplate()
		at.parse(u" | ".join(parts[1:]))
		at.freq=int(parts[0])
		id+=1
		at.id=id
		if args.dynamic_theta:
			if at.freq not in atsByFreq:
				atsByFreq[at.freq]=list()
			atsByFreq[at.freq].append(at)
		else:
			finalAlignmentTemplates.add(at)
		
	file.close()
	
	#dynamically determine theta
	if args.dynamic_theta:
		limit=int(args.dynamic_theta)
		#sort by freq
		sortedFreqs=sorted(atsByFreq.keys(),reverse=True)
		
		numGroupsAccepted=0
		numAtsAccepted=0
		for freq in sortedFreqs:
			if numAtsAccepted+len(atsByFreq[freq]) <= limit:
				numAtsAccepted+=len(atsByFreq[freq])
				numGroupsAccepted+=1
			else:
				break
		print >> sys.stderr, "For limit="+str(limit)+", theta="+str(sortedFreqs[numGroupsAccepted-1] if numGroupsAccepted > 0 else -1 )
		for groupIndex in range(numGroupsAccepted):
			freqOfGroup=sortedFreqs[groupIndex]
			for at in atsByFreq[freqOfGroup]:
				finalAlignmentTemplates.add(at)
	
	#Read bilingual phrases
	bilphrases=ruleLearningLib.AlignmentTemplateSet()
	bilphrasesFileName=intermediate_input_file_only_number_aux+".bilphrases"+gzipSuffix
	if gzip_files:
		file=gzip.open(bilphrasesFileName,'r')
	else:
		file=open(bilphrasesFileName,'r')
	id=0
	for line in file:
		line=line.rstrip('\n').decode('utf-8')
		parts = line.split(u"|")
		at = ruleLearningLib.AlignmentTemplate()
		at.parse(u"|".join(parts[1:5]),True)
		sllemmas=parts[5].strip().split(u"\t")
		tllemmas=parts[6].strip().split(u"\t")
		tllemasfromdictionary=[ p.strip() for p in parts[7].split(u"\t")]
		if DEBUG:
			print >> sys.stderr, "setting Lemmas to: "+str(at)
			print >> sys.stderr, "SL: "+str(sllemmas)
			print >> sys.stderr, "TL: "+str(tllemmas)
		at.set_lemmas(sllemmas,tllemmas)
		at.tl_lemmas_from_dictionary=tllemasfromdictionary
		at.add_explicit_empty_tags()
		at.freq=int(parts[0])
		id+=1
		at.id=id
		bilphrases.add(at)
	file.close()
	
	#subsets are no longer used
	readSubsets=False
	if readSubsets:
		subsetGraphsFileName=intermediate_input_file_only_number_aux+".subsets"+gzipSuffix
		if gzip_files:
			file=gzip.open(subsetGraphsFileName,'rb')
		else:
			file=open(subsetGraphsFileName,'rb')
		subsetsGraph=cPickle.load(file)
		file.close()
	else:
		subsetsGraph=ruleLearningLib.SubsetGraph()
	
	#Choose ATs by linear programming
	
	#if restrictions can't be relaxed, the process of removing contradictory
	#ATs takes into account more particular versions (my old approach)
	
	myAts, reproducibleBilphrasesIds, time_correct_incorrect = ruleLearningLib.filter_pre_minimisation(bilphrases, finalAlignmentTemplates,subsetsGraph,removeContradictoryATs, args.print_num_correct_unfiltered_bilphrases, proportionCorrectBilphrasesThreshold, not(relaxRestrictions))
	
	#No linear programming. Write filtered bilphrases to dir.
	if fileToWriteBilphrases:
		
		if gzip_files:
			file=gzip.open(fileToWriteBilphrases+".bilphrases"+".gz",'w')
		else:
			file=open(fileToWriteBilphrases+".bilphrases",'w')
		for bil_id in reproducibleBilphrasesIds:
			bilphrase=bilphrases.get_by_id(bil_id)
			file.write(str(bilphrase.freq)+" | "+bilphrase.to_string(False,True)+"\n")
		file.close()
		
		for at in myAts.get_all_ats_list():
			print str(at.num_correct_bilphrases)+" "+str(at.num_matching_bilphrases)+" "+str(at.num_correct_bilphrases*1.0/at.num_matching_bilphrases)+" | "+at.to_string()

	#linear programming
	else:
		totaltimeinside=0.0
		if args.first_select_restrictions:
			selectedAts=ruleLearningLib.AlignmentTemplateSet()
			atgroups=myAts.get_all_ids_grouped_by_left_side()
			print >> sys.stderr, str(atgroups)
			for idsOfAtsWithSameLeftSide in atgroups:
				if len(idsOfAtsWithSameLeftSide)==1:
					for id in idsOfAtsWithSameLeftSide:
						selectedAts.add(myAts.get_by_id(id))
				else:
					localAts=ruleLearningLib.AlignmentTemplateSet()
					localBilphrases=set()
					for id in idsOfAtsWithSameLeftSide:
						locAt=myAts.get_by_id(id)
						localAts.add(locAt)
						localBilphrases.update(locAt.correct_bilphrases)
						if locAt.is_restriction_of_generalised_tags_empty() and not args.dont_add_znorest :
							selectedAts.add(locAt)
						
					restrictionsResult,ltimeinside=ruleLearningLib.minimise_linear_programming(localAts,localBilphrases,bilphrases,printNumCorrectUnfilteredBilphrases,lambdaForCombining,relaxRestrictions,relaxWeight,args.remove_third_restriction, args.symmetric_difference,args.more_specific_less_frequent)
					totaltimeinside+=ltimeinside
					for restAt in restrictionsResult:
						selectedAts.add(restAt)
		else:
			selectedAts=myAts
		
		if args.dont_group_bilphrases:
			result,ltimeinside=ruleLearningLib.minimise_linear_programming(selectedAts,reproducibleBilphrasesIds,bilphrases,printNumCorrectUnfilteredBilphrases,lambdaForCombining,relaxRestrictions,relaxWeight,args.remove_third_restriction, args.symmetric_difference,args.more_specific_less_frequent)
		else:
		  	groupedBilphrasesMapping,groupedBilphrasesInverseMapping,syntheticBilphraseSet=ruleLearningLib.group_bilphrases_behaving_equal(selectedAts,reproducibleBilphrasesIds,bilphrases)
			print >> sys.stderr, "From "+str(len(reproducibleBilphrasesIds))+" to "+str(len(groupedBilphrasesMapping))+" bilphrases with grouping"
			result,ltimeinside=ruleLearningLib.minimise_linear_programming(selectedAts,set(groupedBilphrasesMapping.keys()),syntheticBilphraseSet,printNumCorrectUnfilteredBilphrases,lambdaForCombining,relaxRestrictions,relaxWeight,args.remove_third_restriction, args.symmetric_difference,args.more_specific_less_frequent,groupedBilphrasesMapping,bilphrases)
		totaltimeinside+=ltimeinside
		print >> sys.stderr, "Time spent computing correct and incorrect bilphrases: "+str(time_correct_incorrect)
		print >> sys.stderr, "Total time: "+str(totaltimeinside+time_correct_incorrect)
		for at in result:
			print at
