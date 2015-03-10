# coding=utf-8
# -*- encoding: utf-8 -*-

import sys, re, os.path, copy,traceback, tsort, traceback
from time import time
from pulp import *
from collections import defaultdict

DEBUG=False

class SubsetGraph(object):
	def __init__(self):
		
		#set of pairs (child_id,parent_id)
		self.arcs=set()
		
		#lefsideplusrestrictions -> id
		self.idsDict=dict()
		
		#id -> set of ids of adjacent nodes
		self.adjacency=dict()
		
		#list of lefsideplusrestrictions
		self.leftsidesList=list()
		
		#id->set of reachable ids
		self.cache=dict()
	
	#child=subset,parent=superset
	def add(self,child,parent):
		if not child in self.idsDict:
			self.leftsidesList.append(child)
			self.idsDict[child]=len(self.leftsidesList)-1
			self.adjacency[self.idsDict[child]]=set()
		if not parent in self.idsDict:
			self.leftsidesList.append(parent)
			self.idsDict[parent]=len(self.leftsidesList)-1
			self.adjacency[self.idsDict[parent]]=set()
		self.arcs.add((self.idsDict[child],self.idsDict[parent]))
		
		#debug
		if False:
			print >> sys.stderr, "List: " + str(self.leftsidesList)
			print >> sys.stderr, "Dict: "+ str(self.idsDict)
			print >> sys.stderr, "Child: "+ str(self.idsDict[child]) + " " + str(child)
			print >> sys.stderr, "Parent: "+ str(self.idsDict[parent]) + " " + str(parent)
			print >> sys.stderr, "Adjacency: "+ str(self.adjacency)
		
		self.adjacency[self.idsDict[child]].add(self.idsDict[parent])
	
	def reachable_from_iterative(self, node):
		nid=self.idsDict[node]
		outlist = [nid]
		to_traverse = [i for i in self.adjacency[nid]]
		while to_traverse:
			current = to_traverse.pop()
			outlist.append(current)
			if current in self.cache:
				outlist.extend(self.cache[current])
			else:
				to_traverse += [i for i in self.adjacency[current] if i not in outlist and i not in to_traverse]
		return_list=list()
		for oid in outlist:
			if oid!=nid:
				return_list.append(self.leftsidesList[oid])
				
		return return_list
	
	def reachable_from_recursive(self, nid):
		DEBUG_RECURSIVE=False
		
		if DEBUG_RECURSIVE:
			print >> sys.stderr, "Calculating reachable from "+str(nid)
		
		if not nid in self.cache:
			if DEBUG_RECURSIVE:
				print >> sys.stderr, "Reachable from "+str(nid)+" not found in cache"
				print >> sys.stderr, "Adjacent from "+str(nid)+": "+str(self.adjacency[nid])
			reachable=set()
			for ad in self.adjacency[nid]:
				reachable.add(ad)
				for rid in self.reachable_from_recursive(ad):
					reachable.add(rid)
			self.cache[nid]=reachable
		else:
			if DEBUG_RECURSIVE:
				print >> sys.stderr, "Reachable from "+str(nid)+" found in cache"
		
		if DEBUG_RECURSIVE:		
			print >> sys.stderr, "Reachable from "+str(nid)+": "+str(self.cache[nid])
	
		return self.cache[nid]
					
	def reachable_from(self,node):
		DEBUG=False
		if DEBUG:
			print >> sys.stderr, "idsDict: "+str(self.idsDict)
			
		return_list=list()
		#it may happen that the node is not present because the graph is empty
		if node in self.idsDict:
			nid=self.idsDict[node]
			for id in self.reachable_from_recursive(nid):
				return_list.append(self.leftsidesList[id])
		return return_list
	
	def to_string(self):
		return_str_list=list()
		for arc in self.arcs:
			return_str_list.append(u"child: "+self.leftsidesList[arc[0]]+u" -> parent: "+self.leftsidesList[arc[1]])
		return u"\n".join(return_str_list)	

class AlignmentTemplateSet(object):
	def __init__(self):
		self.pos_map=dict()
		self.MAX_EXCEPTIONS_RETURNED=10
		self.id_map=dict()
		self.id_map_by_pos=dict()
		self.left_side_map=defaultdict(set)
	
	def get_l2_maps(self):
		return self.pos_map.items()
	
	def get_ids_of_matching_and_compatible_phrases(self, at):
		bilphrases_matching=set()
		bilphrases_ok=set()
		num_bilphrases_matching=0
		num_bilphrases_ok=0
		
		#debug("Getting ids of matching and compatible bilingual phrases")
		#debug("AT: "+str(at))
		
		l2map=self.find_l2_map(at)
		
		if l2map:
			#debug("l2map found")
			for key in l2map.keys():
				listOfValues=l2map[key]
				onebilfromgroup=listOfValues[0]
				#debug(onebilfromgroup.parsed_restrictions[0].unparse().encode('utf-8'))
				#debug("Checking if matches: "+str(onebilfromgroup)+" ...")					
				if at.matches_bilphrase(onebilfromgroup):
					#debug(" YES")
					for bilphrase in listOfValues:
						bilphrases_matching.add(bilphrase.id)
						num_bilphrases_matching+=bilphrase.freq
						if at.is_bilphrase_reproducible(bilphrase):
							bilphrases_ok.add(bilphrase.id)
							num_bilphrases_ok+=bilphrase.freq
				else:
					pass
					#debug(" NO")
		else:
			pass
			#debug("l2map NOT found")
				
		return bilphrases_ok,bilphrases_matching, num_bilphrases_ok, num_bilphrases_matching
	
	def get_by_id(self,id):
		if id in self.id_map:
			return self.id_map[id]
		else:
			return None
	
	def get_all_ids(self):
		return self.id_map.keys()
	
	def get_total_freq(self):
		return sum( b.freq for b in self.get_all_ats_list() )
	
	def get_all_ats_list(self):
		allats=list()
		for myid in self.get_all_ids():
			allats.append(self.get_by_id(myid))
		return allats
		
	
	def get_one_at(self):
		return self.id_map.items()[0][1]
	
	def get_all_ids_from_l2map(self,key):
		return self.id_map_by_pos[key]
	
	def get_all_ids_grouped_by_left_side(self):
		returnList=list()
		for leftside,ids in self.left_side_map.iteritems():
			returnList.append(ids)
		return returnList
	
	def get_ats_with_sllex_and_restrictions(self,key1, key2):
		if key1 in self.pos_map:
			if key2 in self.pos_map[key1]:
				return self.pos_map[key1][key2]
		return []
	
	def add(self,at):
		l2map=self.find_l2_map(at,True)
		l3atlist=self.find_l3_atlist(at,l2map,True)
		isNew=False
		if at in l3atlist:
			index=l3atlist.index(at)
			l3atlist[index].increase_freq(at.freq)
		else:
			isNew=True
			l3atlist.append(at)
		if at.id != None and isNew:
			self.id_map[at.id]=at
			self.id_map_by_pos[at.get_pos_list_str()].add(at.id)
			self.left_side_map[at.get_left_side_str()].add(at.id)
	
	def is_in_set(self,at,returnAt=False):
		l2map=self.find_l2_map(at)
		if l2map:
			l3atlist=self.find_l3_atlist(at,l2map)
			if l3atlist:
				if at in l3atlist:
					if returnAt:
						index=l3atlist.index(at)
						return l3atlist[index]
					else:
						return True
		return False
	
	def get_ats_with_same_sllex_and_restrictions(self,at):
		l2map=self.find_l2_map(at)
		if not l2map:
			return []
		l3atlist=self.find_l3_atlist(at, l2map)
		if not l3atlist:
			return []
		return l3atlist
	
	def find_l3_atlist(self,at,l2map,create=False):
		sllexandresstr=at.get_sllex_and_restrictions_str()
		if sllexandresstr in l2map:
			return l2map[sllexandresstr]
		else:
			if create:
				l2map[sllexandresstr]=list()
				return l2map[sllexandresstr]
			else:
				return None
	
	def find_l2_map(self,at,create=False):
		pos_str=at.get_pos_list_str()
		if pos_str in self.pos_map:
			return self.pos_map[pos_str]
		else:
			if create:
				self.pos_map[pos_str]=dict()
				self.id_map_by_pos[pos_str]=set()
				return self.pos_map[pos_str]
			else:
				return None
	
	def apply_to_all(self,myfunction):
		for l2map in self.get_l2_maps():
			for listOfAts in l2map[1].values():
				for at in listOfAts:
					myfunction(at)
	def remove(self,id):
		at=self.id_map[id]
		sllexandrestrictions=at.get_sllex_and_restrictions_str()
		poslist=at.get_pos_list_str()
		self.id_map.pop(id)
		self.id_map_by_pos[poslist].remove(id)
		l2map=self.pos_map[poslist]
		listOfAts=l2map[sllexandrestrictions]
		atsToKeep=list()
		for anAt in listOfAts:
			if anAt.id!=id:
				atsToKeep.append(anAt)
		if len(atsToKeep) > 0:
			listOfAts[:]=atsToKeep
		else:
			del l2map[sllexandrestrictions]
		self.left_side_map[at.get_left_side_str()].discard(id)
		if len(self.left_side_map[at.get_left_side_str()]) == 0:
			del self.left_side_map[at.get_left_side_str()]
		
	
	def remove_contradictory_ats(self, takeIntoAccountMoreParticular=True):
		
		#currently ignores parameter and return empty set
		
		# No tengo muy claro todavía qué hace la opción de takeIntoAccountMoreParticular=True
		# Es mejor ejecutarlo con False. En ese caso, elimina contradicciones entre ATs
		# y tb elimina las frases bilingües que no son reproducidas por ninguna AT
		# tras eliminar las contradicciones
		
		bilphrasesToDelete=set()
		
		#addedinlastIteration=True
		#while addedinlastIteration:
			#bilphrasesToAdd=set()
		for l2map in self.get_l2_maps():
			for listOfAts in l2map[1].values():
				sortedList=sorted(listOfAts, key=lambda at: at.freq, reverse=True)
				discardedAts=sortedList[1:]
				keptAt=sortedList[0]
				listOfAts[:]=[ keptAt ]
				for at in discardedAts:
					self.remove(at.id)
						#sllexandrestrictions=at.get_sllex_and_restrictions_str()
						#for bil_id in at.correct_bilphrases:
							#explainedByAMoreParticular=False
							#for listOfAts2 in l2map[1].values():
							#	for at2 in listOfAts2:
							#		#AT2 es más particular y traduce bien bil_id
							#		if bil_id in at2.correct_bilphrases and (( not takeIntoAccountMoreParticular) or ( takeIntoAccountMoreParticular and at.is_subset_of_this(at2) and not at2.is_subset_of_this(at) ) ): 
							#			explainedByAMoreParticular=True
							#			break
							#	if explainedByAMoreParticular:
							#		break
							#if not explainedByAMoreParticular:
							#	bilphrasesToAdd.add(bil_id)
			#bilphrasesToDelete.update(bilphrasesToAdd)
			#if len(bilphrasesToAdd) > 0:
			#	addedinlastIteration=True
			#else:
			#	addedinlastIteration=False
			#bilphrasesToAdd=set()
					
		return bilphrasesToDelete

	
	def write(self,fileobj, printDictionaryTranslations=False):
		for l2map in self.get_l2_maps():
			for listOfAts in l2map[1].values():
				for at in listOfAts:
					fileobj.write(str(at.freq)+" | "+at.to_string(False,printDictionaryTranslations)+"\n")

class AllowedStructuresSet(AlignmentTemplateSet):
	def is_at_allowed(self,at):
		l2map=self.find_l2_map(at)
		if l2map == None:
			return False
		else:
			for atlist in l2map.values():
				for atstruct in atlist:
					if atstruct.is_struct_compatible_with(at):
						return True
			return False

		
def AlignmentTemplate_generate_all_generalisations(at,lemmassl,lemmastl,tllemmas_from_dic,taggroups):
	allGeneralisations=list()
	
	bilphrase=copy.deepcopy(at)
	bilphrase.lexicalise_all(lemmassl,lemmastl)
	bilphrase.tl_lemmas_from_dictionary=tllemmas_from_dic
	
	#Auto-align
	atList=list()
	options=at.get_alignment_options_for_unaligned_words(taggroups)
	for option in options:
		atcopy=copy.deepcopy(at)
		atcopy.add_alignments(option)
		atList.append(atcopy)

	#Lexicalise
	atListNext=list()
	for at in atList:
		indexesOfLexicalisableWords=list()
		for i in range(len(at.restrictions)):
			if at.restrictions[i]!=u"__CLOSEWORD__" and lemmassl[i]!=u"__NONLEXICALIZABLE__" and at.sl_lexforms[i].startswith(u"<"):
				indexesOfLexicalisableWords.append(i)
		optionsToCombine=list()
		for j in range(len(indexesOfLexicalisableWords)):
			optionsToCombine.append([True,False])
		lexicalisationCombinations=combine_elements(optionsToCombine)
		
		for lexicalisationCombination in lexicalisationCombinations:
			lexicalisedAt=copy.deepcopy(at)
			lexicalisedIndexes=list()
			for i in range(len(lexicalisationCombination)):
				if lexicalisationCombination[i]:
					lexicalisedIndexes.append(indexesOfLexicalisableWords[i])
			lexicalisedAt.lexicalise(lexicalisedIndexes,lemmassl,lemmastl)
			atListNext.append(lexicalisedAt)
	
	#Generalise
	for at in atListNext:
		atcopy=copy.deepcopy(at)
		
		if atcopy.is_bilphrase_reproducible(bilphrase):
			allGeneralisations.append(atcopy)
		
		while at.generalise(taggroups):
			atcopy=copy.deepcopy(at)
			if atcopy.is_bilphrase_reproducible(bilphrase):
				allGeneralisations.append(atcopy)
	
	return allGeneralisations

def AlignmentTemplate_generate_all_structural_generalisations(at,generalisationOptions):
	
	atsAfterGeneralisingAttributes=list()
	
	# compute generalisation stuff!
	attribute_names=set()
	sl_attribute_names=set()
	for lexform in at.parsed_sl_lexforms:
		attribute_names.update(lexform.get_tags_with_feature_names_as_dict().keys())
		sl_attribute_names.update(lexform.get_tags_with_feature_names_as_dict().keys())
	for lexform in at.parsed_tl_lexforms:
		attribute_names.update(lexform.get_tags_with_feature_names_as_dict().keys())
	
	#catgories present in restrictions not generalised if option is enabled
	if not generalisationOptions.is_refToBiling():
		for res in at.parsed_restrictions:
			attribute_names-=set(res.get_tags_with_feature_names_as_dict().keys())
	elif generalisationOptions.is_addRestrictionsForEveryTag():
		newAT=at.fast_clone()
		newAT.add_explicit_restrictions()
		at=newAT
		
	if not generalisationOptions.is_generalise():
		return [at]	
	
	debug("Generalising attributes for AT: "+str(at))		
	#for each feature name, compute its possible generalisation values
	newValuesForFeatures=dict()
	for featureName in attribute_names:
		valuesSL=list()
		for lexform in at.parsed_sl_lexforms:
			if featureName in lexform.get_categories():
				valuesSL.append([get_representation_of_sl_generalised_tag(featureName)])
			else:
				valuesSL.append([None])
				
		indexesOfRestrictionsReferenced=set()
		valuesTL=list()
		for i in range(len(at.parsed_tl_lexforms)):
			lexform = at.parsed_tl_lexforms[i]
			if featureName in lexform.get_categories():
				featureValue=lexform.get_tags_with_feature_names_as_dict()[featureName]
				valuesForThisLexform=list()
				
				slindexes=at.get_sl_words_aligned_with(i)
				
				if generalisationOptions.is_refToBiling():
					#first check aligned words
					for slindex in slindexes:		
						#first check bilingual dic. If no equivalency can be found, check Sl tags 
						if at.parsed_restrictions[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue or (at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue and not featureName in at.parsed_restrictions[slindex].get_tags_with_feature_names_as_dict()):
							valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_bidix(featureName,slindex))
							indexesOfRestrictionsReferenced.add(slindex)
						elif at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue:
							valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_sl_word(featureName,slindex))
					
						#if not, check other SL words
						if len(valuesForThisLexform) == 0:
							newslindexes= set(range(len(at.parsed_sl_lexforms))) - set(slindexes)
							for slindex in newslindexes:
								if at.parsed_restrictions[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue or (at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue and not featureName in at.parsed_restrictions[slindex].get_tags_with_feature_names_as_dict()):
									valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_bidix(featureName,slindex))
									indexesOfRestrictionsReferenced.add(slindex)
								elif at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue:
									valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_sl_word(featureName,slindex))
						
						#if not, and option is enabled, mantain value
						if len(valuesForThisLexform) == 0 and generalisationOptions.is_generaliseNonMatchingToo():
							valuesForThisLexform.append(featureValue)
				else:
					#First check whether value is shared with any aligned SL word
					for slindex in slindexes:
						if at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue:
							valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_sl_word(featureName,slindex))
					#if not, check other SL words
					if len(valuesForThisLexform) == 0:
						newslindexes= set(range(len(at.parsed_sl_lexforms))) - set(slindexes)
						for slindex in newslindexes:
							if at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue:
								valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_sl_word(featureName,slindex))					
			
				#if len(valuesForThisLexform) == 0:
				#	valuesTL.append([None])
				#else:
				
				#an empty list means that the lex form contains a tag from the feature name
				#but it can't be generalised
				#None is appended when a tag cannot be generalised but it is empty. In that case it is allowed
				if len(valuesForThisLexform) == 0 and is_empty_tag(featureValue):
					valuesTL.append([None])
				else:
					valuesTL.append(valuesForThisLexform)
			else:
				valuesTL.append([None])
		
		valuesRestrictions=list()
		for i in range(len(at.parsed_restrictions)):
			res=at.parsed_restrictions[i]
			sllex=at.parsed_sl_lexforms[i]
			#None means keep (don't modify anything)
			#True means remove
			#A string means: use that string
			values=[None]
			if generalisationOptions.is_refToBiling() and generalisationOptions.is_differentRestrictionOptions():
				if generalisationOptions.get_possibleValuesForRestrictions() == AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_ALL:
					if featureName in res.get_categories():
						#featureValue=res.get_tags_with_feature_names_as_dict()[featureName]
						#if it is GD, PD or ND, add option to ignore it
						#if its value has been referenced, add it too
						#if featureValue in ["GD","PD","ND"] or i in indexesOfRestrictionsReferenced:
						values.append(True)
					elif featureName in sllex.get_categories():
						featureValue=sllex.get_tags_with_feature_names_as_dict()[featureName]
						values.append(featureValue)
				elif generalisationOptions.get_possibleValuesForRestrictions() == AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_TBDETERMINED:
					if featureName in res.get_categories():
						values=[True]
						featureValue=res.get_tags_with_feature_names_as_dict()[featureName]
						if AT_LexicalTagsProcessor.is_to_be_determined_tag(featureValue):
							values.append(None)
				elif generalisationOptions.get_possibleValuesForRestrictions() == AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_TBDETERMINEDANDCHANGE:
					if featureName in res.get_categories():
						#remove restriction
						values=[True]
						featureValue=res.get_tags_with_feature_names_as_dict()[featureName]
						if AT_LexicalTagsProcessor.is_to_be_determined_tag(featureValue):
							#leave restriction
							values.append(None)
						else:
							#change or not change
							slfeatureValue=sllex.get_tags_with_feature_names_as_dict()[featureName]
							if slfeatureValue == featureValue:
								values.append(get_representation_of_restriction_not_changing(featureName))
							else:
								values.append(get_representation_of_restriction_changing(featureName))
						
				elif generalisationOptions.get_possibleValuesForRestrictions() == AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_TBDETERMINEDANDMF:
					if featureName in res.get_categories():
						values=[True]
						featureValue=res.get_tags_with_feature_names_as_dict()[featureName]
						if AT_LexicalTagsProcessor.is_to_be_determined_tag(featureValue) or AT_LexicalTagsProcessor.is_generator_of_to_be_determined_tag(featureValue):
							values.append(None)
					elif featureName in sllex.get_categories():
						featureValue=sllex.get_tags_with_feature_names_as_dict()[featureName]
						if AT_LexicalTagsProcessor.is_to_be_determined_tag(featureValue) or AT_LexicalTagsProcessor.is_generator_of_to_be_determined_tag(featureValue):
							values.append(featureValue)
				elif generalisationOptions.get_possibleValuesForRestrictions() == AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_TRIGGERINGCHANGE:
					if featureName in res.get_categories():
						values=[True]
			else:
				if generalisationOptions.is_addRestrictionsForEveryTag():
					if featureName in res.get_categories():
						values=[True]
					
			valuesRestrictions.append(values)
		
		newValuesForFeatures[featureName]=(valuesSL,valuesTL,valuesRestrictions)
		debug("Possible values for SL "+featureName+": "+str(valuesSL))
		debug("Possible values for TL "+featureName+": "+str(valuesTL))
		debug("Possible values for Restrictions "+featureName+": "+str(valuesRestrictions))
	
	#check whether the value of each sl attribute can be obtained in all TL words (or is empty)
	slAttributesNotGeneralisableOrEmpty=set()
	if not generalisationOptions.is_dontGeneraliseAllInstancesTogether():
		for featureName in sl_attribute_names:
			canBeObtainedInALlNonEmptyValues=True
			tlvalueLists=newValuesForFeatures[featureName][1]
			for mytlindex in range(len(at.parsed_tl_lexforms)):
				if featureName in at.parsed_tl_lexforms[mytlindex].get_tags_with_feature_names_as_dict():
					myvalue=at.parsed_tl_lexforms[mytlindex].get_tags_with_feature_names_as_dict()[featureName]
					if not is_empty_tag(myvalue):
						if len(tlvalueLists[mytlindex]) == 0:
							canBeObtainedInALlNonEmptyValues=False
							break
			if not canBeObtainedInALlNonEmptyValues:
				slAttributesNotGeneralisableOrEmpty.add(featureName)
	
	if generalisationOptions.is_calculateGeneralisableAttributesLikeInPaper():
		sl_attribute_names-=slAttributesNotGeneralisableOrEmpty
		attribute_names-=slAttributesNotGeneralisableOrEmpty
	
	debug("slAttributesNotGeneralisableOrEmpty:"+unicode(slAttributesNotGeneralisableOrEmpty).encode('utf-8'))
	debug("sl_attribute_names: "+unicode(sl_attribute_names).encode('utf-8'))
		
	#compute sets of attributes to be generalised
	if generalisationOptions.is_fromRightToLeft():
		#OUTDATED: We no longer use TSORT (see below)
		#use tsort to obtain an ordered list of attributes compatible with the
		#tags
		#arcs=list()
		#for lexform in at.parsed_sl_lexforms:
		#	listOfFeatureNames= [ pair.feature_name for pair in lexform.get_tags_with_feature_names() if pair.feature_name in attribute_names ]
		#	prev=U"__END__"
		#	for featureName in reversed(listOfFeatureNames):
		#		arcs.append((prev,featureName))
		#		prev=featureName
		#	arcs.append((prev,u"__START__"))
		#orderedFeatureNames=tsort.tsort(arcs)[1:-1]
		
		combinationsOfFeatureNames=list()
		
		candidateCombinations=powerset(list(sl_attribute_names))
		for candidate in candidateCombinations:
			attributesNotGeneralised=sl_attribute_names - set(candidate)
			
			#check whether exist any word with the form n.*.f.*
			existBannedWord=False
			for lexform in at.parsed_sl_lexforms:
				firstGeneralisedMatched=False
				for tagFeatureAndValue in lexform.get_tags_with_feature_names():
					if firstGeneralisedMatched and  tagFeatureAndValue.feature_name in attributesNotGeneralised:
						existBannedWord=True
						break
					if tagFeatureAndValue.feature_name in candidate:
						firstGeneralisedMatched=True
			
			if not existBannedWord:
				#if len(set(candidate) & slAttributesNotGeneralisableOrEmpty) == 0:
				if all(att not in slAttributesNotGeneralisableOrEmpty for att in candidate):
					combinationsOfFeatureNames.append(candidate)
				
		#combinationsOfFeatureNames=list()
		#for i in range(len(orderedFeatureNames)+1):
		#	featureNamesToGeneralise=orderedFeatureNames[:i]
		#	check whether exist any word with the form n.*.f.*
		#	existBannedWord=False
		#	for lexform in at.parsed_sl_lexforms:
		#		firstGeneralisedMatched=False
		#		for tagFeatureAndValue in lexform.get_tags_with_feature_names():
		#			if firstGeneralisedMatched and not tagFeatureAndValue.feature_name in featureNamesToGeneralise:
		#				existBannedWord=True
		#				break
		#			if tagFeatureAndValue.feature_name in featureNamesToGeneralise:
		#				firstGeneralisedMatched=True
		#	if existBannedWord:
		#		break
			
			#check whether the feature name can be generalised in every/any TL word
			#if i > 0:
			#	tlvalueLists=newValuesForFeatures[orderedFeatureNames[i-1]][1]
			#	tlwordswithnovalue=[ l for l in tlvalueLists if len(l)==0 ]
			#	tlwordswithvalue=[ l for l in tlvalueLists if len(l)>0 ]
			#	if generalisationOptions.is_dontGeneraliseAllInstancesTogether():
			#		if len(tlwordswithvalue) == 0:
			#			break
			#	else:
			#		if len(tlwordswithnovalue) > 0:
			#			break
			#	#TODO: esto tiene mala pinta
			#	#if len(l) == 0:
			#	#	break
			#combinationsOfFeatureNames.append(orderedFeatureNames[:i])
	else:
		candidateCombinations=powerset(list(sl_attribute_names))
		combinationsOfFeatureNames=list()
		for candidate in candidateCombinations:
			attributesNotGeneralised=sl_attribute_names - set(candidate)
			lexcats=set()
			for lexform in at.parsed_sl_lexforms:
				if lexform.get_pos() in generalisationOptions.get_count_attribute_changes():
					lexcats.add(lexform.get_pos())
			
			validCandidate=True
			
			for lexcat in lexcats:
				#check all pairs
				for generalisedAttr in candidate:
					if not validCandidate:
						break
					for nonGeneralisedAttr in attributesNotGeneralised:
						if generalisationOptions.get_count_attribute_changes()[lexcat][generalisedAttr] > generalisationOptions.get_count_attribute_changes()[lexcat][nonGeneralisedAttr]:
							validCandidate=False
							break

			if validCandidate:
				combinationsOfFeatureNames.append(candidate)

	previousGeneralisedLists=list()
	
	debug("Valid feature combinations: "+str(combinationsOfFeatureNames))
	
	#Generalising attribute
	#generalise the feature values
	for featureNamesToGeneralise in combinationsOfFeatureNames:
		optionsForEachFeature=list()
		
		debug("Generalising feature combination: "+str(featureNamesToGeneralise))
		
		#get list of options available for each feature
		for featureName in featureNamesToGeneralise:
			newValues=newValuesForFeatures[featureName]
			#SL list + TL list + Restriction list
			newValuesInSingleList=newValues[0]+newValues[1]
			optionsForThisFeature=combine_elements(newValuesInSingleList)
			optionsForEachFeature.append(optionsForThisFeature)
		
		#combine options for different features
		generalOptions=combine_elements(optionsForEachFeature)

		for option in generalOptions:
			featuresBidixReferencedByTlWords=list()
			for i in range(len(at.parsed_sl_lexforms)):
				featuresBidixReferencedByTlWords.append(set())
			
			debug("Obtained option for generalising tags:")
			#option is list of |featureNamesToGeneralise| elements
			#	each element of the list is the list of values for a feature
			generalisedAT=copy.deepcopy(at)
			for i in range(len(featureNamesToGeneralise)):
				featureName=featureNamesToGeneralise[i]
				newValues=option[i]
				slValues=newValues[:len(generalisedAT.parsed_sl_lexforms)]
				tlValues=newValues[len(generalisedAT.parsed_sl_lexforms):]
				debug(featureName+": SL="+str(slValues)+" TL="+str(tlValues))
				for j in range(len(slValues)):
					if slValues[j]:
						generalisedAT.parsed_sl_lexforms[j].set_tag_value_for_name(featureName,slValues[j])
				for j in range(len(tlValues)):
					if tlValues[j]:
						generalisedAT.parsed_tl_lexforms[j].set_tag_value_for_name(featureName,tlValues[j])
						parsedType,parsedCategory,referencedSlBidix = parse_special_tag(tlValues[j])
						if parsedType == AT_SpecialTagType.CHECK_BIDIX:
							featuresBidixReferencedByTlWords[referencedSlBidix].add(featureName)
			
			if generalisationOptions.is_refToBiling():
				#At this point, AT with generalised attributes
				#last step, remove restrictions
				debug("Computing restriction removal options")
				if generalisationOptions.is_differentRestrictionOptions() or generalisationOptions.is_addRestrictionsForEveryTag():
					lisfOfOptionsForEachFeature=list()
					for featureName in featureNamesToGeneralise:
						valuesForRestrictions=newValuesForFeatures[featureName][2]
						debug("Rest. options for "+featureName+": "+str(valuesForRestrictions))
						options=combine_elements(valuesForRestrictions)
						lisfOfOptionsForEachFeature.append(options)
					finalOptions=combine_elements(lisfOfOptionsForEachFeature)
					
					for finalOption in finalOptions:
						newAT=copy.deepcopy(generalisedAT)
						#finalOption object is a list. Each element represents a feature
						#each element is a list of |sllexforms| values. Each value if the value of the feature in each restriction
						for l in range(len(finalOption)):
							featureName=featureNamesToGeneralise[l]
							valuesForFeature=finalOption[l]
							for k in range(len(valuesForFeature)):
								valueForRestriction=valuesForFeature[k]
								if valueForRestriction != None:
									if valueForRestriction == True:
										#remove
										newAT.parsed_restrictions[k].remove_tag_from_category(featureName)
									else:
										#add
										newAT.parsed_restrictions[k].remove_tag_from_category(featureName)
										newAT.parsed_restrictions[k].append_tag(valueForRestriction)
							#if not generalisedAT.is_restriction_ending_in_empty_tag():
						if generalisationOptions.get_possibleValuesForRestrictions() == AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_TRIGGERINGCHANGE:
							newAT.set_afterwards_restrictions_from(at)
							
						debug("Obtained structural AT: "+str(newAT))
						debug("with afterwards restrictions: "+str(newAT.afterwards_restrictions))
						atsAfterGeneralisingAttributes.append(newAT)
								
				else:
					#removingRestrictionsOptions=list()
					#for i  in range(len(generalisedAT.parsed_restrictions)):
						#restriction=generalisedAT.parsed_restrictions[i]
						#debug("restriction "+str(i)+" featuresBidixReferencedByTlWords[i]:"+str(featuresBidixReferencedByTlWords[i]))
						#restriction.remove_longest_suffix(featuresBidixReferencedByTlWords[i])
						#restriction.remove_longest_suffix(featureNamesToGeneralise)
						#if not generalisedAT.is_restriction_ending_in_empty_tag():
					atsAfterGeneralisingAttributes.append(generalisedAT)
			else:
				if not generalisedAT.is_restriction_ending_in_empty_tag():
					atsAfterGeneralisingAttributes.append(generalisedAT)
	return atsAfterGeneralisingAttributes


def AlignmentTemplate_generate_all_lexical_generalisations(at,lemmassl,lemmastl,tllemmas_from_dic,unlexicaliseSLunaligned=False):
	lexicalisedATs=list()
	
	#take this into account in the future: and not lemmassl[i].startswith(u"_")
	indexesOfUnLexicalisableWords=list()
	unlexicalisableTLforUnlexicalisableWords=list()
	for i in range(len(at.parsed_sl_lexforms)):	
		#check if any aligned TL word matches dictionary translation
		alignedTLWords=[ al[1] for al in at.alignments if al[0] == i]
		matchingDictionaryTranslations=[ tli for tli in alignedTLWords if lowercase_first_letter(lemmastl[tli]) == lowercase_first_letter(tllemmas_from_dic[i])  ]
		if len(matchingDictionaryTranslations) > 0 or (len(alignedTLWords)==0 and unlexicaliseSLunaligned):
			indexesOfUnLexicalisableWords.append(i)
			unlexicalisableTLforUnlexicalisableWords.append(matchingDictionaryTranslations)
	optionsToCombine=list()
	for j in range(len(indexesOfUnLexicalisableWords)):
		optionsToCombine.append([True,False])
	lexicalisationCombinations=combine_elements(optionsToCombine)
	
	for lexicalisationCombination in lexicalisationCombinations:
		lexicalisedAt=copy.deepcopy(at)
		unlexicalisedIndexes=list()
		for i in range(len(lexicalisationCombination)):
			if lexicalisationCombination[i]:
				unlexicalisedIndexes.append(indexesOfUnLexicalisableWords[i])
		
		lexicalisedAt.lexicalise_sl_withexceptions(unlexicalisedIndexes,lemmassl)
		
		unlexicalisedtlset=set()
		for slindex in unlexicalisedIndexes:
			unlexicalisedtlset.update(unlexicalisableTLforUnlexicalisableWords[indexesOfUnLexicalisableWords.index(slindex)])
		lexicalisedAt.lexicalise_tl_withexceptions(unlexicalisedtlset,lemmastl)	
		lexicalisedATs.append(lexicalisedAt)
	
	return lexicalisedATs	
	
def AlignmentTemplate_generate_all_lexical_generalisations_and_add_them(at,originalat,lemmassl,lemmastl,tllemmas_from_dic, finalAlignmentTemplates,idAt, generalisationOptions):
	
	originalFreq=at.freq
	bilphrase=copy.deepcopy(originalat)
	bilphrase.set_lemmas(lemmassl,lemmastl)
	bilphrase.tl_lemmas_from_dictionary=tllemmas_from_dic
	
	atsAfterAutoUnalign=list()
	options=at.get_unalignment_options_for_multiple_aligned_tl_words()
	if DEBUG:
		print >> sys.stderr, "Unalignment alternatives: "+str(options)
	for option in options:
		if DEBUG:
			print >>sys.stderr, "Removing these alignments: "+str(option)
		
		atcopy=copy.deepcopy(at)
		for opcomponent in option:
			atcopy.remove_alignments(opcomponent)
		atcopy.alignments.sort()
		atsAfterAutoUnalign.append(atcopy)
	
	lexicalisedATs=list()
	for at in atsAfterAutoUnalign:
		everythingLexicalised=copy.deepcopy(at)
		everythingLexicalised.lexicalise_all(lemmassl,lemmastl)
		lexicalisedATs.append(everythingLexicalised)		
		
		#take this into acount in the future: and not lemmassl[i].startswith(u"_")
		indexesOfUnLexicalisableWords=list()
		unlexicalisableTLforUnlexicalisableWords=list()
		for i in range(len(at.parsed_restrictions)):
			if not at.parsed_restrictions[i].is_special() and not at.parsed_sl_lexforms[i].has_lemma():
				#check if any aligned TL word matches dictionary translation
				alignedTLWords=[ al[1] for al in at.alignments if al[0] == i]
				matchingDictionaryTranslations=[ tli for tli in alignedTLWords if lowercase_first_letter(lemmastl[tli]) == lowercase_first_letter(tllemmas_from_dic[i])  ]
				if len(matchingDictionaryTranslations) > 0:
					indexesOfUnLexicalisableWords.append(i)
					unlexicalisableTLforUnlexicalisableWords.append(matchingDictionaryTranslations)
		optionsToCombine=list()
		for j in range(len(indexesOfUnLexicalisableWords)):
			optionsToCombine.append([True,False])
		lexicalisationCombinations=combine_elements(optionsToCombine)
		
		for lexicalisationCombination in lexicalisationCombinations:
			lexicalisedAt=copy.deepcopy(at)
			unlexicalisedIndexes=list()
			for i in range(len(lexicalisationCombination)):
				if lexicalisationCombination[i]:
					unlexicalisedIndexes.append(indexesOfUnLexicalisableWords[i])
			
			lexicalisedAt.lexicalise_sl_withexceptions(unlexicalisedIndexes,lemmassl)
			
			unlexicalisedtlset=set()
			for slindex in unlexicalisedIndexes:
				unlexicalisedtlset.update(unlexicalisableTLforUnlexicalisableWords[indexesOfUnLexicalisableWords.index(slindex)])
			lexicalisedAt.lexicalise_tl_withexceptions(unlexicalisedtlset,lemmastl)	
			lexicalisedATs.append(lexicalisedAt)
		
		if DEBUG:
			print >>sys.stderr, "Lexicalised ATs: ("+str(len(lexicalisedATs))+") : "+str(lexicalisedATs)
	
	for finalGeneralisedAT in lexicalisedATs:		
		#An AT is obtained after running all the transformations
		#Check whether reproduces the bilingual phrase and add it
		debug("Obtained AT: "+str(finalGeneralisedAT))
		if not finalAlignmentTemplates.is_in_set(finalGeneralisedAT):
			debug("is NOT in set")
			idAt+=1
			finalGeneralisedAT.id=idAt
			finalAlignmentTemplates.add(finalGeneralisedAT)
	return idAt

#THIS METHOD IS NEVER USED
def AlignmentTemplate_generate_all_rich_generalisations_and_add_them(at,lemmassl,lemmastl,tllemmas_from_dic, finalAlignmentTemplates,idAt, generalisationOptions):
	if DEBUG:
		print >> sys.stderr, "Starting from id: "+str(idAt)
	
	originalFreq=at.freq
	bilphrase=copy.deepcopy(at)
	bilphrase.set_lemmas(lemmassl,lemmastl)
	bilphrase.tl_lemmas_from_dictionary=tllemmas_from_dic
	
	atList=set()
	
	atList.add(at)
	atsAfterGeneralisingAttributes=list()
	#Generalise attributes:
	for at in atList:
		# compute generalisation stuff!
		attribute_names=set()
		for lexform in at.parsed_sl_lexforms:
			attribute_names.update(lexform.get_tags_with_feature_names_as_dict().keys())
		for lexform in at.parsed_tl_lexforms:
			attribute_names.update(lexform.get_tags_with_feature_names_as_dict().keys())
		
		#catgories present in restrictions not generalised if option is enabled
		if not generalisationOptions.is_refToBiling():
			for res in at.parsed_restrictions:
				attribute_names-=set(res.get_tags_with_feature_names_as_dict().keys())
			
		
		debug("Generalising attributes for AT: "+str(at))		
		#for each feature name, compute its possible generalisation values
		newValuesForFeatures=dict()
		for featureName in attribute_names:
			valuesSL=list()
			for lexform in at.parsed_sl_lexforms:
				if featureName in lexform.get_categories():
					valuesSL.append([get_representation_of_sl_generalised_tag(featureName)])
				else:
					valuesSL.append([None])
					
			indexesOfRestrictionsReferenced=set()
			valuesTL=list()
			for i in range(len(at.parsed_tl_lexforms)):
				lexform = at.parsed_tl_lexforms[i]
				if featureName in lexform.get_categories():
					featureValue=lexform.get_tags_with_feature_names_as_dict()[featureName]
					valuesForThisLexform=list()
					
					slindexes=at.get_sl_words_aligned_with(i)
					
					if generalisationOptions.is_refToBiling():
						#first check aligned words
						for slindex in slindexes:		
							#first check bilingual dic. If no equivalency can be found, check Sl tags 
							if at.parsed_restrictions[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue or (at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue and not featureName in at.parsed_restrictions[slindex].get_tags_with_feature_names_as_dict()):
								valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_bidix(featureName,slindex))
								indexesOfRestrictionsReferenced.add(slindex)
							elif at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue:
								valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_sl_word(featureName,slindex))
						
							#if not, check other SL words
							if len(valuesForThisLexform) == 0:
								newslindexes= set(range(len(at.parsed_sl_lexforms))) - set(slindexes)
								for slindex in newslindexes:
									if at.parsed_restrictions[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue or (at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue and not featureName in at.parsed_restrictions[slindex].get_tags_with_feature_names_as_dict()):
										valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_bidix(featureName,slindex))
										indexesOfRestrictionsReferenced.add(slindex)
									elif at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue:
										valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_sl_word(featureName,slindex))
					else:
						#First check whether value is shared with any aligned SL word
						for slindex in slindexes:
							if at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue:
								valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_sl_word(featureName,slindex))
						#if not, check other SL words
						if len(valuesForThisLexform) == 0:
							newslindexes= set(range(len(at.parsed_sl_lexforms))) - set(slindexes)
							for slindex in newslindexes:
								if at.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict().get(featureName)==featureValue:
									valuesForThisLexform.append(get_representation_of_tl_generalised_tag_from_sl_word(featureName,slindex))					
				
					#if len(valuesForThisLexform) == 0:
					#	valuesTL.append([None])
					#else:
					
					#an empty list means that the lex form contains a tag from the feature name
					#but it can't be generalised
					#None is appended when a tag cannot be generalised but it is empty. In that case it is allowed
					if len(valuesForThisLexform) == 0 and is_empty_tag(featureValue):
						valuesTL.append([None])
					else:
						valuesTL.append(valuesForThisLexform)
				else:
					valuesTL.append([None])
			
			valuesRestrictions=list()
			for i in range(len(at.parsed_restrictions)):
				res=at.parsed_restrictions[i]
				sllex=at.parsed_sl_lexforms[i]
				#None means keep (don't modify anything)
				#True means remove
				#A string means: use that string
				values=[None]
				if generalisationOptions.is_refToBiling() and generalisationOptions.is_differentRestrictionOptions():
					if featureName in res.get_categories():
						#featureValue=res.get_tags_with_feature_names_as_dict()[featureName]
						#if it is GD, PD or ND, add option to ignore it
						#if its value has been referenced, add it too
						#if featureValue in ["GD","PD","ND"] or i in indexesOfRestrictionsReferenced:
						values.append(True)
					elif featureName in sllex.get_categories():
						featureValue=sllex.get_tags_with_feature_names_as_dict()[featureName]
						values.append(featureValue)
						
				valuesRestrictions.append(values)
			
			newValuesForFeatures[featureName]=(valuesSL,valuesTL,valuesRestrictions)
			debug("Possible values for SL "+featureName+": "+str(valuesSL))
			debug("Possible values for TL "+featureName+": "+str(valuesTL))
			debug("Possible values for Restrictions "+featureName+": "+str(valuesRestrictions))
		
		#compute sets of attributes to be generalised
		if generalisationOptions.is_fromRightToLeft():
			#use tsort to obtain an ordered list of attributes compatible with the
			#tags
			arcs=list()
			for lexform in at.parsed_sl_lexforms:
				listOfFeatureNames= [ pair.feature_name for pair in lexform.get_tags_with_feature_names() if pair.feature_name in attribute_names ]
				prev=U"__END__"
				for featureName in reversed(listOfFeatureNames):
					arcs.append((prev,featureName))
					prev=featureName
				arcs.append((prev,u"__START__"))
			orderedFeatureNames=tsort.tsort(arcs)[1:-1]
			combinationsOfFeatureNames=list()
			for i in range(len(orderedFeatureNames)+1):
				
				featureNamesToGeneralise=orderedFeatureNames[:i]
				
				#check whether exist any word with the form n.*.f.*
				existBannedWord=False
				for lexform in at.parsed_sl_lexforms:
					firstGeneralisedMatched=False
					for tagFeatureAndValue in lexform.get_tags_with_feature_names():
						if firstGeneralisedMatched and not tagFeatureAndValue.feature_name in featureNamesToGeneralise:
							existBannedWord=True
							break
						if tagFeatureAndValue.feature_name in featureNamesToGeneralise:
							firstGeneralisedMatched=True
				
				if existBannedWord:
					break
				
				#check whether the feature name can be generalised in every TL word
				if i > 0:
					tlvalueLists=newValuesForFeatures[orderedFeatureNames[i-1]][1]
					tlwordswithnovalue=[ l for l in tlvalueLists if len(l)==0 ]
					if len(tlwordswithnovalue) > 0:
						break
					#TODO: esto tiene mala pinta
					#if len(l) == 0:
					#	break
				combinationsOfFeatureNames.append(orderedFeatureNames[:i])
		else:
			combinationsOfFeatureNames=powerset(list(attribute_names))
	
		previousGeneralisedLists=list()
		
		#Generalising attribute
		#generalise the feature values
		for featureNamesToGeneralise in combinationsOfFeatureNames:
			optionsForEachFeature=list()
			
			debug("Generalising feature combination: "+str(featureNamesToGeneralise))
			
			#get list of options available for each feature
			for featureName in featureNamesToGeneralise:
				newValues=newValuesForFeatures[featureName]
				#SL list + TL list + Restriction list
				newValuesInSingleList=newValues[0]+newValues[1]
				optionsForThisFeature=combine_elements(newValuesInSingleList)
				optionsForEachFeature.append(optionsForThisFeature)
			
			#combine options for different features
			generalOptions=combine_elements(optionsForEachFeature)

			for option in generalOptions:
				featuresBidixReferencedByTlWords=list()
				for i in range(len(at.parsed_sl_lexforms)):
					featuresBidixReferencedByTlWords.append(set())
				
				debug("Obtained option for generalising tags:")
				#option is list of |featureNamesToGeneralise| elements
				#	each element of the list is the list of values for a feature
				generalisedAT=copy.deepcopy(at)
				for i in range(len(featureNamesToGeneralise)):
					featureName=featureNamesToGeneralise[i]
					newValues=option[i]
					slValues=newValues[:len(generalisedAT.parsed_sl_lexforms)]
					tlValues=newValues[len(generalisedAT.parsed_sl_lexforms):]
					debug(featureName+": SL="+str(slValues)+" TL="+str(tlValues))
					for j in range(len(slValues)):
						if slValues[j]:
							generalisedAT.parsed_sl_lexforms[j].set_tag_value_for_name(featureName,slValues[j])
					for j in range(len(tlValues)):
						if tlValues[j]:
							generalisedAT.parsed_tl_lexforms[j].set_tag_value_for_name(featureName,tlValues[j])
							parsedType,parsedCategory,referencedSlBidix = parse_special_tag(tlValues[j])
							if parsedType == AT_SpecialTagType.CHECK_BIDIX:
								featuresBidixReferencedByTlWords[referencedSlBidix].add(featureName)
				
				if generalisationOptions.is_refToBiling():
					#At this point, AT with generalised attributes
					#last step, remove restrictions
					debug("Computing restriction removal options")
					if generalisationOptions.is_differentRestrictionOptions():
						for featureName in featureNamesToGeneralise:
							valuesForRestrictions=newValuesForFeatures[featureName][2]
							options=combine_elements(valuesForRestrictions)
							for option in options:
								newAT=copy.deepcopy(generalisedAT)
								for k in range(len(option)):
									valueForRestriction=option[k]
									if valueForRestriction != None:
										if valueForRestriction == True:
											#remove
											newAT.parsed_restrictions[k].remove_tag_from_category(featureName)
										else:
											#add
											newAT.parsed_restrictions[k].append_tag(valueForRestriction)
								if not generalisedAT.is_restriction_ending_in_empty_tag():
									atsAfterGeneralisingAttributes.append(generalisedAT)
									
					else:
						#removingRestrictionsOptions=list()
						for i  in range(len(generalisedAT.parsed_restrictions)):
							restriction=generalisedAT.parsed_restrictions[i]
							#debug("restriction "+str(i)+" featuresBidixReferencedByTlWords[i]:"+str(featuresBidixReferencedByTlWords[i]))
							#restriction.remove_longest_suffix(featuresBidixReferencedByTlWords[i])
							restriction.remove_longest_suffix(featureNamesToGeneralise)
							if not generalisedAT.is_restriction_ending_in_empty_tag():
								atsAfterGeneralisingAttributes.append(generalisedAT)
				else:
					if not generalisedAT.is_restriction_ending_in_empty_tag():
						atsAfterGeneralisingAttributes.append(generalisedAT)

	#TODO: mover autoUnalign al final, como en el paper
	atsAfterAutoUnalign=list()
	#Auto unalign: 
	#for at in atFromFirstStep:
	for at in atsAfterGeneralisingAttributes:
		options=at.get_unalignment_options_for_multiple_aligned_tl_words()
		if DEBUG:
			print >> sys.stderr, "Unalignment alternatives: "+str(options)
		for option in options:
			
			if DEBUG:
				print >>sys.stderr, "Removing these alignments: "+str(option)
			
			atcopy=copy.deepcopy(at)
			for opcomponent in option:
				atcopy.remove_alignments(opcomponent)
			atcopy.alignments.sort()
			atsAfterAutoUnalign.append(atcopy)
	
	lexicalisedATs=list()
	for at in atsAfterAutoUnalign:
		everythingLexicalised=copy.deepcopy(at)
		everythingLexicalised.lexicalise_all(lemmassl,lemmastl)
		lexicalisedATs.append(everythingLexicalised)		
		
		#take this into acount in the future: and not lemmassl[i].startswith(u"_")
		indexesOfUnLexicalisableWords=list()
		unlexicalisableTLforUnlexicalisableWords=list()
		for i in range(len(at.parsed_restrictions)):
			if not at.parsed_restrictions[i].is_special() and not at.parsed_sl_lexforms[i].has_lemma():
				#check if any aligned TL word matches dictionary translation
				alignedTLWords=[ al[1] for al in at.alignments if al[0] == i]
				matchingDictionaryTranslations=[ tli for tli in alignedTLWords if lowercase_first_letter(lemmastl[tli]) == lowercase_first_letter(tllemmas_from_dic[i])  ]
				if len(matchingDictionaryTranslations) > 0:
					indexesOfUnLexicalisableWords.append(i)
					unlexicalisableTLforUnlexicalisableWords.append(matchingDictionaryTranslations)
		optionsToCombine=list()
		for j in range(len(indexesOfUnLexicalisableWords)):
			optionsToCombine.append([True,False])
		lexicalisationCombinations=combine_elements(optionsToCombine)
		
		for lexicalisationCombination in lexicalisationCombinations:
			lexicalisedAt=copy.deepcopy(at)
			unlexicalisedIndexes=list()
			for i in range(len(lexicalisationCombination)):
				if lexicalisationCombination[i]:
					unlexicalisedIndexes.append(indexesOfUnLexicalisableWords[i])
			
			lexicalisedAt.lexicalise_sl_withexceptions(unlexicalisedIndexes,lemmassl)
			
			#TODO: revisar esto, creo que no hace falta el segundo combine_elements
			unlexicalisationTLOptions=[ unlexicalisableTLforUnlexicalisableWords[indexesOfUnLexicalisableWords.index(slindex)] for slindex in unlexicalisedIndexes ]
			for unlexicalisationTLOption in combine_elements(unlexicalisationTLOptions):
				debug("option for unlexicalising TL: "+str(unlexicalisationTLOption))
				lexicalisedATTL=copy.deepcopy(lexicalisedAt)
				lexicalisedATTL.lexicalise_tl_withexceptions(unlexicalisationTLOption,lemmastl)
				lexicalisedATs.append(lexicalisedATTL)
				debug("resulting AT: "+str(lexicalisedATTL))
		
		if DEBUG:
			print >>sys.stderr, "Lexicalised ATs: ("+str(len(lexicalisedATs))+") : "+str(lexicalisedATs)
	
	for finalGeneralisedAT in lexicalisedATs:		
		#An AT is obtained after running all the transformations
		#Check whether reproduces the bilingual phrase and add it
		debug("Obtained AT: "+str(finalGeneralisedAT))
		if finalGeneralisedAT.is_bilphrase_reproducible(bilphrase):
			if finalAlignmentTemplates.is_in_set(finalGeneralisedAT):
				debug("IS reproducible and IS in set")
				atInSet=finalAlignmentTemplates.is_in_set(finalGeneralisedAT,returnAt=True)
				atInSet.increase_freq(originalFreq)
			else:
				debug("IS reproducible and NOT is in set")
				idAt+=1
				finalGeneralisedAT.id=idAt
				finalAlignmentTemplates.add(finalGeneralisedAT)
		else:
			debug("NOT reproducible")
	return idAt

def AlignmentTemplate_generate_all_generalisations_and_add_them(at,lemmassl,lemmastl,tllemmas_from_dic, finalAlignmentTemplates,idAt, subsetsGraph,RestrictionsRestrictGeneralisation,AgreementsRestrictGeneralisation,tagGroupsWhichCanBeGeneralisedWhenEmpty,tagGroupsWhichCanBeGeneralisedWhenEmptySL):
	#DEBUG=False
	
	computeSubsetGraph=False
	
	originalFreq=at.freq
	
	allGeneralisations=list()
	
	bilphrase=copy.deepcopy(at)
	bilphrase.lexicalise_all(lemmassl,lemmastl)
	bilphrase.tl_lemmas_from_dictionary=tllemmas_from_dic
	
	#Auto-align
	atList=set()
	atFromFirstStep=list()
	options=at.get_alignment_options_for_unaligned_words()
	for option in options:
		atcopy=copy.deepcopy(at)
		atcopy.add_alignments(option)
		atcopy.alignments.sort()
		atFromFirstStep.append(atcopy)
	
	if DEBUG:
		print >> sys.stderr, "Alignment templates after auto-align:"
		print >> sys.stderr, atFromFirstStep
	
	#Auto unalign
	for at in atFromFirstStep:
		options=at.get_unalignment_options_for_multiple_aligned_tl_words()
		if DEBUG:
			print >> sys.stderr, "Unalignment alternatives: "+str(options)
		for option in options:
			
			if DEBUG:
				print >>sys.stderr, "Removing these alignments: "+str(option)
			
			atcopy=copy.deepcopy(at)
			for opcomponent in option:
				atcopy.remove_alignments(opcomponent)
			atcopy.alignments.sort()
			atList.add(atcopy)

	#Lexicalise
	for at in atList:
		if DEBUG:
			print >> sys.stderr, "Computing lexicalisation alternatives for: "+str(at)
		lexicalisedATs=list()
		indexesOfLexicalisableWords=list()
		for i in range(len(at.restrictions)):
			if at.restrictions[i]!=u"__CLOSEWORD__" and lemmassl[i]!=u"__NONLEXICALIZABLE__" and at.sl_lexforms[i].startswith(u"<"):
				indexesOfLexicalisableWords.append(i)
		optionsToCombine=list()
		for j in range(len(indexesOfLexicalisableWords)):
			optionsToCombine.append([True,False])
		lexicalisationCombinations=combine_elements(optionsToCombine)
		
		for lexicalisationCombination in lexicalisationCombinations:
			lexicalisedAt=copy.deepcopy(at)
			lexicalisedIndexes=list()
			for i in range(len(lexicalisationCombination)):
				if lexicalisationCombination[i]:
					lexicalisedIndexes.append(indexesOfLexicalisableWords[i])
			
			lexicalisedAt.lexicalise(lexicalisedIndexes,lemmassl,lemmastl)
			
			if DEBUG:
				print >> sys.stderr, "SL lexicalisation combination: "+ str(lexicalisationCombination)
				print >> sys.stderr, str(lexicalisedAt)
				sys.stderr.write("Is reproducible?: ")
			if lexicalisedAt.is_bilphrase_reproducible(bilphrase):
				if DEBUG:
					print >>sys.stderr, "Yes"
				lexicalisedATs.append(lexicalisedAt)
			else:
				if DEBUG:
					print >>sys.stderr, "No"
			
			tllexicalisationAlternatives=lexicalisedAt.compute_alternatives_for_tl_lexicalisations()
			if DEBUG:
				print >> sys.stderr, str(len(tllexicalisationAlternatives))+" TL lex alternatives"
			for tllexicalisationAlternative in tllexicalisationAlternatives:
				if DEBUG:
					print >> sys.stderr, "TL lexicalisation alt: "+ str(tllexicalisationAlternative)
				tlLexicalisedAt=copy.deepcopy(lexicalisedAt)
				tlLexicalisedAt.lexicalise_tl(tllexicalisationAlternative,lemmastl)
				if DEBUG:
					print >> sys.stderr, str(tlLexicalisedAt)
					sys.stderr.write("Is reproducible?: ")
				if tlLexicalisedAt.is_bilphrase_reproducible(bilphrase):
					lexicalisedATs.append(tlLexicalisedAt)
					if DEBUG:
						print >>sys.stderr, "Yes"
				else:
					if DEBUG:
						print >>sys.stderr, "No"
		
		if DEBUG:
			print >>sys.stderr, "Lexicalised ATs: ("+str(len(lexicalisedATs))+") : "+str(lexicalisedATs)
		
		previousGeneralisedLists=list()
		
		#Compute which ATs are subsets of others
		#arc from subset to superset
		subsets=list()
		for i in range(len(lexicalisedATs)):
			for j in range(len(lexicalisedATs)):
				if i!=j:
					if lexicalisedATs[i].is_subset_of_this(lexicalisedATs[j]) and not lexicalisedATs[j].is_subset_of_this(lexicalisedATs[i]):
						subsets.append((j,i))
		
		#Generalise ignoring right side and add data to subset graph
		generalisedFullATs=list()
		generalisedFullATs.extend(lexicalisedATs)
		prevGeneralisedFullATs=list()
		
		if DEBUG:
			print >> sys.stderr, "generalising left sides to obtain subset graph:"
		
		while len(generalisedFullATs) > 0 and computeSubsetGraph:
			#subsetGraph contains arcs from supersets to subsets
			for subset in subsets:
				if DEBUG:
					print >> sys.stderr, "adding "+generalisedFullATs[subset[1]].get_sllex_and_restrictions_str().encode('utf-8')+" -> "+generalisedFullATs[subset[0]].get_sllex_and_restrictions_str().encode('utf-8')
				subsetsGraph.add(generalisedFullATs[subset[1]].get_sllex_and_restrictions_str(),generalisedFullATs[subset[0]].get_sllex_and_restrictions_str())
			if len(prevGeneralisedFullATs) > 0:
				for i in range(len(generalisedFullATs)):
					if DEBUG:
						print >> sys.stderr, "adding "+generalisedFullATs[i].get_sllex_and_restrictions_str().encode('utf-8')+" -> "+prevGeneralisedFullATs[i].get_sllex_and_restrictions_str().encode('utf-8')
					subsetsGraph.add(generalisedFullATs[i].get_sllex_and_restrictions_str(),prevGeneralisedFullATs[i].get_sllex_and_restrictions_str())
			newGeneralisedFullAts=list()
			for at in generalisedFullATs:
				atcopy=copy.deepcopy(at)
				#bla bla
				if atcopy.generalise(AT_LexicalTagsProcessor.taggroups,False,False,tagGroupsWhichCanBeGeneralisedWhenEmpty,tagGroupsWhichCanBeGeneralisedWhenEmptySL):
					newGeneralisedFullAts.append(atcopy)
			if len(newGeneralisedFullAts) == len(generalisedFullATs):
				prevGeneralisedFullATs=generalisedFullATs
				generalisedFullATs=newGeneralisedFullAts
			else:
				generalisedFullATs=[]
		if DEBUG:
			print >> sys.stderr, "end generalising left sides to obtain subset graph"
		
		#Generalise actual alignment templates
		while len(lexicalisedATs) > 0:
			addedInThisIteration=list()
			for i in range(len(lexicalisedATs)):
				particularLexicalisationAt=lexicalisedATs[i]
				if finalAlignmentTemplates.is_in_set(particularLexicalisationAt):
					lexicalisedATs[i]=finalAlignmentTemplates.is_in_set(particularLexicalisationAt,returnAt=True)
					lexicalisedATs[i].increase_freq(originalFreq)
					addedInThisIteration.append(False)
					if len(previousGeneralisedLists) > 0:
						previousGeneralisedLists[-1][i].parent=lexicalisedATs[i]
				else:
					idAt+=1
					particularLexicalisationAt.id=idAt
					finalAlignmentTemplates.add(particularLexicalisationAt)
					addedInThisIteration.append(True)
			
			if DEBUG:
				print >> sys.stderr, "Subsets: "+str(subsets)
				print >> sys.stderr, "len(lexicalisedATs): "+str(len(lexicalisedATs))
			
			if False:
				#add pointers to ats which are subsets
				for subset in subsets:
					if DEBUG:
						print >> sys.stderr, "subset: "+str(subset)
						print >> sys.stderr, "subset[0]: "+str(subset[0])
						print >> sys.stderr, "subset[1]: "+str(subset[1])
						print >> sys.stderr, lexicalisedATs[subset[1]]
						print >> sys.stderr, lexicalisedATs[subset[0]]
					
					lexicalisedATs[subset[1]].atswhicharesubsetpointers.add(lexicalisedATs[subset[0]])		
				#add pointers from previous levels
				for prevLevelAts in previousGeneralisedLists:
					for i in range(len(lexicalisedATs)):
						lexicalisedATs[i].atswhicharesubsetpointers.add(prevLevelAts[i])
					for subset in subsets:
						lexicalisedATs[subset[1]].atswhicharesubsetpointers.add(prevLevelAts[subset[0]])
			
			#add pointers to ats which are subsets
			#Done before, generalising only the left side
			if False:
				for subset in subsets:
					subsetsGraph.add(lexicalisedATs[subset[1]].get_sllex_and_restrictions_str(),lexicalisedATs[subset[0]].get_sllex_and_restrictions_str())
				if len(previousGeneralisedLists) > 0:
					for i in range(len(lexicalisedATs)):
						subsetsGraph.add(lexicalisedATs[i].get_sllex_and_restrictions_str(),previousGeneralisedLists[-1][i].get_sllex_and_restrictions_str())
			
			#Generalise
			lexicalisedAtsGeneralised=list()
			for i in range(len(lexicalisedATs)):
				particularLexicalisationAt=lexicalisedATs[i]
				if addedInThisIteration[i]==False:
					#seguir puntero
					if particularLexicalisationAt.parent:
						lexicalisedAtsGeneralised.append(particularLexicalisationAt.parent)
					
				else: #(lo acabo de añadir)
					#copiar y generalizar
					
					#atswhicharesubsetpointers ya no se usa. Tenemos grafo
					#subsetpointers=particularLexicalisationAt.atswhicharesubsetpointers
					#particularLexicalisationAt.atswhicharesubsetpointers=set()
					
					atgeneralised=copy.deepcopy(particularLexicalisationAt)
					
					if atgeneralised.generalise(RestrictionsRestrictGeneralisation,AgreementsRestrictGeneralisation,tagGroupsWhichCanBeGeneralisedWhenEmpty,tagGroupsWhichCanBeGeneralisedWhenEmptySL):
						lexicalisedAtsGeneralised.append(atgeneralised)
						#cuidado con el parent cuando añado el at generalizado y ya existe
						#Se tiene en cuenta más arriba 
						particularLexicalisationAt.parent=atgeneralised
					
			if len(lexicalisedAtsGeneralised) == len(lexicalisedATs):
				previousGeneralisedLists.append(lexicalisedATs)
				lexicalisedATs=lexicalisedAtsGeneralised
			else:
				lexicalisedATs=list()
				if len(lexicalisedAtsGeneralised) > 0:
					print >> sys.stderr, "WARNING: All the alignment templates have not been generalised at the same time"
	
	if DEBUG:
		print >> sys.stderr, "Subsets graph after adding the ATs:"
		print >> sys.stderr, "Dict:"
		for pair in subsetsGraph.idsDict.items():
			print >> sys.stderr, pair
		for pair in subsetsGraph.arcs:
			print >> sys.stderr, pair
	
	return idAt


			

class BilingualSequenceLexTags(object):
	
	WILDCARD=u"*"
	
	UNALIGNED_SIDE_BOTH=0
	UNALIGNED_SIDE_LEFT=1
	UNALIGNED_SIDE_RIGHT=2
	
	
	def __init__(self):
		self.slseq=[]
		self.tlseq=[]
	
	def load_from_at(self,at,unalignedEdgesBecomeWildcards=False,side=None):
		if side==None:
			side=BilingualSequenceLexTags.UNALIGNED_SIDE_BOTH
		if not unalignedEdgesBecomeWildcards:
			for l in at.parsed_sl_lexforms:
				self.slseq.append(unicode(AT_LexicalForm.create_without_lemma(l)))
			for l in at.parsed_tl_lexforms:
				self.tlseq.append(unicode(AT_LexicalForm.create_without_lemma(l)))
		else:
			for i in range(at.get_first_aligned_sl_word()):
				if side==BilingualSequenceLexTags.UNALIGNED_SIDE_BOTH or side==BilingualSequenceLexTags.UNALIGNED_SIDE_LEFT: 
					self.slseq.append(BilingualSequenceLexTags.WILDCARD)
				else:
					self.slseq.append(unicode(AT_LexicalForm.create_without_lemma(at.parsed_sl_lexforms[i])))
			for i in range(at.get_first_aligned_sl_word(),at.get_last_aligned_sl_word()+1):
				self.slseq.append(unicode(AT_LexicalForm.create_without_lemma(at.parsed_sl_lexforms[i])))
			for i in range(at.get_last_aligned_sl_word()+1,len(at.parsed_sl_lexforms)):
				if side==BilingualSequenceLexTags.UNALIGNED_SIDE_BOTH or side==BilingualSequenceLexTags.UNALIGNED_SIDE_RIGHT:
					self.slseq.append(BilingualSequenceLexTags.WILDCARD)
				else:
					self.slseq.append(unicode(AT_LexicalForm.create_without_lemma(at.parsed_sl_lexforms[i])))
			
			for i in range(at.get_first_aligned_tl_word()):
				if side==BilingualSequenceLexTags.UNALIGNED_SIDE_BOTH or side==BilingualSequenceLexTags.UNALIGNED_SIDE_LEFT:
					self.tlseq.append(BilingualSequenceLexTags.WILDCARD)
				else:
					self.tlseq.append(unicode(AT_LexicalForm.create_without_lemma(at.parsed_tl_lexforms[i])))
			for i in range(at.get_first_aligned_tl_word(),at.get_last_aligned_tl_word()+1):
				self.tlseq.append(unicode(AT_LexicalForm.create_without_lemma(at.parsed_tl_lexforms[i])))
			for i in range(at.get_last_aligned_tl_word()+1,len(at.parsed_tl_lexforms)):
				if side==BilingualSequenceLexTags.UNALIGNED_SIDE_BOTH or side==BilingualSequenceLexTags.UNALIGNED_SIDE_RIGHT:
					self.tlseq.append(BilingualSequenceLexTags.WILDCARD)
				else:
					self.tlseq.append(unicode(AT_LexicalForm.create_without_lemma(at.parsed_tl_lexforms[i])))
	
	def sub(self,slStart,sllen,tlStart,tllen):
		bsltret=BilingualSequenceLexTags()
		for i in xrange(slStart,slStart+sllen):
			bsltret.slseq.append(self.slseq[i])
		for i in xrange(tlStart,tlStart+tllen):
			bsltret.tlseq.append(self.tlseq[i])
		return bsltret
	
	def attach_lexform_sl_left(self,lexform):
		self.slseq.insert(0, unicode(AT_LexicalForm.create_without_lemma(lexform)) )
	def attach_lexform_tl_left(self,lexform):
		self.tlseq.insert(0, unicode(AT_LexicalForm.create_without_lemma(lexform)) )
	def attach_lexform_sl_right(self,lexform):
		self.slseq.append( unicode(AT_LexicalForm.create_without_lemma(lexform)) )
	def attach_lexform_tl_right(self,lexform):
		self.tlseq.append( unicode(AT_LexicalForm.create_without_lemma(lexform)) )
				
	def __repr__(self):
		return (" ".join([ l.encode('utf-8') for l in self.slseq])+" | "+" ".join([ l.encode('utf-8') for l in self.tlseq]))
	
	def copy(self):
		returned=BilingualSequenceLexTags()
		returned.slseq.extend(self.slseq)
		returned.tlseq.extend(self.tlseq)

		return returned
	
	def parse(self,strin):
		parts=strin.split(u" | ")
		self.slseq=parts[0].split(u" ")
		self.tlseq=parts[1].split(u" ")
	
	def matches_wildcards(self,wilcarded_bslx):
		if len(self.slseq) != len(wilcarded_bslx.slseq) or len(self.tlseq) != len(wilcarded_bslx.tlseq):
			return False
		for i in  xrange(len(wilcarded_bslx.slseq)):
			if wilcarded_bslx.slseq[i] != "*":
				if wilcarded_bslx.slseq[i] != self.slseq[i]:
					return False
		for i in  xrange(len(wilcarded_bslx.tlseq)):
			if wilcarded_bslx.tlseq[i] != "*":
				if wilcarded_bslx.tlseq[i] != self.tlseq[i]:
					return False
		return True 
	
	def __hash__(self):
		return hash(self.__repr__())
	def __eq__(self,other):
		return self.__repr__() == other.__repr__()

class BilingualSequenceLexSet(object):
	def __init__(self):
		self.freqmap=dict()
		self.keyslengthmap=dict()
		self.wildcardsCache=dict()
	
	def add_from_bilphrase(self,bilphrase,freq=1):
		bslta=BilingualSequenceLexTags()
		bslta.load_from_at(bilphrase)
		self.add(bslta,freq)
	
	def add(self,bslx,freq=1):
		if bslx in self.freqmap:
			self.freqmap[bslx]+=freq
		else:
			self.freqmap[bslx]=freq
		if not (len(bslx.slseq),len(bslx.tlseq)) in self.keyslengthmap:
			self.keyslengthmap[(len(bslx.slseq),len(bslx.tlseq))]=set()
		self.keyslengthmap[(len(bslx.slseq),len(bslx.tlseq))].add(bslx)
	def __str__(self):
		outputmap=dict()
		for key in self.freqmap.iterkeys():
			outputmap[str(key)]=self.freqmap[key]
		return str(outputmap)
	
	def get_freq(self,bslx):
		if bslx in self.freqmap:
			return self.freqmap[bslx]
		else:
			return 0
	
	def parse(self,strin):
		tmpMap=eval(strin)
		for key in tmpMap:
			bslx=BilingualSequenceLexTags()
			bslx.parse(key)
			self.add(bslx, tmpMap[key])
	
	def sum_freqs_of_compatible_seqs(self,bslx):
		mysum=0
		lengsthsTuple=(len(bslx.slseq),len(bslx.tlseq))
		if lengsthsTuple in self.keyslengthmap:
			if bslx in self.wildcardsCache:
				return self.wildcardsCache[bslx]
			
			candidatesSet=self.keyslengthmap[lengsthsTuple]
			
			#ugly and slow loop
			for bslc in candidatesSet:
				if bslc.matches_wildcards(bslx):
					#print >> sys.stderr, "candidate:\t"+str(bslc)
					mysum+=self.freqmap[bslc]
		self.wildcardsCache[bslx]=mysum
		return mysum


class AT_ParsingError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class AlignmentTemplate(object):
	
	SIDE_LEFT=1
	SIDE_RIGHT=2
	SIDE_NONE=-1 
	
	def __init__(self):
		self.sl_lexforms=list()
		self.tl_lexforms=list()
		
		self.parsed_sl_lexforms=list()
		self.parsed_tl_lexforms=list()
		
		self.alignments=list()
		self.restrictions=list()
		self.parsed_restrictions=list()
		
		#freq no se representa en __repr()__, por lo que dos ATs con distinta frecuencia
		#serán consideradas la misma cuanto estén en un set, x ejemplo
		self.freq=0
		#Lo mismo pasa con tl_lemmas_from_dictionary
		self.tl_lemmas_from_dictionary=list()
		#Lo mismo pasa con ID y los demás
		self.id=None
		self.correct_bilphrases=set()
		self.incorrect_bilphrases=set()
		
		#To be removed
		self.correct_bilphrases_original=set()
		self.matching_bilphrases=set()
		
		self.num_correct_bilphrases=0
		self.num_matching_bilphrases=0
		
		self.atswhicharesubset=set()
		self.atssymmetricdifferencenotempty=set()
		self.atswhicharesubsetpointers=set()
		self.parent=None
		
		self.afterwards_restrictions=list()
		
		self.bslt=None
		
		self.sl_position_in_sentence=0
		self.tl_position_in_sentence=0
		
		self.atsmatchingthisbilphrase=set()
		self.atsreproducingthisbilphrase=set()
		#an antiphrase is a tuple 
		#tuple[0]-> sorted list of contiguous sl indexes
		#tuple[1]-> sorted list of contiguous tl indexes
		self.antiphrases=list()
	def __repr__(self):
		return self.to_string()
	
	def clean_subsets(self):
		self.atswhicharesubset.clear()
		self.atssymmetricdifferencenotempty.clear()
		self.atswhicharesubsetpointers.clear()
		self.parent=None
	
	#def to_string(self,removeRestrictionsFromLexicalised=True, printDictionaryTranslations=False):
	def to_string(self,removeRestrictionsFromLexicalised=False, printDictionaryTranslations=False, useSecondEmptyRepresentation=False):
		
		if len(self.parsed_restrictions) != len(self.parsed_sl_lexforms):
			print >> sys.stderr, "Different length of sl words and restrictions"
			print >> sys.stderr, "SL: "+str(self.parsed_sl_lexforms)
			print >> sys.stderr, "Restrictions: "+str(self.parsed_restrictions)
			traceback.print_stack()
			return "__INCORRECT_ALIGNMENT_TEMPLATE__"
		
		mod_sllexlist=list()
		for plexform in self.parsed_sl_lexforms:
			mod_sllexlist.append(plexform.unparse(replaceSpacesWithUnderscore=True))

		mod_tllexlist=list()
		for plexform in self.parsed_tl_lexforms:
			mod_tllexlist.append(plexform.unparse(replaceSpacesWithUnderscore=True))

		mod_alignslist=list()
		for alignment in self.alignments:
			mod_alignslist.append(str(alignment[0])+":"+str(alignment[1]))
		
		alignStr=" "
		if len(mod_alignslist) > 0:
			alignStr=" ".join(mod_alignslist)
			
		mod_restrictions=list()
		for i in range(len(self.parsed_restrictions)):
			if self.parsed_sl_lexforms[i].has_lemma()  and removeRestrictionsFromLexicalised:
				mod_restrictions.append(u"__CLOSEWORD__")
			else:
				mod_restrictions.append(self.parsed_restrictions[i].unparse(useSecondEmptyRepresentation))
		
		if printDictionaryTranslations:
			mod_dictionary_translations=list()
			for tllemmadic in self.tl_lemmas_from_dictionary:
				mod_dictionary_translations.append(tllemmadic.replace(u" ",u"_"))
			return "%s | %s | %s | %s |%s" % (u" ".join(mod_sllexlist).encode('utf-8'), u" ".join(mod_tllexlist).encode('utf-8'), alignStr.encode('utf-8') ,u" ".join(mod_restrictions).encode('utf-8'),u" ".join(mod_dictionary_translations).encode('utf-8'))
		else:
			return "%s | %s | %s | %s" % (u" ".join(mod_sllexlist).encode('utf-8'), u" ".join(mod_tllexlist).encode('utf-8'), alignStr.encode('utf-8') ,u" ".join(mod_restrictions).encode('utf-8'))
	
	def draw_dot(self):
		myid=str(id(self))
		dotlines=list()
		dotlines.append("subgraph \"clusterat"+myid+"\" {")
		
		dotlines.append("DUMMY_clusterat"+myid+" [shape=point style=invis];")
		
		slfields=list()
		for i,l in enumerate(self.parsed_sl_lexforms):
			antiphraseIndexes=[ ai for ai in range(len(self.antiphrases)) if i in self.antiphrases[ai][0] ]
			antiphraseStr=",".join([str(api) for api in antiphraseIndexes])	
			if len(antiphraseIndexes) > 0:
				colorStr="grey"
			else:
				colorStr="white"
			slfields.append("<td port=\"f"+str(i)+"\" border=\"1\" bgcolor=\""+colorStr+"\">"+antiphraseStr+" "+str(l)+"</td>")
		jointfields="<table border=\"0\" cellspacing=\"0\"><tr>"+"".join(slfields)+"</tr></table>"
		dotlines.append(" sl"+myid+" [shape=none,label=<"+jointfields+">];")
		
		tlfields=list()
		for i,l in enumerate(self.parsed_tl_lexforms):
			antiphraseIndexes=[ ai for ai in range(len(self.antiphrases)) if i in self.antiphrases[ai][1] ]
			antiphraseStr=",".join([str(api) for api in antiphraseIndexes])	
			if len(antiphraseIndexes) > 0:
				colorStr="grey"
			else:
				colorStr="white"
			tlfields.append("<td port=\"f"+str(i)+"\" border=\"1\" bgcolor=\""+colorStr+"\">"+antiphraseStr+" "+str(l)+"</td>")
		jointfields="<table border=\"0\" cellspacing=\"0\"><tr>"+"".join(tlfields)+"</tr></table>"
		dotlines.append(" tl"+myid+" [shape=none,label=<"+jointfields+">];")
		
		for al in self.alignments:
			dotlines.append("sl"+myid+":f"+str(al[0])+" -> tl"+myid+":f"+str(al[1])+";")
		
		dotlines.append("}")
		return "\n".join(dotlines),"clusterat"+myid
	
	def __hash__(self):
		return hash(self.__repr__())
		#return hash(self.__repr__())
	
	def __cmp__(self,obj):
		return cmp(self.__repr__(),obj.__repr__())
		#return cmp(self.__repr__(),obj.__repr__())
	
	def fast_clone(self):
		myclone=AlignmentTemplate()
		myclone.parse(self.to_string(removeRestrictionsFromLexicalised=False).decode('utf-8'))
		
		myclone.afterwards_restrictions=list()
		for odict in self.afterwards_restrictions:
			cloneDict=dict()
			for key in odict.keys():
				cloneDict[key]=odict[key]
			myclone.afterwards_restrictions.append(cloneDict)
		
		return myclone
	
	def extract_lex_and_context_from_antiphrase(self,antiphrase):
		self.extract_bslt()
		
		sllex=list()
		tllex=list()
		
		#loop over sl positions
		for i in antiphrase[0]:
			sllex.append(self.bslt.slseq[i])
		#loop over tl positions
		for i in antiphrase[1]:
			tllex.append(self.bslt.tlseq[i])
		
		slPrev=self.bslt.slseq[antiphrase[0][0]-1] if len(antiphrase[0]) > 0 else self.bslt.slseq[antiphrase[2][0]]
		tlPrev=self.bslt.tlseq[antiphrase[1][0]-1] if len(antiphrase[1]) > 0 else self.bslt.tlseq[antiphrase[2][0]]
		
		slPost=self.bslt.slseq[antiphrase[0][-1]+1] if len(antiphrase[0]) > 0 else self.bslt.slseq[antiphrase[2][1]]
		tlPost=self.bslt.tlseq[antiphrase[1][-1]+1] if len(antiphrase[1]) > 0 else self.bslt.tlseq[antiphrase[2][1]]
		
		return slPrev,tlPrev, sllex,tllex, slPost,tlPost
		
	
	def contains_unk_or_punct(self):
		return any(lexform.is_unk_or_punct() for lexform in self.parsed_sl_lexforms) or any(lexform.is_unk_or_punct() for lexform in self.parsed_tl_lexforms) 
	
	def add_special_start_end_words(self):
		
		startSLMark=AT_LexicalForm()
		startSLMark.set_pos(u"sentencestart")
		startTLMark=AT_LexicalForm()
		startTLMark.set_pos(u"sentencestart")
		startResMark=AT_Restriction()
		startResMark.set_pos(u"sentencestart")
		self.parsed_sl_lexforms.insert(0, startSLMark)
		self.parsed_tl_lexforms.insert(0, startTLMark)
		self.parsed_restrictions.insert(0,startResMark)
		
		endSLMark=AT_LexicalForm()
		endSLMark.set_pos(u"sentenceend")
		endTLMark=AT_LexicalForm()
		endTLMark.set_pos(u"sentenceend")
		endResMark=AT_Restriction()
		endResMark.set_pos(u"sentenceend")
		self.parsed_sl_lexforms.append(endSLMark)
		self.parsed_tl_lexforms.append(endTLMark)
		self.parsed_restrictions.append(endResMark)
		
		oldalignments=self.alignments
		self.alignments=list()
		#start marks
		self.alignments.append((0,0))
		#original alignments
		for oldal in oldalignments:
			self.alignments.append((oldal[0]+1,oldal[1]+1))
		#end marks
		self.alignments.append((len(self.parsed_sl_lexforms)-1,len(self.parsed_tl_lexforms)-1))
		
		#update tl lemams form dictionary too
		if len(self.tl_lemmas_from_dictionary) > 0:
			self.tl_lemmas_from_dictionary.insert(0, u"dummylemma")
			self.tl_lemmas_from_dictionary.append(u"dummylemma")
	
	#an antiphrase is a tuple 
	#tuple[0]-> sorted list of contiguous sl indexes
	#tuple[1]-> sorted list of contiguous tl indexes
	#tuple[2]-> if tuple[0] or tuple[1] are empty, (righmostLeft,leftmostRight)
	def extract_antiphrases(self):
		self.antiphrases=list()
		
		localAntiphrases=list()
		
		#detect sequences of unaligned SL words
		seqsOfUnalignedSL=list()
		currentSeq=list()
		for i in xrange(len(self.parsed_sl_lexforms)):
			if len(self.get_tl_words_aligned_with(i))==0:
				if len(currentSeq) > 0 and currentSeq[-1] < i-1 :
					seqsOfUnalignedSL.append(currentSeq)
					currentSeq=list()
				currentSeq.append(i)
		if len(currentSeq) > 0:
			seqsOfUnalignedSL.append(currentSeq)
			
		#for each sequence, build TL side of antiphrase
		for seqOfUnalignedSl in seqsOfUnalignedSL:
			#rightmost TL word aligned with an SL word at the left of seq
			tlwordsalleft=set()
			for i in xrange(seqOfUnalignedSl[0]):
				tlwordsalleft.update(self.get_tl_words_aligned_with(i))
			if len(tlwordsalleft) > 0:				
				righmostLeft=max(tlwordsalleft)
			else:
				righmostLeft=-1
			#old	
			#righmostLeft=max( max( self.get_tl_words_aligned_with(i) ) for i in xrange(seqOfUnalignedSl[0]) )
			
			#leftmost TL word aligned with an SL word at the right of seq
			tlwordsalright=set()
			for i in xrange(seqOfUnalignedSl[-1]+1,len(self.parsed_sl_lexforms)):
				tlwordsalright.update(self.get_tl_words_aligned_with(i))
			if len(tlwordsalright) > 0:
				leftmostRight=min(tlwordsalright)
			else:
				leftmostRight=len(self.parsed_tl_lexforms)
			#OLD
			#leftmostRight=min( min(self.get_tl_words_aligned_with(i)) for i in xrange(seqOfUnalignedSl[-1]+1,len(self.parsed_sl_lexforms)) )
			
			#if lefmost and rightmost do not intersect...
			if righmostLeft < leftmostRight:
				#...and all the TL words between them are unaligned...
				# Note that all([]) == True
				if all( len(self.get_sl_words_aligned_with(i))==0 for i in xrange(righmostLeft+1,leftmostRight)):
					#... the antiphrase is OK
					localAntiphrases.append((seqOfUnalignedSl,range(righmostLeft+1,leftmostRight),(righmostLeft,leftmostRight) if leftmostRight-righmostLeft==1 else [] ))
						
		#detect sequences of unaligned TL words
		seqsOfUnalignedTL=list()
		currentSeq=list()
		for i in xrange(len(self.parsed_tl_lexforms)):
			if len(self.get_sl_words_aligned_with(i))==0:
				if len(currentSeq) > 0 and currentSeq[-1] < i-1 :
					seqsOfUnalignedTL.append(currentSeq)
					currentSeq=list()
				currentSeq.append(i)
		if len(currentSeq) > 0:
			seqsOfUnalignedTL.append(currentSeq)
		
		#for each sequence, build SL side of antiphrase
		for seqOfUnalignedTl in seqsOfUnalignedTL:
			#rightmost SL word aligned with a TL word at the left of seq
			slwordsalleft=set()
			for i in xrange(seqOfUnalignedTl[0]):
				slwordsalleft.update(self.get_sl_words_aligned_with(i))
			if len(slwordsalleft) > 0:				
				righmostLeft=max(slwordsalleft)
			else:
				righmostLeft=-1
			
			#leftmost SL word aligned with a TL word at the right of seq
			slwordsalright=set()
			for i in xrange(seqOfUnalignedTl[-1]+1,len(self.parsed_tl_lexforms)):
				slwordsalright.update(self.get_sl_words_aligned_with(i))
			if len(slwordsalright) > 0:
				leftmostRight=min(slwordsalright)
			else:
				leftmostRight=len(self.parsed_sl_lexforms)
			
			#if lefmost and rightmost do not intersect...
			if righmostLeft < leftmostRight:
				#...and all the SL words between them are unaligned...
				# Note that all([]) == True
				if all( len(self.get_tl_words_aligned_with(i))==0 for i in xrange(righmostLeft+1,leftmostRight)):
					#... the antiphrase is OK
					localAntiphrases.append((range(righmostLeft+1,leftmostRight),seqOfUnalignedTl,(righmostLeft,leftmostRight) if leftmostRight-righmostLeft==1 else []))
		#remove duplicates from localAntiphrases
		#TODO: make it faster
		for locAntiphrase in localAntiphrases:
			if not locAntiphrase in self.antiphrases:
				self.antiphrases.append(locAntiphrase)
		
	def increase_freq(self,pfreq):
		self.freq+=pfreq
	
	def remove_all_lemmas(self):
		for lex in self.parsed_sl_lexforms:
			lex.remove_lemma()
		for lex in self.parsed_tl_lexforms:
			lex.remove_lemma()
	
	def remove_all_inflection_tags(self):
		for lex in self.parsed_sl_lexforms:
			lex.remove_all_inflection_tags()
		for lex in self.parsed_tl_lexforms:
			lex.remove_all_inflection_tags()
		for lex in self.parsed_restrictions:
			lex.remove_all_inflection_tags()
	
	def get_sequences_of_lextags(self):
		slseq=[]
		tlseq=[]
		for l in self.parsed_sl_lexforms:
			slseq.append(AT_LexicalForm.create_without_lemma(l))
		for l in self.parsed_tl_lexforms:
			tlseq.append(AT_LexicalForm.create_without_lemma(l))
		return slseq,tlseq
	
	def get_first_aligned_sl_word(self):
		alignedSlWords=[ a[0] for a in self.alignments ]
		if len(alignedSlWords) > 0:
			return sorted(alignedSlWords)[0]
		else:
			return None
	
	def get_last_aligned_sl_word(self):
		alignedSlWords=[ a[0] for a in self.alignments ]
		if len(alignedSlWords) > 0:
			return sorted(alignedSlWords,reverse=True)[0]
		else:
			return None
	
	def get_first_aligned_tl_word(self):
		alignedTlWords=[ a[1] for a in self.alignments ]
		if len(alignedTlWords) > 0:
			return sorted(alignedTlWords)[0]
		else:
			return None
	
	def get_last_aligned_tl_word(self):
		alignedTlWords=[ a[1] for a in self.alignments ]
		if len(alignedTlWords) > 0:
			return sorted(alignedTlWords,reverse=True)[0]
		else:
			return None
	
	def extract_bslt(self):
		if self.bslt == None:
			bslt=BilingualSequenceLexTags()
			bslt.load_from_at(self)
			self.bslt=bslt
	
	def get_sequences_of_lextags_ends_aligned(self):
		self.extract_bslt()
		
		slseq=[]
		tlseq=[]
		
		for i in range(self.get_first_aligned_sl_word(),self.get_last_aligned_sl_word()+1):
			slseq.append(self.bslt.slseq[i])
		for i in range(self.get_first_aligned_tl_word(),self.get_last_aligned_tl_word()+1):
			tlseq.append(self.bslt.tlseq[i])
		return slseq,tlseq
	
	def set_afterwards_restrictions_from(self,otherat):
		self.afterwards_restrictions=list()
		for i in range(len(self.parsed_sl_lexforms)):
			sllexValues=self.parsed_sl_lexforms[i].get_tags_with_feature_names_as_dict()
			resValues=otherat.parsed_restrictions[i].get_tags_with_feature_names_as_dict()
			myDict=dict()
			#for featureName in sllexValues.keys():
			for featureName in resValues:
				if featureName in sllexValues:
					if parse_special_tag(sllexValues[featureName])[0] == AT_SpecialTagType.FOLLOW_ALIGNMENT:
						myDict[featureName]=resValues[featureName]
				else:
					 myDict[featureName]=resValues[featureName]
			self.afterwards_restrictions.append(myDict)
	
	def add_restrictions_from_tuples(self,tuples):
		for mytuple in tuples:
			self.parsed_restrictions[mytuple[0]].append_tag(mytuple[2])
			
	#old method. I guess it can be removed safely
	def build_grep_regexp(self):
		forgrep=u""
		
		for i in range(len(self.sl_lexforms)):
			lexformwithoutEmpty=re.sub(r'<empty_tag_[^>]*>', '', self.sl_lexforms[i])
			if self.restrictions[i]==u"__CLOSEWORD__":
				forgrep=forgrep+u"\\^"+lexformwithoutEmpty+u"\\$"
			else:
				forgrep=forgrep+u"\\^[^<]*"+re.sub(r"<\*[^>]*>", u"", lexformwithoutEmpty)+u"[^\\$]*\\$"
			if i < len(self.sl_lexforms)-1:
				forgrep=forgrep+u"[^^]*"
		
		return forgrep.strip()
	
	def get_sllex_and_restrictions_str(self):
		mod_sllexlist=list()
		for lexform in self.parsed_sl_lexforms:
			mod_sllexlist.append(lexform.unparse(replaceSpacesWithUnderscore=True))
		return u" ".join(mod_sllexlist)+" | "+u" ".join([ parsed_restriction.unparse() for parsed_restriction in self.parsed_restrictions])
	
	def get_pos_list(self,include_restrictions=False):
		posList=list()
		for i in range(len(self.parsed_sl_lexforms)):
			pword=self.parsed_sl_lexforms[i]
			prestriction=self.parsed_restrictions[i]
			if include_restrictions:
				posList.append((pword.pos,prestriction.get_tags()))
			else:
				posList.append(pword.pos)
		return posList
	
	def get_pos_list_str(self, include_restrictions=False):
		posList=list()
		for i in range(len(self.parsed_sl_lexforms)):
			pword=self.parsed_sl_lexforms[i]
			prestriction=self.parsed_restrictions[i]
			if include_restrictions:
				posList.append(pword.pos+"_"+prestriction.unparse())
			else:
				posList.append(pword.pos)
		return u"__".join(posList)
	
	def get_left_side_str(self):
		return u"__".join([lf.unparse() for lf in self.parsed_sl_lexforms])
	
	def get_num_lemmas_of_aligned_words(self):
		num=0
		for numlexform in range(len(self.parsed_sl_lexforms)):
			isAligned=False
			for al in self.alignments:
				if al[0]==numlexform:
					isAligned=True
					break
			if isAligned:
				sllexform=self.parsed_sl_lexforms[numlexform]
				if sllexform.has_lemma():
					num+=1
		return num
	
	def get_sl_words_aligned_with(self,tlindex):
		sl_indexes=list()
		for al in self.alignments:
			if al[1]==tlindex:
				sl_indexes.append(al[0])
		return sl_indexes
	def get_tl_words_aligned_with(self,slindex):
		tl_indexes=list()
		for al in self.alignments:
			if al[0]==slindex:
				tl_indexes.append(al[1])
		return tl_indexes
	
	def set_lemmas_from_other_at(self,otherat):
		for i in range(len(self.parsed_sl_lexforms)):
			self.parsed_sl_lexforms[i].set_lemma(otherat.parsed_sl_lexforms[i].get_lemma())
		for i in range(len(self.parsed_tl_lexforms)):
			self.parsed_tl_lexforms[i].set_lemma(otherat.parsed_tl_lexforms[i].get_lemma())
		
	
	def get_sl_lemmas(self):
		sllemmas=list()
		for sllex in self.parsed_sl_lexforms:
			sllemmas.append(sllex.get_lemma())
		return sllemmas
		
	
	
	def extract_lemmas(self):
		sllemmas=list()
		tllemmas=list()
		for i in range(len(self.parsed_sl_lexforms)):
			lf=self.parsed_sl_lexforms[i]
			lemma=lf.get_lemma()
			self.parsed_sl_lexforms[i].remove_lemma()
			if len(lemma)>0:
				sllemmas.append(lemma)
			else:
				sllemmas.append(u"__NONLEXICALIZABLE__")
		
		for i in range(len(self.parsed_tl_lexforms)):
			lf=self.parsed_tl_lexforms[i]
			lemma=lf.get_lemma()
			self.parsed_tl_lexforms[i].remove_lemma()
			
			if len(lemma)>0:
				tllemmas.append(lemma)
			else:
				tllemmas.append(u"__NONLEXICALIZABLE__")
		return sllemmas,tllemmas	
	
	def lexicalise_all(self,sllemmas,tllemmas):
		slindexes=list()
		for i in range(len(self.parsed_sl_lexforms)):
			if not self.parsed_sl_lexforms[i].has_lemma():
				slindexes.append(i)
		self.lexicalise(slindexes,sllemmas,tllemmas)
	
	#alternatives=list of alternative
	#alternative=set of tl indexes to be lexicalised
	#These Tl indexes must match a sl index of a non-lexicalised word
	#Sl non-lexicalised word must be aligned with multiple Tl words
	def compute_alternatives_for_tl_lexicalisations(self):
		alternatives=list()
		slIndexesOfMultipleAligned=list()
		
		totalTlWordsCanBeLexicalised=0
		for i in range(len(self.parsed_sl_lexforms)):
			tl_aligned_with=list()
			for alignment in self.alignments:
				if alignment[0]==i:
					tl_aligned_with.append(alignment[1])
			if len(tl_aligned_with)> 1:
				slIndexesOfMultipleAligned.append((i,tl_aligned_with))
		
		combinationsForEachSlIndex=list()
		
		for slIndex,tlIndexes in slIndexesOfMultipleAligned:
			totalTlWordsCanBeLexicalised+=len(tlIndexes)
			optionsToCombine=list()
			#True=lexicalise
			#False=not lexicalise
			for tlIndex in tlIndexes:
				optionsToCombine.append((True,False))
			tmpCombinations=combine_elements(optionsToCombine)
			combinations=list()
			for tc in tmpCombinations:
				indexesCombination=list()
				for i in range(len(tc)):
					if tc[i]:
						indexesCombination.append(tlIndexes[i])
				combinations.append(indexesCombination)
			combinationsForEachSlIndex.append(combinations)
		
		finalCombinations=combine_elements(combinationsForEachSlIndex)
		for finalCombination in finalCombinations:
			currentAlternative=list()
			for element in finalCombination:
				for index in element:
					currentAlternative.append(index)
			#combination True,True,True.. is banned
			#combination False,False,False.. is banned?
			if len(currentAlternative) > 0 and len(currentAlternative) < totalTlWordsCanBeLexicalised:
				alternatives.append(currentAlternative)

		return alternatives
	
	def lexicalise_sl_withexceptions(self,exceptions,lemmas):
		for i in range(len(self.parsed_sl_lexforms)):
			if not i in exceptions:
				self.parsed_sl_lexforms[i].set_lemma(lemmas[i])
	
	def lexicalise_tl_withexceptions(self,exceptions,lemmas):
		for i in range(len(self.parsed_tl_lexforms)):
			if not i in exceptions:
				self.parsed_tl_lexforms[i].set_lemma(lemmas[i])
			else:
				self.parsed_tl_lexforms[i].remove_lemma()
	
	def lexicalise_from_categories(self,categories,sl_lemmas,tl_lemmas):
		for i in range(len(self.parsed_sl_lexforms)):
			if self.parsed_sl_lexforms[i].get_pos() in categories:
				self.parsed_sl_lexforms[i].set_lemma(sl_lemmas[i])
		
		for i in range(len(self.parsed_tl_lexforms)):
			if self.parsed_tl_lexforms[i].get_pos() in categories:
				self.parsed_tl_lexforms[i].set_lemma(tl_lemmas[i])
		

	def lexicalise_tl(self,tlindexes,tllemmas):
		for tlindex in tlindexes:
			if self.parsed_tl_lexforms[tlindex].has_lemma():
				self.parsed_tl_lexforms[tlindex].set_lemma("__ERROR__")
			else:
				self.parsed_tl_lexforms[tlindex].set_lemma(tllemmas[tlindex])
	
	def lexicalise(self,slindexes,sllemmas,tllemmas):
		for index in slindexes:
#			self.restrictions[index]=u"__CLOSEWORD__"
			self.parsed_sl_lexforms[index].set_lemma(sllemmas[index])
			alignedTLWords=list()
			newAlignments=list()
			for alignment in self.alignments:
				if alignment[0]==index:
					alignedTLWords.append(alignment[1])
			#	else:
			#		newAlignments.append(alignment)
			#self.alignments=newAlignments
			for alignedTLWord in alignedTLWords:
				if not self.parsed_tl_lexforms[alignedTLWord].has_lemma():
					self.parsed_tl_lexforms[alignedTLWord].set_lemma(tllemmas[alignedTLWord])
	
	#Simply assigns the lemmas provided to the SL and TL lexical forms.
	#DOes not follow alignments
	def set_lemmas(self, sllemmas, tllemmas):
		for i in range(len(sllemmas)):
			self.parsed_sl_lexforms[i].set_lemma( (sllemmas[i][1:] if sllemmas[i].startswith(u"_") else sllemmas[i] ).replace(u"_",""))
		for i in range(len(tllemmas)):
			self.parsed_tl_lexforms[i].set_lemma(tllemmas[i].replace(u"_",""))
	
				
	def add_alignments(self,newalignments):
		for newalignment in newalignments:
			self.alignments.append(newalignment)
	
	def remove_alignments(self,newalignments):
		for newalignment in newalignments:
			self.alignments.remove(newalignment)
	
	def shorten_restrictions(self):
		for i in range(len(self.parsed_sl_lexforms)):
			sllex=self.parsed_sl_lexforms[i]
			res=self.parsed_restrictions[i]
			differentTags=[ j for j in range(len(res.get_tags())) if sllex.get_tags()[j] != res.get_tags()[j] ]
			#cut to the last different tag
			if len(differentTags) == 0:
				res.set_tags([])
			else:
				lastDifferentTag=differentTags[-1]
				res.set_tags(res.get_tags()[:lastDifferentTag+1])
	
	def add_explicit_restrictions(self):
		for i in range(len(self.parsed_sl_lexforms)):
			sllex=self.parsed_sl_lexforms[i]
			res=self.parsed_restrictions[i]
			newtags=list()
			newtags.extend(res.get_tags())
			newtags.extend(sllex.get_tags()[len(res.get_tags()):])
			res.set_tags(newtags)
	
	def add_explicit_empty_tags(self):
		#tagsequences:dict
		#key:pos
		#value: list of taggroups
		
		for word in self.parsed_sl_lexforms:
			word.set_tags(AT_LexicalTagsProcessor.add_explicit_empty_tags(word.get_pos(),word.get_tags()))
		
		for word in self.parsed_tl_lexforms:
			word.set_tags(AT_LexicalTagsProcessor.add_explicit_empty_tags(word.get_pos(),word.get_tags()))
		
		for res in self.parsed_restrictions:
			if not res.is_special():
				res.set_tags(AT_LexicalTagsProcessor.add_explicit_empty_tags(res.get_pos(),res.get_tags(),weAreProcessingRestrictions=True)) 
	
	
	#Returns list. Each element of the list is a list of alignments to be added to the AT.
	# Each alignment is a tuple (SL index, TL index)
	def get_alignment_options_for_unaligned_words(self):
		unalignedTLindexes=set()
		for i in range(len(self.parsed_tl_lexforms)):
			unalignedTLindexes.add(i)
		for al in self.alignments:
			unalignedTLindexes.discard(al[1])
		
		SLlastTagsCatList=list()
		for sllexword in self.parsed_sl_lexforms:
			if DEBUG:
				print >> sys.stderr, "Tags and categories list:"
				print >> sys.stderr, str(sllexword.tags)
				print >> sys.stderr, str(sllexword.categories)
			
			if len(sllexword.get_tags()) > 0:
				SLlastTagsCatList.append(sllexword.get_tags_with_feature_names()[-1].feature_name)
			else:
				SLlastTagsCatList.append(None)
		if DEBUG:
			print >> sys.stderr, "Last SL categories of "+str(self)+":"
			print >> sys.stderr, str(SLlastTagsCatList)
			
		
		possibleAlignmentsForEachUnalignedTLWord=list()
		
		unalignedTLindexesList=list(unalignedTLindexes)
		for unalignedTLindex in unalignedTLindexesList:
			tllex=self.parsed_tl_lexforms[unalignedTLindex]
			tagsAndNames=tllex.get_tags_with_feature_names()
			lastTag=tagsAndNames[-1].feature_value
			tagroup=tagsAndNames[-1].feature_name
			
			candidateSLWords=list()
			
			for i in range(len(SLlastTagsCatList)):
				if tagroup == SLlastTagsCatList[i]:
					candidateSLWords.append(i)
			candidateSLWords.append(-1)
			
			possibleAlignmentsForEachUnalignedTLWord.append(candidateSLWords)
		
		#Combine possible alignments for each TL word
		options=combine_elements(possibleAlignmentsForEachUnalignedTLWord)
		output_list=list()
		
		for option in options:
			output_option=list()
			for i in range(len(option)):
				tlindex=unalignedTLindexesList[i]
				if option[i] != -1:
					alignment=(option[i],tlindex)
					output_option.append(alignment)
			output_list.append(output_option)
		
		return output_list
	
	def is_contiguous_to_antiphrase(self,antiphrases,antiphraseResults):
		slleft=self.sl_position_in_sentence-1
		tlleft=self.tl_position_in_sentence-1
		
		slright=self.sl_position_in_sentence+len(self.parsed_sl_lexforms)
		tlright=self.tl_position_in_sentence+len(self.parsed_tl_lexforms)
		
		slleftAntiphraseIndexes=[ i for i in range(len(antiphrases)) if slleft in antiphrases[i][0] ]
		tlleftAntiphraseIndexes=[ i for i in range(len(antiphrases)) if tlleft in antiphrases[i][1] ]
		slrightAntiphrasesIndexes=[ i for i in range(len(antiphrases)) if slright in antiphrases[i][0] ]
		tlrightAntiphrasesIndexes=[ i for i in range(len(antiphrases)) if tlright in antiphrases[i][1] ]
		
		if any( antiphraseResults[i]==AlignmentTemplate.SIDE_RIGHT for i in slleftAntiphraseIndexes ):
			return True
		if any( antiphraseResults[i]==AlignmentTemplate.SIDE_RIGHT for i in tlleftAntiphraseIndexes ):
			return True
		if any( antiphraseResults[i]==AlignmentTemplate.SIDE_LEFT for i in slrightAntiphrasesIndexes ):
			return True
		if any( antiphraseResults[i]==AlignmentTemplate.SIDE_LEFT for i in tlrightAntiphrasesIndexes ):
			return True
		return False
	
	def unaligned_edges_match_antiphrase(self,antiphrases,antiphraseResults):
		fsl=self.get_first_aligned_sl_word()
		ftl=self.get_first_aligned_tl_word()
		
		lsl=self.get_last_aligned_sl_word()
		ltl=self.get_last_aligned_tl_word()
		
		leftAntiphraseSLLen=fsl
		leftAntiphraseTLLen=ftl
		
		rightAntiphraseSLLen=len(self.parsed_sl_lexforms)-1-lsl
		rightAntiphraseTLLen=len(self.parsed_tl_lexforms)-1-ltl
		
		leftAntiphrase=(range(self.sl_position_in_sentence,self.sl_position_in_sentence+leftAntiphraseSLLen),range(self.tl_position_in_sentence,self.tl_position_in_sentence+leftAntiphraseTLLen))
		rightAntiphrase=(range(self.sl_position_in_sentence+len(self.parsed_sl_lexforms)-rightAntiphraseSLLen,self.sl_position_in_sentence+len(self.parsed_sl_lexforms)),range(self.tl_position_in_sentence+len(self.parsed_tl_lexforms)-rightAntiphraseTLLen,self.tl_position_in_sentence+len(self.parsed_tl_lexforms)))
		
		#check left antiphrase
		if leftAntiphraseSLLen>0 or leftAntiphraseTLLen>0:
			foundInAntiphraseList=False
			for antiphraseIndex,antiphrase in enumerate(antiphrases):
				if antiphrase[0:2] == leftAntiphrase and antiphraseResults[antiphraseIndex]==AlignmentTemplate.SIDE_RIGHT:
					foundInAntiphraseList=True
			if not foundInAntiphraseList:
				return False
		
		#check right antiphrase
		if rightAntiphraseSLLen>0 or rightAntiphraseTLLen>0:
			foundInAntiphraseList=False
			for antiphraseIndex,antiphrase in enumerate(antiphrases):
				if antiphrase[0:2] == rightAntiphrase and antiphraseResults[antiphraseIndex]==AlignmentTemplate.SIDE_LEFT:
					foundInAntiphraseList=True
			if not foundInAntiphraseList:
				return False
		
		return True
	
	def is_ends_aligned(self):
		firstSL=0
		lastSL=len(self.parsed_sl_lexforms)-1
		firstTL=0
		lastTL=len(self.parsed_tl_lexforms)-1
		
		alignedWithFirstSL=[ al for al in self.alignments if al[0]==firstSL]
		alignedWithLastSL=[al for al in self.alignments if al[0] == lastSL]
		alignedWithFirstTL=[ al for al in self.alignments if al[1]==firstTL]
		alignedWithLastTL=[al for al in self.alignments if al[1] == lastTL]
		
		if len(alignedWithFirstSL) > 0 and len(alignedWithLastSL) > 0 and len(alignedWithFirstTL)>0 and len(alignedWithLastTL)>0:
			return True
		else:
			return False

	# Returns list. Each element of the list is a list of alignments to be removed from the AT.
	# When removing them each Tl word will be aligned with at most one SL word
	# Each alignment is a tuple (SL index, TL index)
	def get_unalignment_options_for_multiple_aligned_unlexicalised_tl_words(self,bilphrase):
		
		alignmentsOfTL=list()
		for i in range(len(self.parsed_tl_lexforms)):
			alignmentList=list()
			for al in self.alignments:
				if al[1]==i:
					alignmentList.append(al)
			if len(alignmentList) > 1 and not self.parsed_tl_lexforms[i].has_lemma():
				alignmentsOfTL.append((i,alignmentList))
		
		validAlignmentsOfTL=list()
		for alTL in alignmentsOfTL:
			i=alTL[0]
			alignmentList=alTL[1]
			newAlignmentList=[ al for al in alignmentList if bilphrase.tl_lemmas_from_dictionary[al[0]] == bilphrase.parsed_tl_lexforms[al[1]].get_lemma() ]
			validAlignmentsOfTL.append((i,newAlignmentList))
		
		
		output_list=list()
		
		combinationInput=[ el[1] for el in  validAlignmentsOfTL]
		allAlignments=[ el[1] for el in  alignmentsOfTL ]
		combinationOutput=combine_elements(combinationInput)
		for combination in combinationOutput:
			atgroups=copy.deepcopy(allAlignments)
			atgroupsset=set()
			for i in range(len(combination)):
				atgroups[i].remove(combination[i])
				atgroupsset.update(atgroups[i])
			output_list.append(atgroupsset)
		
		return output_list

	# Returns list. Each element of the list is a list of alignments to be removed from the AT.
	# When removing them each Tl word will be aligned with at most one SL word
	# Each alignment is a tuple (SL index, TL index)
	def get_unalignment_options_for_multiple_aligned_tl_words(self):
		
		alignmentsOfTL=list()
		for i in range(len(self.tl_lexforms)):
			alignmentList=list()
			for al in self.alignments:
				if al[1]==i:
					alignmentList.append(al)
			if len(alignmentList) > 1:
				alignmentsOfTL.append((i,alignmentList))
		
		output_list=list()
		
		combinationInput=[ el[1] for el in  alignmentsOfTL]
		combinationOutput=combine_elements(combinationInput)
		for combination in combinationOutput:
			atgroups=copy.deepcopy(combinationInput)
			for i in range(len(combination)):
				atgroups[i].remove(combination[i])
			output_list.append(atgroups)
		
		return output_list
	
	#WARNING: taggroups removed from parameters
	#WARNING: Really hacky method. I wont rewrite it
	#NOT USED ANYNMORE
	def generalise(self,RestrictionsRestrictGeneralisation=True,AgreementsRestrictGeneralisation=True,tagGroupsWhichCanBeGeneralisedWhenEmpty=["gender","numberat","person"],tagGroupsWhichCanBeGeneralisedWhenEmptySL=[],allWordsAtTheSameTime=True,UnalignedWordsRestrictOtherWords=True):
		
		DEBUG=False
		if DEBUG:
			print >>sys.stderr, "Generalising AT: "+self.__repr__()
			print >>sys.stderr, "Options:"
			print >>sys.stderr, "RestrictionsRestrictGeneralisation="+str(RestrictionsRestrictGeneralisation)
			print >>sys.stderr, "AgreementsRestrictGeneralisation="+str(AgreementsRestrictGeneralisation)
			print >>sys.stderr, "allWordsAtTheSameTime="+str(allWordsAtTheSameTime)
			print >>sys.stderr, "UnalignedWordsRestrictOtherWords="+str(UnalignedWordsRestrictOtherWords)
			
		########################################
		############           #################
		#RestrictionsRestrictGeneralisation=False
		########################################
		#AgreementsRestrictGeneralisation=False
		#######################################
		#allWordsAtTheSameTime=True
		########################################
		#UnalignedWordsRestrictOtherWords=True
		########################################
		
		#Algoritmo en pseudocódigo:
		#
		# 1. buscar + de 1 palabra con la misma terminación. Si las encuentro, quitarla
		# si no, quitar la última etiqueta de la palabra más larga
		#
		
		#self.sl_lexforms and self.tl_lexforms are only used in this method and will be removed soon
		
		parsed_sl_lex=list()
		self.sl_lexforms[:]=[]
		for lexform in self.parsed_sl_lexforms:
			parsed_sl_lex.append(lexform.get_lexical_category_plus_tags())
			self.sl_lexforms.append(lexform.unparse())
		
		parsed_tl_lex=list()
		self.tl_lexforms[:]=[]
		for lexform in self.parsed_tl_lexforms:
			parsed_tl_lex.append(lexform.get_lexical_category_plus_tags())
			self.tl_lexforms.append(lexform.unparse())
		
		self.restrictions[:]=[]
		parsed_restrictions=list()
		for res in self.parsed_restrictions:
			parsed_restrictions.append(res.get_lexical_category_plus_tags())
			self.restrictions.append(res.unparse())
		
		
		#Remove SL generalised tags
		generalisedSLIndexes=list()
		for i in range(len(parsed_sl_lex)):
			generalisedSLIndexes.append([])
			for j in range(len( parsed_sl_lex[i])):
				if parsed_sl_lex[i][j].startswith("*"):
					generalisedSLIndexes[i]=parsed_sl_lex[i][j:]
					parsed_sl_lex[i]=parsed_sl_lex[i][:j]
					break

		#Remove TL generalised tags:
		#Cuidado!!! Pueden quedar etiquetas en TL generalizadas fuera del final
		generalisedTLIndexes=list()
		for i in range(len(parsed_tl_lex)):
			generalisedTLIndexes.append([])
			for al in self.alignments:
				if al[1]==i:
					slindex=al[0]
					k=len(generalisedSLIndexes[slindex])-1
					while k>=0:
						if DEBUG:
							print >> sys.stderr, str(generalisedSLIndexes[slindex][k])+" == "+str(parsed_tl_lex[i][-1])
						if generalisedSLIndexes[slindex][k] == parsed_tl_lex[i][-1] or generalisedSLIndexes[slindex][k][1:] == get_tag_group_from_tag(parsed_tl_lex[i][-1],AT_LexicalTagsProcessor.taggroups,parsed_tl_lex[i][0]):
							generalisedTLIndexes[i].insert(0,parsed_tl_lex[i][-1])
							parsed_tl_lex[i]=parsed_tl_lex[i][:-1]
						k-=1
					
					#sllength=len(parsed_sl_lex[slindex])
					#generalisedTLIndexes[i]=parsed_tl_lex[i][sllength:]
					#parsed_tl_lex[i]=parsed_tl_lex[i][:sllength]
			
		if DEBUG:
			print >> sys.stderr, "generalisedSLIndexes: "+str(generalisedSLIndexes)
			print >> sys.stderr, "parsed_sl_lex: "+str(parsed_sl_lex)
			
		if DEBUG:
			print >> sys.stderr, "generalisedTLIndexes: "+str(generalisedTLIndexes)
			print >> sys.stderr, "parsed_tl_lex: "+str(parsed_tl_lex)
		
		
		#Already lexicalised words and words with only 1 tag cannot be lexicalised 
		#
		#WARNING: Now lexicalised words also have restrictions. 
		generalizableIndexes=list()
		for i in range(len(self.restrictions)):
			#if self.restrictions[i]!=u"__CLOSEWORD__" and len(parsed_sl_lex[i])>1:
			if len(parsed_sl_lex[i])>1:
				generalizableIndexes.append(i)
		
		if DEBUG:
			print >> sys.stderr, "GeneralizableIndexex after step 1: "+str(generalizableIndexes)		
		
		#if SL and TL tags are of the same type:
		#Last tag must be the same in SL and TL 
		if AgreementsRestrictGeneralisation:
			newGeneralizableIndexes=list()
			tagGroupsNotGeneralized=set()
			for genindex in generalizableIndexes:
				slLastTag=parsed_sl_lex[genindex][-1]
				slPos=parsed_sl_lex[genindex][0]
				tlLastTags=list()
				restrictionLastTag=u""
				
				#Useless right now
				if len(parsed_restrictions[genindex]) >= len(parsed_sl_lex[genindex]):
					restrictionLastTag=parsed_restrictions[genindex][len(parsed_sl_lex[genindex])-1]
				
				for al in self.alignments:
					if al[0] == genindex:
						tlLastTags.append((parsed_tl_lex[al[1]][-1],parsed_tl_lex[al[1]][0]))

				slgroup=get_tag_group_from_tag(slLastTag,AT_LexicalTagsProcessor.taggroups,slPos)
				sameLastTags=True
				for tlLastTag in tlLastTags:
					tlgroup=get_tag_group_from_tag(tlLastTag[0],AT_LexicalTagsProcessor.taggroups,tlLastTag[1])
					if slgroup==tlgroup and slLastTag != tlLastTag[0] and not ( tlLastTag[0].startswith(u"empty_tag_") and tlLastTag[0][10:] in tagGroupsWhichCanBeGeneralisedWhenEmpty ) and not ( slLastTag.startswith(u"empty_tag_") and slLastTag[10:] in tagGroupsWhichCanBeGeneralisedWhenEmptySL ):
						sameLastTags=False
				
				#Disabled
				if False:
					sameRestritionTags=True
					for tlLastTag in tlLastTags:
						if restrictionLastTag != tlLastTag[0]:
							sameRestritionTags=False
							
				#if sameLastTags or sameRestritionTags:
				if sameLastTags:
					newGeneralizableIndexes.append(genindex)
				else:
					tagGroupsNotGeneralized.add(get_tag_group_from_tag(slLastTag,AT_LexicalTagsProcessor.taggroups,slPos))
			generalizableIndexes=newGeneralizableIndexes
			
			if DEBUG:
				print >> sys.stderr, "GeneralizableIndexex after step 1.5: "+str(generalizableIndexes)
			
			if allWordsAtTheSameTime:
				newGeneralizableIndexes=list()
				for genindex in generalizableIndexes:
					slLastTag=parsed_sl_lex[genindex][-1]
					slPos=parsed_sl_lex[genindex][0]
					if not get_tag_group_from_tag(slLastTag,AT_LexicalTagsProcessor.taggroups,slPos) in tagGroupsNotGeneralized:
						newGeneralizableIndexes.append(genindex)
				generalizableIndexes=newGeneralizableIndexes

		if DEBUG:
			print >> sys.stderr, "GeneralizableIndexex after step 2: "+str(generalizableIndexes)
		
		#Resulting tags legth must be longer or equal than restrictions
		if RestrictionsRestrictGeneralisation:
			newGeneralizableIndexes=list()
			restrictedCategories=set()
			for genindex in generalizableIndexes:
				if len(parsed_sl_lex[genindex])>len(parsed_restrictions[genindex]):
					newGeneralizableIndexes.append(genindex)
				else:
					restrictedCategories.add(get_tag_group_from_tag(parsed_restrictions[genindex][-1],AT_LexicalTagsProcessor.taggroups,parsed_restrictions[genindex][0]))
			if allWordsAtTheSameTime:
				generalizableIndexes=list()
				for newgenindex in newGeneralizableIndexes:
					if not get_tag_group_from_tag(parsed_sl_lex[newgenindex][-1],AT_LexicalTagsProcessor.taggroups,parsed_sl_lex[newgenindex][0]) in restrictedCategories:
						generalizableIndexes.append(newgenindex)
			else:
				generalizableIndexes=newGeneralizableIndexes
		
		if DEBUG:
			print >> sys.stderr, "GeneralizableIndexex after step 3: "+str(generalizableIndexes)
			
		if UnalignedWordsRestrictOtherWords:
			#Search TL words that are not aligned
			unalignedTLIndexes=list()
			for i in range(len(parsed_tl_lex)):
				isAligned=False
				for al in self.alignments:
					if al[1]==i:
						isAligned=True
						break
				if not isAligned:
					unalignedTLIndexes.append(i)
			if DEBUG:
				print >> sys.stderr, "Unaligned TL indexes: "+str(unalignedTLIndexes)
			for unalignedTLIndex in unalignedTLIndexes:
				for j in range(len(parsed_tl_lex[unalignedTLIndex])):
					if j > 0:
						taggroup=get_tag_group_from_tag(parsed_tl_lex[unalignedTLIndex][j],AT_LexicalTagsProcessor.taggroups,parsed_tl_lex[unalignedTLIndex][0])
						newGeneralizableIndexes=list()
						for generalizableIndex in generalizableIndexes:
							if get_tag_group_from_tag(parsed_sl_lex[generalizableIndex][-1],AT_LexicalTagsProcessor.taggroups,parsed_sl_lex[generalizableIndex][0]) != taggroup:
								newGeneralizableIndexes.append(generalizableIndex)
						generalizableIndexes=newGeneralizableIndexes
		
		if DEBUG:
			print >> sys.stderr, "GeneralizableIndexex after step 4: "+str(generalizableIndexes)
		
		if len(generalizableIndexes) > 0:
			
			#Find maximum group of words whose last tag belongs to the same group
			lastTagGroups=list()
			for genindex in generalizableIndexes:
				lastTag=parsed_sl_lex[genindex][-1]
				pos=parsed_sl_lex[genindex][0]
				lastTagGroups.append(get_tag_group_from_tag(lastTag,AT_LexicalTagsProcessor.taggroups,pos))
				
			
			#build dict to find the most repeated group in last tag		
			dictGroupId_index=dict()
			for i in range(len(lastTagGroups)):
				if not lastTagGroups[i] in dictGroupId_index:
					dictGroupId_index[lastTagGroups[i]]=set()
				dictGroupId_index[lastTagGroups[i]].add(i)
			
			GroupIdWithMorewords=None
			maxWords=0
			for groupid in dictGroupId_index.keys():
				if len(dictGroupId_index[groupid]) > maxWords:
					GroupIdWithMorewords=groupid
					maxWords=len(dictGroupId_index[groupid])
			
			if DEBUG:
				print >> sys.stderr, "Group ID with more words: "+str(GroupIdWithMorewords)
				print >> sys.stderr, "maxWords: "+str(maxWords)
			
			if maxWords > 1:
				wordsToBeGeneralised=dictGroupId_index[GroupIdWithMorewords]
				GeneraliseInTL=True
				#Check if any TL word shares last tag with restriction: NOT NOW.
				# If SL and TL word don't have the same value in the tag, no generalisation in TL
				
				for wordToBeGeneralised in wordsToBeGeneralised:
					trueIndex=generalizableIndexes[wordToBeGeneralised]
					tlindexes=list()
					for al in self.alignments:
						if al[0]==trueIndex:
							tlindexes.append(al[1])
					#for tlindex in tlindexes:
						#if parsed_sl_lex[trueIndex][-1] != parsed_tl_lex[tlindex][-1]:
							#GeneraliseInTL=False
						#if len(parsed_restrictions[trueIndex]) >= len(parsed_tl_lex[tlindex]):
						#	if parsed_tl_lex[tlindex][-1] == parsed_restrictions[trueIndex][len(parsed_tl_lex[tlindex])-1]:
						#		GeneraliseInTL=False
					
				#remove last tag from the corresponding words
				for wordToBeGeneralised in wordsToBeGeneralised:
					trueIndex=generalizableIndexes[wordToBeGeneralised]
					self.sl_lexforms[trueIndex]=get_lemma(self.sl_lexforms[trueIndex])+u"<"+u"><".join(parsed_sl_lex[trueIndex][:-1])+u"><*"+GroupIdWithMorewords+u">"
					if len(generalisedSLIndexes[trueIndex]) > 0:
						self.sl_lexforms[trueIndex]=self.sl_lexforms[trueIndex]+u"<"+u"><".join(generalisedSLIndexes[trueIndex])+u">"
						
					tlindexes=list()
					for al in self.alignments:
						if al[0]==trueIndex:
							tlindexes.append(al[1])
					
					for tlindex in tlindexes:
						#if (GeneraliseInTL or parsed_tl_lex[tlindex][-1]==parsed_sl_lex[trueIndex][-1]) and get_tag_group_from_tag(parsed_tl_lex[tlindex][-1],taggroups,parsed_tl_lex[tlindex][0])==get_tag_group_from_tag(parsed_sl_lex[trueIndex][-1],taggroups,parsed_sl_lex[trueIndex][0]):
						if parsed_tl_lex[tlindex][-1]==parsed_sl_lex[trueIndex][-1] and get_tag_group_from_tag(parsed_tl_lex[tlindex][-1],AT_LexicalTagsProcessor.taggroups,parsed_tl_lex[tlindex][0])==get_tag_group_from_tag(parsed_sl_lex[trueIndex][-1],AT_LexicalTagsProcessor.taggroups,parsed_sl_lex[trueIndex][0]):
							self.tl_lexforms[tlindex]=get_lemma(self.tl_lexforms[tlindex])+u"<"+u"><".join(parsed_tl_lex[tlindex][:-1])+u"><*"+GroupIdWithMorewords+u">"
							if len(generalisedTLIndexes[tlindex]) > 0:
								self.tl_lexforms[tlindex]=self.tl_lexforms[tlindex]+u"<"+u"><".join(generalisedTLIndexes[tlindex])+u">"
			else:
				#remove last tag from the longest word
				maxLength=1
				maxLengthIndex=-1
				for genindex in generalizableIndexes:
					if len(parsed_sl_lex[genindex])>maxLength:
						maxLength=len(parsed_sl_lex[genindex])
						maxLengthIndex=genindex
				self.sl_lexforms[maxLengthIndex]=get_lemma(self.sl_lexforms[maxLengthIndex])+u"<"+u"><".join(parsed_sl_lex[maxLengthIndex][:-1])+u"><*"+get_tag_group_from_tag(parsed_sl_lex[maxLengthIndex][-1],AT_LexicalTagsProcessor.taggroups,parsed_sl_lex[maxLengthIndex][0])+u">"
				if len(generalisedSLIndexes[maxLengthIndex]) > 0:
					self.sl_lexforms[maxLengthIndex]=self.sl_lexforms[maxLengthIndex]+u"<"+u"><".join(generalisedSLIndexes[maxLengthIndex])+u">"
				
				tlindexes=list()
				for al in self.alignments:
					if al[0]==maxLengthIndex:
						tlindexes.append(al[1])
				
				
				for tlindex in tlindexes:
					#GeneraliseInTL=True
					#if len(parsed_restrictions[maxLengthIndex]) >= len(parsed_tl_lex[tlindex]):
					#	if parsed_tl_lex[tlindex][-1] == parsed_restrictions[maxLengthIndex][len(parsed_tl_lex[tlindex])-1]:
					#		GeneraliseInTL=False
									
					for tlindex in tlindexes:
						#if (GeneraliseInTL and parsed_tl_lex[tlindex][-1]==parsed_sl_lex[maxLengthIndex][-1]) and get_tag_group_from_tag(parsed_tl_lex[tlindex][-1],taggroups,parsed_tl_lex[tlindex][0])==get_tag_group_from_tag(parsed_sl_lex[maxLengthIndex][-1],taggroups,parsed_sl_lex[maxLengthIndex][0]):
						if parsed_tl_lex[tlindex][-1]==parsed_sl_lex[maxLengthIndex][-1] and get_tag_group_from_tag(parsed_tl_lex[tlindex][-1],AT_LexicalTagsProcessor.taggroups,parsed_tl_lex[tlindex][0])==get_tag_group_from_tag(parsed_sl_lex[maxLengthIndex][-1],AT_LexicalTagsProcessor.taggroups,parsed_sl_lex[maxLengthIndex][0]):
							self.tl_lexforms[tlindex]=get_lemma(self.tl_lexforms[tlindex])+u"<"+u"><".join(parsed_tl_lex[tlindex][:-1])+u"><*"+get_tag_group_from_tag(parsed_tl_lex[tlindex][-1],AT_LexicalTagsProcessor.taggroups,parsed_tl_lex[tlindex][0])+u">"	
							if len(generalisedTLIndexes[tlindex]) > 0:
								self.tl_lexforms[tlindex]=self.tl_lexforms[tlindex]+u"<"+u"><".join(generalisedTLIndexes[tlindex])+u">"
				
#			if DEBUG:
#				print >> sys.stderr, "Preliminary result: "+self.__repr__()
#			for i in range(len(generalisedSLIndexes)):
#				if len(generalisedSLIndexes[i]) > 0:
#					self.sl_lexforms[i]=self.sl_lexforms[i]+u"<"+u"><".join(generalisedSLIndexes[i])+u">"
#			for i in range(len(generalisedTLIndexes)):
#				if len(generalisedTLIndexes[i]) > 0:
#					self.tl_lexforms[i]=self.tl_lexforms[i]+u"<"+u"><".join(generalisedTLIndexes[i])+u">"
						
			if DEBUG:
				print >>sys.stderr, "Result: "+self.__repr__()
				print >>sys.stderr, "------------------------\n"
			
			
			self.parsed_sl_lexforms[:]=[]
			for unparsedsl in self.sl_lexforms:
				lexform_obj=AT_LexicalForm()
				lexform_obj.parse(unparsedsl)
				self.parsed_sl_lexforms.append(lexform_obj)
			self.parsed_tl_lexforms[:]=[]
			for unparsedtl in self.tl_lexforms:
				lexform_obj=AT_LexicalForm()
				lexform_obj.parse(unparsedtl)
				self.parsed_tl_lexforms.append(lexform_obj)
			
			
			return True
		
		else:
			
			if DEBUG:
				print >>sys.stderr, "AT couldn't be generalised"
				print >>sys.stderr, "------------------------\n"
			
			self.parsed_sl_lexforms[:]=[]
			for unparsedsl in self.sl_lexforms:
				lexform_obj=AT_LexicalForm()
				lexform_obj.parse(unparsedsl)
				self.parsed_sl_lexforms.append(lexform_obj)
			self.parsed_tl_lexforms[:]=[]
			for unparsedtl in self.tl_lexforms:
				lexform_obj=AT_LexicalForm()
				lexform_obj.parse(unparsedtl)
				self.parsed_tl_lexforms.append(lexform_obj)
			
			return False		
		
	def parse(self, mystring, parseTlLemmasFromDic=False):
		
		self.sl_lexforms=list()
		self.tl_lexforms=list()
		self.parsed_sl_lexforms=list()
		self.parsed_tl_lexforms=list()
		self.alignments=list()
		self.restrictions=list()
		self.parsed_restrictions=list()
		
		fields=mystring.split(u'|')
		if len(fields) >= 4:
			mysllex=fields[0].strip().split(u" ")
			for lexform in mysllex:
				
				lexform_obj=AT_LexicalForm()
				lexform_obj.parse(lexform,removeUnderscoreFromLemma=True)
				self.parsed_sl_lexforms.append(lexform_obj)
				
				#this code should be removed at some point
				lemma=get_lemma(lexform)
				tags=get_tags(lexform)
				self.sl_lexforms.append(lemma.replace(u"_",u" ")+tags)
				
			
			mytllex=fields[1].strip().split(u" ")
			for lexform in mytllex:
				lexform_obj=AT_LexicalForm()
				lexform_obj.parse(lexform,removeUnderscoreFromLemma=True)
				self.parsed_tl_lexforms.append(lexform_obj)
				
				#this code should be removed at some point
				lemma=get_lemma(lexform)
				tags=get_tags(lexform)
				self.tl_lexforms.append(lemma.replace(u"_",u" ")+tags)
			
			myals=fields[2].strip().split(u" ")
			for al in myals:
				parts=al.split(u':')
				self.alignments.append((int(parts[0]),int(parts[1])))
			
			myrestrictions=fields[3].strip().split(u" ")
			for resi,res in enumerate(myrestrictions):
				resobj =AT_Restriction()
				if res == u"EMPTY":
					resobj.set_pos(self.parsed_sl_lexforms[resi].get_pos())
				else:
					#if len(res.strip()) > 0:
					resobj.parse(res)
				self.parsed_restrictions.append(resobj)
				
				#this code should be removed at some point
				self.restrictions.append(res)
			
			if parseTlLemmasFromDic and len(fields) >= 5:
				self.tl_lemmas_from_dictionary=list()
				#mytldic=fields[4].strip().split(u" ")
				mytldic=fields[4].split(u" ")
				for tllemma in mytldic:
					self.tl_lemmas_from_dictionary.append(tllemma.replace(u"_",u" "))
	
	def is_restriction_ending_in_empty_tag(self):
		for res in self.parsed_restrictions:
			if len(res.get_tags()) > 0:
				if is_empty_tag(res.get_tags()[-1]):
					return True
		return False
				
	
	def is_word_for_word(self):
		
		#check same number of sl lexforms and tl lexforms
		if len(self.parsed_sl_lexforms)!=len(self.parsed_tl_lexforms):
			return False
		
		#check aligned one by one
		if len(self.parsed_sl_lexforms)!=len(self.alignments):
			return False
		for i in range(len(self.alignments)):
			if self.alignments[i][0]!=i:
				return False
			if self.alignments[i][1]!=i:
				return False
		
		#check restrictions, etc.
		for i in range(len(self.parsed_sl_lexforms)):
			sllexform=self.parsed_sl_lexforms[i]
			tllexform=self.parsed_tl_lexforms[i]
			restriction=self.parsed_restrictions[i]
			
			if sllexform.has_lemma()  or tllexform.has_lemma():
				return False
			
			lenRestrictions=len(restriction.get_lexical_category_plus_tags())
			if u".".join(tllexform.get_lexical_category_plus_tags()[:lenRestrictions]) != u".".join(restriction.get_lexical_category_plus_tags()):
				return False
			if u".".join(tllexform.get_lexical_category_plus_tags()[:lenRestrictions]) != u".".join(sllexform.get_lexical_category_plus_tags()[:lenRestrictions]):
				return False
		
		return True
		
	
	def is_symmetric_difference_empty(self,otherat):
		if len(self.parsed_sl_lexforms) != len(otherat.parsed_sl_lexforms):
			print >> sys.stderr, "Precondition not met"
			exit()
		
		containsMoreGeneralSelf=False
		containsMoreGeneralOther=False
		
		for i in range(len(self.parsed_sl_lexforms)):
			
			sllexself=self.parsed_sl_lexforms[i]
			sllexother=otherat.parsed_sl_lexforms[i]
			
			resself=self.parsed_restrictions[i]
			resother=otherat.parsed_restrictions[i]
			
			if sllexself.get_pos() != sllexother.get_pos():
				print >> sys.stderr, "Precondition not met"
				exit()
			
			if sllexself.has_lemma() and not sllexother.has_lemma():
				containsMoreGeneralOther=True
			if not sllexself.has_lemma() and sllexother.has_lemma():
				containsMoreGeneralSelf=True
			
			if sllexself.get_num_generalised_tags() > sllexother.get_num_generalised_tags():
				if sllexself.get_tags()[:-sllexself.get_num_generalised_tags()] == sllexother.get_tags()[:-sllexself.get_num_generalised_tags()]: 
					containsMoreGeneralSelf=True
			if sllexself.get_num_generalised_tags() < sllexother.get_num_generalised_tags():
				if sllexself.get_tags()[:-sllexother.get_num_generalised_tags()] == sllexother.get_tags()[:-sllexother.get_num_generalised_tags()]:
					containsMoreGeneralOther=True
			
			if len(resself.get_tags()) < len(resother.get_tags()):
				if resself.get_tags() == resother.get_tags()[:len(resself.get_tags())]:
					containsMoreGeneralSelf=True
			if len(resself.get_tags()) > len(resother.get_tags()):
				if resother.get_tags() == resself.get_tags()[:len(resother.get_tags())]:
					containsMoreGeneralOther=True
		
		return not (containsMoreGeneralSelf and containsMoreGeneralOther)
				
	
	#Test whether the parameter "otherat" has the same left side that the current at
	def has_same_left_side(self,otherat):
		if len(self.parsed_sl_lexforms) != len(otherat.parsed_sl_lexforms):
			return False
		for i in range(len(self.sl_lexforms)):
			if self.parsed_sl_lexforms[i]!=otherat.parsed_sl_lexforms[i]:
				return False
		return True
	
	def is_restriction_of_generalised_tags_empty(self):
		for i,sllex in enumerate(self.parsed_sl_lexforms):
			generalisedFeatureNames=sllex.get_generalised_feature_names()
			restDict=self.parsed_restrictions[i].get_tags_with_feature_names_as_dict()
			for featureName in generalisedFeatureNames:
				if featureName in restDict.keys():
					return False
		return True
	

	def matches_bilphrase(self,bilphrase,checkRestrictions=True, flexibleRestrictions=True):
		return self.is_subset_of_this(bilphrase, checkRestrictions, flexibleRestrictions, checkingBilphrase=True)
	
	def is_struct_compatible_with(self,otherat):
		if len(self.parsed_sl_lexforms) != len(otherat.parsed_sl_lexforms):
			return False
		if len(self.parsed_tl_lexforms) != len(otherat.parsed_tl_lexforms):
			return False
		
		for i in range(len(self.parsed_sl_lexforms)):
			if self.parsed_sl_lexforms[i].get_pos() != otherat.parsed_sl_lexforms[i].get_pos():
				return False
		
		for i in range(len(self.parsed_tl_lexforms)):
			if self.parsed_tl_lexforms[i].get_pos() != otherat.parsed_tl_lexforms[i].get_pos():
				return False  

		return True
	
	#Test whether the parameter "otherat" is a subset of the current at
	def is_subset_of_this(self,otherat, checkRestrictions=True, flexibleRestrictions=True,checkingBilphrase=False):
		if len(self.parsed_sl_lexforms) != len(otherat.parsed_sl_lexforms):
			return False
			
		for i in range(len(self.parsed_sl_lexforms)):
			#Check lemmas
			restrictionCheckResult=True
			#if checkRestrictions and not self.parsed_sl_lexforms[i].has_lemma():
			if checkRestrictions:
				#if not otherat.parsed_sl_lexforms[i].has_lemma() or checkingBilphrase:
				if flexibleRestrictions:
					otherAtResDict=otherat.parsed_restrictions[i].get_tags_with_feature_names_as_dict()
					otherAtSlDict=otherat.parsed_sl_lexforms[i].get_tags_with_feature_names_as_dict()
					selfResDict=self.parsed_restrictions[i].get_tags_with_feature_names_as_dict()
					for featureName in selfResDict.keys():
						valueOfRes=selfResDict[featureName]
						tagType,feat,number =parse_special_tag(valueOfRes)
						
						if tagType == AT_SpecialTagType.RESTRICTION_CHANGING or tagType == AT_SpecialTagType.RESTRICTION_CONSTANT:
							restrictionConstant=True
							slvalue=otherat.parsed_sl_lexforms[i].get_tags_with_feature_names_as_dict()[featureName]
							if featureName in otherat.parsed_restrictions[i].get_tags_with_feature_names_as_dict():
								tlvalue=otherat.parsed_restrictions[i].get_tags_with_feature_names_as_dict()[featureName]
							else:
								tlvalue=slvalue
							if slvalue != tlvalue:
								restrictionConstant=False
							if tagType == AT_SpecialTagType.RESTRICTION_CHANGING and restrictionConstant:
								restrictionCheckResult=False
							if tagType == AT_SpecialTagType.RESTRICTION_CONSTANT and not restrictionConstant:
								restrictionCheckResult=False
						else:
							if not featureName in otherAtResDict:
								if checkingBilphrase:									
									#if bilphrase does not have that feature name
									#in its restrictions, it means that it doesn't change between SL and TL
									if featureName not in otherAtSlDict:
										restrictionCheckResult=False
									elif otherat.parsed_sl_lexforms[i].get_tags_with_feature_names_as_dict()[featureName] != valueOfRes:
										restrictionCheckResult=False
								else:
									restrictionCheckResult=False
							elif otherAtResDict[featureName]!=selfResDict[featureName]:
								restrictionCheckResult=False
				else:
					restrictionCheckResult=self.parsed_restrictions[i].get_tags()==otherat.parsed_restrictions[i].get_tags()
			
			if not restrictionCheckResult:
				return False
			
			if not (  not self.parsed_sl_lexforms[i].has_lemma() or (self.parsed_sl_lexforms[i].has_lemma() and self.parsed_sl_lexforms[i].get_lemma() == otherat.parsed_sl_lexforms[i].get_lemma()) ):
				return False

			#if not ( ( not self.parsed_sl_lexforms[i].has_lemma() and restrictionCheckResult==True ) or (self.parsed_sl_lexforms[i].has_lemma() and self.parsed_sl_lexforms[i].get_lemma() == otherat.parsed_sl_lexforms[i].get_lemma()) ):
			#	return False
			
			#must have same pos
			if self.parsed_sl_lexforms[i].get_pos() != otherat.parsed_sl_lexforms[i].get_pos():
				return False
			
			tagsself=self.parsed_sl_lexforms[i].get_tags()
			tagsother=otherat.parsed_sl_lexforms[i].get_tags()
			tagsotherwithgroups=otherat.parsed_sl_lexforms[i].get_tags_with_feature_names()
			
			#Must have same number of tags
			if len(tagsself) != len(tagsother):
				return False
			
			#Same tags or concrete tag belongs to generalised group
			for j in range(len(tagsself)):
				if not ( tagsself[j]==tagsother[j] or (tagsself[j][0]==u"*" and  tagsself[j][1:] ==  tagsotherwithgroups[j].feature_name   ) ):
					return False

		return True
	
	#TODO: This method and the previous one share too much code
	def apply(self,slsegment,lemmastl,restrictions):
		result=list()
		for i in range(len(self.parsed_tl_lexforms)):
			tllexform=self.parsed_tl_lexforms[i]
			outputLexform=AT_LexicalForm()
			
			#lexical category
			outputLexform.set_pos(tllexform.get_pos())
			
			#lemma
			if tllexform.has_lemma():
				outputLexform.set_lemma(tllexform.get_lemma())
			else:
				outputLexform.set_lemma(lemmastl[self.get_sl_words_aligned_with(i)[0]])
			
			#morphological inflection tags
			outputTags=list()
			for tag in tllexform.get_tags():
				tagtype,feature,ref=parse_special_tag(tag)
				if tagtype == AT_SpecialTagType.NO_SPECIAL:
					outputTags.append(tag)
				elif tagtype == AT_SpecialTagType.FOLLOW_ALIGNMENT:
					alignedSL=self.get_sl_words_aligned_with(i)[0]
					outputTags.append(slsegment[alignedSL].get_tags_with_feature_names_as_dict()[feature] )
				elif tagtype == AT_SpecialTagType.SPECIFIED_SL:
					outputTags.append(slsegment[ref].get_tags_with_feature_names_as_dict()[feature] )
				elif tagtype == AT_SpecialTagType.CHECK_BIDIX:
					if feature in restrictions[ref].get_tags_with_feature_names_as_dict():
						outputTags.append(restrictions[ref].get_tags_with_feature_names_as_dict()[feature] )
					else:
						outputTags.append(slsegment[ref].get_tags_with_feature_names_as_dict()[feature] )
				else:
					raise RuntimeError()
					
			outputLexform.set_tags(outputTags) 
			result.append(outputLexform)
		return result
	
	#TODO: This method and the previous one share too much code
	def matches_segment(self,segment,restrictions,restrictionPrefixMatching):
		if len(self.parsed_sl_lexforms) != len(segment):
			return False
		
		numUnknown=len([ lf for lf in segment if lf.is_unknown()])
		if numUnknown > 0:
			return False
		
		for i in range(len(segment)):
			if self.parsed_sl_lexforms[i].get_pos() != segment[i].get_pos():
				return False
			tagsself=self.parsed_sl_lexforms[i].get_tags()
			tagsother=segment[i].get_tags()
			tagsotherDict=segment[i].get_tags_with_feature_names_as_dict()
			tagsotherwithgroups=segment[i].get_tags_with_feature_names()
			
			resself=self.parsed_restrictions[i]
			resselfDict=resself.get_tags_with_feature_names_as_dict()
			
			resother=restrictions[i]
			resSegmentDict=resother.get_tags_with_feature_names_as_dict()
			#Same tags or concrete tag belongs to generalised group
			for j in range(len(tagsself)):
				if not ( tagsself[j]==tagsother[j] or (tagsself[j][0]==u"*" and  tagsself[j][1:] ==  tagsotherwithgroups[j].feature_name   ) ):
					return False
			
			#lemmas!!!
			if self.parsed_sl_lexforms[i].has_lemma():
				if segment[i].get_lemma() != self.parsed_sl_lexforms[i].get_lemma():
					return False
			else:
				#same restrictions or prefix if it is allowed
				if restrictionPrefixMatching:
					if not ( len(resother) >= len(resself) and resother[:len(resself)]== resself):
						return False
				else:
					for featName in resselfDict.keys():
						if featName in resSegmentDict.keys():
							if resselfDict[featName] != resSegmentDict[featName]:
								return False
						else:
							if featName in tagsotherDict:
								if resselfDict[featName] != tagsotherDict[featName]:
									return False
							else:
								return False
			
		return True
	
	def is_bilphrase_reproducible(self,bilphrase):
		if not self.matches_bilphrase(bilphrase):
			print >>sys.stderr, "WARNING. Testing if a bilphrase which does not match left side is reproducible"
			return False
		
		tlreference=bilphrase.parsed_tl_lexforms
		
		tlobtained=list()
		for tlindex in range(len(self.parsed_tl_lexforms)):
			tllex=self.parsed_tl_lexforms[tlindex]
			
			lemma=tllex.get_lemma()
			pos=tllex.get_pos()
			tags=copy.deepcopy(tllex.get_tags())
			
			slindexes=self.get_sl_words_aligned_with(tlindex)
						
			#ONLY ONE SL WORD CAN BE ALIGNED
			if len(slindexes) > 0:
				slindex=slindexes[0]
			else:
				slindex=None
			
			if len(lemma)==0:
				#Necesito diccionario, incrustado en bilphrrase
				lemma=bilphrase.tl_lemmas_from_dictionary[slindex]
			
			for tagindex in range(len(tags)):
				tagtype,featureName,slwordindex=parse_special_tag(tags[tagindex])
				
				if tagtype == AT_SpecialTagType.FOLLOW_ALIGNMENT:
					tagsofslaligned=bilphrase.parsed_sl_lexforms[slindex].get_tags_with_feature_names_as_dict()
					tags[tagindex]=tagsofslaligned[featureName]
					if not tags[tagindex]:
						tags[tagindex]=u"__ERROR__TAG__"
				elif tagtype == AT_SpecialTagType.SPECIFIED_SL:
					tags[tagindex]=bilphrase.parsed_sl_lexforms[slwordindex].get_tags_with_feature_names_as_dict()[featureName]
				elif tagtype == AT_SpecialTagType.CHECK_BIDIX:
					restriction=bilphrase.parsed_restrictions[slwordindex]
					sllexform=bilphrase.parsed_sl_lexforms[slwordindex]
					if featureName in restriction.get_tags_with_feature_names_as_dict():
						tags[tagindex]=restriction.get_tags_with_feature_names_as_dict()[featureName]
					else:
						tags[tagindex]=sllexform.get_tags_with_feature_names_as_dict()[featureName]
				
			tllf=AT_LexicalForm()
			tllf.set_values(lemma,pos,tags)
			tlobtained.append(tllf)
		
		#debug("Comparing "+str(tlreference)+" with "+str(tlobtained))
		if len(tlreference)!=len(tlobtained):
			return False
		
		for i in range(len(tlreference)):
			if tlreference[i].get_tags() != tlobtained[i].get_tags():
				return False
			if tlreference[i].get_pos() != tlobtained[i].get_pos():
				return False
		
		for i in range(len(tlreference)):
			if lowercase_first_letter(tlreference[i].get_lemma())!=lowercase_first_letter(tlobtained[i].get_lemma()):
				return False
		
		return True	
	
	def aligned_words_of_open_categories_match_dictionary_translation(self,closedCategoriesSet,dictionaryTranslations,singleAlignedtoConsiderContrary=True,openMustBeAlignedWithOpen=False):
		for i in range(len(self.parsed_sl_lexforms)):
			if self.parsed_sl_lexforms[i].get_pos() not in closedCategoriesSet:
				atLeastAlignedWithOneOpen=False
				atLeastOneMatches=False
				for j in self.get_tl_words_aligned_with(i):
					if self.parsed_tl_lexforms[j].get_pos() not in closedCategoriesSet:
						atLeastAlignedWithOneOpen=True
						if compare_lowercase_first_letter(dictionaryTranslations[i],self.parsed_tl_lexforms[j].get_lemma()) and self.parsed_restrictions[i].get_pos() == self.parsed_tl_lexforms[j].get_pos():
							atLeastOneMatches=True
				if not atLeastOneMatches and atLeastAlignedWithOneOpen:
					atLeastOneMatchesContrary=False
					for k in self.get_tl_words_aligned_with(i):
						for m in self.get_sl_words_aligned_with(k):
							if dictionaryTranslations[m]==self.parsed_tl_lexforms[k].get_lemma() and self.parsed_restrictions[m].get_pos() == self.parsed_tl_lexforms[k].get_pos():
								atLeastOneMatchesContrary=True
					if not atLeastOneMatchesContrary or (len(self.get_tl_words_aligned_with(i)) > 1 and singleAlignedtoConsiderContrary):
						return False
				elif not atLeastOneMatches and not atLeastAlignedWithOneOpen and openMustBeAlignedWithOpen:
					return False
					
		
		for j in range(len(self.parsed_tl_lexforms)):
			if self.parsed_tl_lexforms[j].get_pos() not in closedCategoriesSet:
				atLeastAlignedWithOneOpen=False
				atLeastOneMatches=False
				for i in self.get_sl_words_aligned_with(j):
					atLeastAlignedWithOneOpen=True
					if self.parsed_sl_lexforms[i].get_pos() not in closedCategoriesSet:
						if compare_lowercase_first_letter(dictionaryTranslations[i],self.parsed_tl_lexforms[j].get_lemma()) and self.parsed_restrictions[i].get_pos() == self.parsed_tl_lexforms[j].get_pos():
							atLeastOneMatches=True
				if not atLeastOneMatches and atLeastAlignedWithOneOpen:
					atLeastOneMatchesContrary=False
					for k in self.get_sl_words_aligned_with(j):
						for m in self.get_tl_words_aligned_with(k):
							if dictionaryTranslations[k]==self.parsed_tl_lexforms[m].get_lemma() and self.parsed_restrictions[k].get_pos() == self.parsed_tl_lexforms[m].get_pos():
								atLeastOneMatchesContrary=True
					if not atLeastOneMatchesContrary or (len(self.get_sl_words_aligned_with(j)) > 1 and singleAlignedtoConsiderContrary):
						return False
				elif not atLeastOneMatches and not atLeastAlignedWithOneOpen and openMustBeAlignedWithOpen:
					return False
		return True

	def get_specificity_level(self):
		level=1
		maxtags=1
		lexicalisedwords=0
		for restriction in self.parsed_restrictions:
			level+=len(restriction.get_tags())
		for sllexform in self.parsed_sl_lexforms:
			if sllexform.has_lemma():
				lexicalisedwords+=1
			for tag in sllexform.get_tags():
				special_type,ignore,ignore=parse_special_tag(tag)
				if special_type == AT_SpecialTagType.NO_SPECIAL:
					level+=1
			maxtags+=2*len(sllexform.get_tags())
		
		return lexicalisedwords*(maxtags+1)+level
		
		
	
	#No longer used
	def add_restrictions_to_sl_side(self):
		newsl_lexforms=list()
		for i in range(len(self.sl_lexforms)):
			newsltagslist=list()
			lemma=get_lemma(self.sl_lexforms[i])
			sltagsl= parse_tags(self.sl_lexforms[i])
			restrictionsl=parse_tags(self.restrictions[i])
			for res in restrictionsl:
				newsltagslist.append(u"RES"+res)
			for sltag in sltagsl:
				newsltagslist.append(sltag)
				
			newsl_lexforms.append(unparse_lex_form(lemma,newsltagslist))
			
		self.sl_lexforms=newsl_lexforms



class AT_FeatureNameValuePair(object):
	def __init__(self,featureName,value):
		self.feature_name=featureName
		self.feature_value=value

	

class AT_GeneralisationOptions(object):
	VALUE_FOR_RESTRICTION_ALL=0
	VALUE_FOR_RESTRICTION_TBDETERMINED=1
	VALUE_FOR_RESTRICTION_TBDETERMINEDANDMF=2
	VALUE_FOR_RESTRICTION_TBDETERMINEDANDCHANGE=3
	VALUE_FOR_RESTRICTION_TRIGGERINGCHANGE=4
	
	def __init__(self):
		self.genWhenEmptySLCats=list()
		self.genWhenEmptyTLCats=list()
		self.fromRightToLeft=False
		self.refToBiling=False
		self.addRestrictionsToEveryTag=False
		self.differentRestrictionOptions=False
		self.possibleValuesForRestrictions=AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_ALL
		self.generalise=True
		self.triggeringLimitedLength=False
		self.triggeringNoGoodDiscarded=False
		self.discardRestrictionsNotImproving=False
		self.generaliseNonMatchingToo=False
		self.unlexicaliseUnalignedSL=False
		self.countAtributeChanges=dict()
		self.dontGeneraliseAllInstancesTogether=False
		self.calculateGeneralisableAttributesLikeInPaper=False
	
	def set_calculateGeneralisableAttributesLikeInPaper(self,p_calcgen):
		self.calculateGeneralisableAttributesLikeInPaper=p_calcgen
	
	def set_genWhenEmptySLCats(self,p_genWhenEmptySLCats ):
		self.genWhenEmptySLCats=p_genWhenEmptySLCats
	
	def set_genWhenEmptyTLCats(self, p_genWhenEmptyTLCats):
		self.genWhenEmptyTLCats=p_genWhenEmptyTLCats
		
	def set_fromRightToLeft(self, p_frtl):
		self.fromRightToLeft=p_frtl
	
	def set_differentRestrictionOptions(self,p_dfro):
		self.differentRestrictionOptions=p_dfro
	
	def set_refToBiling(self,p_refToBiling):
		self.refToBiling=p_refToBiling
	
	def set_possibleValuesForRestrictions(self,p_pres):
		self.possibleValuesForRestrictions=p_pres
	
	def set_addRestrictionsForEveryTag(self,p_resevtag):
		self.addRestrictionsToEveryTag=p_resevtag
	
	def set_generalise(self, p_generalise):
		self.generalise=p_generalise
	
	def set_triggeringLimitedLength(self,p_lml):
		self.triggeringLimitedLength=p_lml
	
	def set_triggeringNoGoodDiscarded(self,p_ngd):
		self.triggeringNoGoodDiscarded=p_ngd
	
	def set_discardRestrictionsNotImproving(self,p_drni):
		self.discardRestrictionsNotImproving=p_drni
	
	def set_generaliseNonMatchingToo(self,p_gnmt):
		self.generaliseNonMatchingToo=p_gnmt
	
	def set_unlexicaliseUnalignedSL(self,p_uusl):
		self.unlexicaliseUnalignedSL=p_uusl
	
	def get_genWhenEmptySLCats(self):
		return self.genWhenEmptySLCats
	
	def set_count_attribute_changes(self,filed):
		for line in filed:
			line=line.strip()
			parts=line.split("\t")
			lexCategory=parts[0]
			counts=eval(parts[1].replace("<type 'int'>","int"))
			self.countAtributeChanges[lexCategory]=counts
	
	def set_dontGeneraliseAllInstancesTogether(self,p_dgai):
		self.dontGeneraliseAllInstancesTogether=p_dgai
	
	def get_count_attribute_changes(self):
		return self.countAtributeChanges
	
	def get_genWhenEmptyTLCats(self):
		return self.genWhenEmptyTLCats
	
	def is_calculateGeneralisableAttributesLikeInPaper(self):
		return self.calculateGeneralisableAttributesLikeInPaper
	
	def is_fromRightToLeft(self):
		return self.fromRightToLeft
	
	def is_refToBiling(self):
		return self.refToBiling
	
	def is_differentRestrictionOptions(self):
		return self.differentRestrictionOptions
	
	def get_possibleValuesForRestrictions(self):
		return self.possibleValuesForRestrictions
	
	def is_addRestrictionsForEveryTag(self):
		return self.addRestrictionsToEveryTag
	
	def is_generalise(self):
		return self.generalise
	
	def is_triggeringLimitedLength(self):
		return self.triggeringLimitedLength
	
	def is_triggeringNoGoodDiscarded(self):
		return self.triggeringNoGoodDiscarded
	
	def is_discardRestrictionsNotImproving(self):
		return self.discardRestrictionsNotImproving
	
	def is_generaliseNonMatchingToo(self):
		return self.generaliseNonMatchingToo
	
	def is_unlexicaliseUnalignedSL(self):
		return self.unlexicaliseUnalignedSL
	
	def is_dontGeneraliseAllInstancesTogether(self):
		return self.dontGeneraliseAllInstancesTogether
	
class AT_AbstractClassPosAndTags(object):
	def __init__(self):
		self.pos=u""
		self.tags=list()
		self.categories=list()
		
	def parse(self, mystr):
		parsed_tags=parse_tags(mystr)
		self.pos=parsed_tags[0]
		self.tags=parsed_tags[1:]
		self.compute_categories_of_tags()
	
	def compute_categories_of_tags(self):
		if AT_LexicalTagsProcessor.taggroups:
			self.categories[:]=[]
			for tag in self.tags:
				self.categories.append(get_tag_group_from_tag(tag,AT_LexicalTagsProcessor.taggroups,self.pos))
		#else:
		#	print >> sys.stderr, "WARNING: No tag groups defined. Cannot obtain feature names of tags"
	
	def unparse(self):
		raise NotImplementedError("Please Implement this method")
	
	def get_num_generalised_tags(self):
		generalisedTags=[ tag for tag in self.tags if parse_special_tag(tag)[0] != AT_SpecialTagType.NO_SPECIAL ]
		return len(generalisedTags)
	
	def get_generalised_feature_names(self):
		cdict=self.get_tags_with_feature_names_as_dict()
		return [ category for category in cdict.keys() if parse_special_tag(cdict[category])[0] != AT_SpecialTagType.NO_SPECIAL ]
	
	def get_tags_with_feature_names(self):
		outputlist=list()
		for i in range(len(self.tags)):
			pair=AT_FeatureNameValuePair(self.categories[i],self.tags[i])
			outputlist.append(pair)
		return outputlist
	def get_tags_with_feature_names_as_dict(self):
		outputdict=dict()
		for i in range(len(self.tags)):
			outputdict[self.categories[i]]=self.tags[i]
		return outputdict
	
	def get_lexical_category_plus_tags(self):
		outputlist=list()
		outputlist.append(self.pos)
		outputlist.extend(self.tags)
		return outputlist	

	def set_tag_value_for_name(self,featureName, featureValue ):		
		position=self.categories.index(featureName)
		self.tags[position]=featureValue
	
	def remove_tag_from_category(self,featureName):
		if featureName in self.categories:
			position=self.categories.index(featureName )
			self.categories.pop(position)
			self.tags.pop(position)
	
	def get_categories(self):
		return self.categories	

	def get_tags(self):
		return self.tags
	
	def set_tags(self,p_tags):
		self.tags=p_tags
		self.compute_categories_of_tags()
	
	def append_tag(self,tag):
		self.tags.append(tag)
		self.compute_categories_of_tags()
	
	def remove_all_inflection_tags(self):
		self.tags=[]
		self.compute_categories_of_tags()
	
	def get_pos(self):
		return self.pos
	def set_pos(self, p_pos):
		self.pos=p_pos
	
	def __eq__(self, other):
		if self.pos != other.pos:
			return False
		if self.tags != other.tags:
			return False
		return True

class AT_Restriction(AT_AbstractClassPosAndTags):
	def __init__(self):
		AT_AbstractClassPosAndTags.__init__(self)
		self.special=u""
			
	def parse(self,resstr):
		if resstr.startswith(u"__"):
			self.special=resstr
		elif len(resstr) == 0:
			self.special="EMPTY"
		else:
			AT_AbstractClassPosAndTags.parse(self,resstr)
			
	def is_special(self):
		return len(self.special) > 0
	
	def unparse(self,useSecondEmptyRepresentation=False):
		if self.is_special():
			if self.special==u"__EMPTYRESTRICTION__" and useSecondEmptyRepresentation:
				return u"EMPTY"
			else:
				return self.special
		else:
			return unparse_tags([self.pos]+self.tags)
	
	def remove_longest_suffix(self,referencedFeatureNames):
		for i in reversed(range(len(self.tags))):
			if self.categories[i] in referencedFeatureNames: #or self.tags[i] in ["GD","ND","PD"]:
				self.tags=self.tags[:i]
				self.categories=self.categories[:i]
			else:
				break
	

	def __eq__(self, other):
		if not isinstance(other, AT_Restriction):
			return False
		if not AT_AbstractClassPosAndTags.__eq__(self,other):
			return False
		if self.special != other.special:
			return False
		return True
	def __ne__(self, other):
		return not self.__eq__(other)	
	
	def __repr__(self):
		output=(u".".join([self.pos]+self.tags)).encode('utf-8')
		return output
		#if len(output) > 0:
		#	return output
		#else:
		#	return "__EMPTYRESTRICTION__" 
	

class AT_LexicalForm(AT_AbstractClassPosAndTags):
	def __init__(self):
		AT_AbstractClassPosAndTags.__init__(self)
		self.lemma=u""
		self.unknown=False
	
	def set_values(self,p_lemma,p_pos,p_tags):
		self.set_lemma(p_lemma)
		self.set_pos(p_pos)
		self.set_tags(p_tags)
	
	
	def parse(self,lexformstr,removeUnderscoreFromLemma=False):
		
		#debug("parsing: "+lexformstr.encode('utf-8'))
		
		if lexformstr.startswith("*"):
			self.unknown=True
			self.lemma=lexformstr[1:]
		else:
			if removeUnderscoreFromLemma:
				self.lemma=get_lemma(lexformstr).replace(u"_",u" ")
			else:
				self.lemma=get_lemma(lexformstr).replace(u"_",u" ")
			AT_AbstractClassPosAndTags.parse(self,lexformstr)
		
	def unparse(self,replaceSpacesWithUnderscore=False,removeEmptyTags=False):
		if removeEmptyTags:
			cleantags=[ tag for tag in self.tags if not is_empty_tag(tag) ]
		else:
			cleantags=self.tags
		
		if self.is_unknown():
			return u"*"+self.lemma
		else:
			if replaceSpacesWithUnderscore:
				return escape_lemma(self.lemma.replace(u" ",u"_"))+unparse_tags([self.pos]+cleantags)
			else:
				return escape_lemma(self.lemma)+unparse_tags([self.pos]+cleantags)
	
	def is_unknown(self):
		return self.unknown
	
	def has_lemma(self):
		return len(self.lemma) > 0
	
	def get_lemma(self):
		return self.lemma
	
	
	def remove_lemma(self):
		self.set_lemma(u"")
	
	def set_lemma(self, lemmaval):
		self.lemma=lemmaval
	
	def is_unk_or_punct(self):
		return self.is_unknown() or self.get_pos() in [u"sent",u"guio",u"cm",u"rpar",u"lpar",u"lquest",u"rquest"]
	
	def __eq__(self, other):
		if not isinstance(other, AT_LexicalForm):
			return False
		if self.lemma != other.lemma:
			return False
		if not AT_AbstractClassPosAndTags.__eq__(self,other):
			return False
		return True
	def __ne__(self, other):
		return not self.__eq__(other)
	
	def __repr__(self):
		return self.__unicode__().encode('utf-8')
	def __unicode__(self):
		return (self.lemma+u"-"+u".".join([self.pos]+self.tags))
	
	@classmethod
	def create_without_lemma(cls,otherlex):
		lf=AT_LexicalForm()
		lf.set_pos(otherlex.pos)
		lf.set_tags(otherlex.tags)
		return lf 
	
		
class AT_LexicalTagsProcessor(object):
	taggroups = None
	tagsequences = None
	tagsWhichGenerateToBeDetermined=[u"mf",u"sp"]
	
	@staticmethod
	def is_generator_of_to_be_determined_tag(tag):
		return tag in AT_LexicalTagsProcessor.tagsWhichGenerateToBeDetermined
	
	@staticmethod
	def is_to_be_determined_tag(tag):
		return tag.upper() == tag
	
	@staticmethod
	def initialize(taggroups_f,tagsequences_f):
		if taggroups_f:
			tag_groups_file=open(taggroups_f,'r')
			AT_LexicalTagsProcessor.taggroups=read_tag_groups(tag_groups_file)
			tag_groups_file.close()

		if tagsequences_f:
			tagsequencesfile=open(tagsequences_f)
			AT_LexicalTagsProcessor.tagsequences=read_tag_sequences(tagsequencesfile)
			tagsequencesfile.close()
	
	@staticmethod
	def add_explicit_empty_tags(pos,parsed_tags,weAreProcessingRestrictions=False):
		oldtagslist=parsed_tags[:]
		
		if pos in AT_LexicalTagsProcessor.tagsequences:
			newtagslist=list()
			groupsequence=AT_LexicalTagsProcessor.tagsequences[pos]
			for groupid in groupsequence:
				tag=find_tag_from_tag_group_in_tag_sequence(oldtagslist,groupid,AT_LexicalTagsProcessor.taggroups,pos)
				if tag!=None:
					newtagslist.append(tag)
				else:
					newtagslist.append(u"empty_tag_"+groupid)
			
			#NO longer needed
			#if weAreProcessingRestrictions:
			#	lastindexofnotemptytag=-1
			#	for i in range(len(newtagslist)):
			#		if not newtagslist[i].startswith(u"empty_tag_"):
			#			lastindexofnotemptytag=i	
			#	newtagslist=newtagslist[:lastindexofnotemptytag+1]
			return newtagslist
		else:
			return oldtagslist
	@staticmethod
	def get_tag_group_names():
		return AT_LexicalTagsProcessor.taggroups.keys()

def uniprint(unicodestr,erroutput=False,encoding='utf-8'):
	if erroutput:
		print >> sys.stderr, unicodestr.encode(encoding)
	else:
		print unicodestr.encode(encoding)
def unidecode(rawstr,encoding='utf-8'):
	return rawstr.decode(encoding)


def powerset(seq):
    """
    Returns all the subsets of this set. This is a generator.
    """
    if len(seq) <= 1:
        yield seq
        yield []
    else:
        for item in powerset(seq[1:]):
            yield [seq[0]]+item
            yield item

def get_representation_of_sl_generalised_tag(taggroup):
	return u"*"+taggroup

def get_representation_of_tl_generalised_tag_from_aligned_word(taggroup):
	return u"*"+taggroup

def get_representation_of_tl_generalised_tag_from_sl_word(taggroup,position):
	return u"("+unicode(str(position).zfill(3))+taggroup

def get_representation_of_tl_generalised_tag_from_bidix(taggroup,position):
	return u")"+unicode(str(position).zfill(3))+taggroup

def get_representation_of_restriction_not_changing(taggroup):
	return u"["+taggroup

def get_representation_of_restriction_changing(taggroup):
	return u"]"+taggroup


class AT_SpecialTagType:
	FOLLOW_ALIGNMENT=1
	SPECIFIED_SL=4
	CHECK_BIDIX=2
	NO_SPECIAL=3
	RESTRICTION_CONSTANT=5
	RESTRICTION_CHANGING=6

def parse_special_tag(tag):
	if tag.startswith(u"*"):
		return AT_SpecialTagType.FOLLOW_ALIGNMENT,tag[1:],None
	elif tag.startswith(u")"):
		return AT_SpecialTagType.CHECK_BIDIX,tag[4:],int(tag[1:4])
	elif tag.startswith(u"("):
		return AT_SpecialTagType.SPECIFIED_SL,tag[4:],int(tag[1:4])
	elif tag.startswith(u"["):
		return AT_SpecialTagType.RESTRICTION_CONSTANT,tag[1:],None
	elif tag.startswith(u"]"):
		return AT_SpecialTagType.RESTRICTION_CHANGING,tag[1:],None
	else:
		return AT_SpecialTagType.NO_SPECIAL,None,None

def is_empty_tag(tag):
	return tag.startswith(u"empty_tag")


def debug(debugstr):
	if DEBUG:
		print >> sys.stderr, debugstr


def filter_pre_minimisation(bilphrases, finalAlignmentTemplates, subsetsGraph,removeContradictoryATs=False, printNumCorrectUnfilteredBilphrases=False, proportionCorrectBilphrasesThreshold=0.00, takeIntoAccountLowerLevelsInContradictions=True):
	
	if DEBUG:
		print >> sys.stderr, "Proportion correct bilphrases threshold: "+str(proportionCorrectBilphrasesThreshold)
		
		print >> sys.stderr, "Subset graph:"
		print >> sys.stderr, subsetsGraph.to_string().encode('utf-8')
		
		listOfBilphrases=bilphrases.get_all_ats_list()
		print >> sys.stderr, "Bilphrases ("+str(len(listOfBilphrases))+"):"
		for bil in listOfBilphrases:
			print >> sys.stderr, str(bil.id)+": "+str(bil)
		
		listOfAts=finalAlignmentTemplates.get_all_ats_list()
		print >> sys.stderr, "ATs ("+str(len(listOfAts))+"):"
		for at in listOfAts:
			print >> sys.stderr, str(at.id)+": "+str(at)		
	
	atsToRemoveBecauseThreshold=list()
	
	globalReproducibleBilphrases=set()
	#myComputeCorrectAndIncorrectBilphrases=def_computeCorrectAndIncorrectBilphrases_closure(globalReproducibleBilphrases)
	def computeCorrectAndIncorrectBilphrases(myAt):
		
		reproducible_phrases,matching_phrases, num_reproducible_phrases, num_matching_phrases=bilphrases.get_ids_of_matching_and_compatible_phrases(myAt)
		
		if DEBUG:
			print >> sys.stderr, "Computing correct and incorrect bilphrases for AT: "+str(myAt.to_string(removeRestrictionsFromLexicalised=False))
			print >> sys.stderr, "Reproducible: "+str(reproducible_phrases)
			print >> sys.stderr, "Matching: "+str(matching_phrases)
		
		incorrect_phrases=matching_phrases-reproducible_phrases
		myAt.correct_bilphrases=reproducible_phrases
		myAt.incorrect_bilphrases=incorrect_phrases
		
		myAt.num_correct_bilphrases=num_reproducible_phrases
		myAt.num_matching_bilphrases=num_matching_phrases
		
		if myAt.num_correct_bilphrases*1.0/myAt.num_matching_bilphrases >= proportionCorrectBilphrasesThreshold:
			globalReproducibleBilphrases.update(reproducible_phrases)
			for matchingPhraseId in matching_phrases:
				bilphrases.get_by_id(matchingPhraseId).atsmatchingthisbilphrase.add(myAt.id)
			for reproducedPhraseId in reproducible_phrases:
				bilphrases.get_by_id(reproducedPhraseId).atsreproducingthisbilphrase.add(myAt.id)
		else:
			atsToRemoveBecauseThreshold.append(myAt.id)
			
	
	t_start_computingcorrectincorrect=time()
	finalAlignmentTemplates.apply_to_all(computeCorrectAndIncorrectBilphrases)
	t_computingcorrectincorrect=time()-t_start_computingcorrectincorrect
	#print >> sys.stderr, "Time spent computing correct and incorrect bilphrases: "+str(t_computingcorrectincorrect)
	
	print >> sys.stderr, "Ats removed because of threshold:"
	for at_id in atsToRemoveBecauseThreshold:
		at=finalAlignmentTemplates.get_by_id(at_id)
		print >> sys.stderr,str(at.num_correct_bilphrases*1.0/at.num_matching_bilphrases)+" | "+str(at)
		
	if printNumCorrectUnfilteredBilphrases:
		print >> sys.stderr, "ATS_BEFORE_LINEAR_PROG_AND_REMOVING_CONTRADICTIONS"
		for at_id in finalAlignmentTemplates.get_all_ids():
			at=finalAlignmentTemplates.get_by_id(at_id)
			print >> sys.stderr, str(at)+"\t"+str(at.num_correct_bilphrases)+"\t"+str(at.num_matching_bilphrases)
		print >> sys.stderr, "END_ATS_BEFORE_LINEAR_PROG_AND_REMOVING_CONTRADICTIONS"
	
	if DEBUG:
			print >> sys.stderr, "ATs before removing by threshold:"
			for id in finalAlignmentTemplates.get_all_ids():
				print >> sys.stderr, finalAlignmentTemplates.get_by_id(id)
	
	for id in atsToRemoveBecauseThreshold:
		finalAlignmentTemplates.remove(id)
	
	debug("ATs after removing by threshold: ")
	for id in finalAlignmentTemplates.get_all_ids():
		debug(str(finalAlignmentTemplates.get_by_id(id)))
	
	allBilphraseIds=bilphrases.get_all_ids()
	notReproducibleBilphraseIds=set(allBilphraseIds)
	notReproducibleBilphraseIds-=globalReproducibleBilphrases
	
	def removeNotReproducibleBilphrasesFromAts(myAt):
		myAt.correct_bilphrases-=notReproducibleBilphraseIds
		myAt.incorrect_bilphrases-=notReproducibleBilphraseIds
	finalAlignmentTemplates.apply_to_all(removeNotReproducibleBilphrasesFromAts)
	
	print >> sys.stderr, str(len(globalReproducibleBilphrases))+" bilphrases reproducible by any AT/ "+str(len(bilphrases.get_all_ids()))+" total bilphrases"
	
	bilphrasesToDelete=set()
	if removeContradictoryATs:
		if DEBUG:
			print >> sys.stderr, "ATs before removing contradictory ones:"
			for id in finalAlignmentTemplates.get_all_ids():
				print >> sys.stderr, finalAlignmentTemplates.get_by_id(id)
		
		print >>sys.stderr, "Removing contradictory bilingual phrases. Taking into account more particular ATs: "+str(takeIntoAccountLowerLevelsInContradictions)
		finalAlignmentTemplates.remove_contradictory_ats()
		#globalReproducibleBilphrases-=bilphrasesToDelete
		#def removeBilphrasesToDeleteFromAts(myAt):
		#	myAt.correct_bilphrases-=bilphrasesToDelete
		#	myAt.incorrect_bilphrases-=bilphrasesToDelete
		#finalAlignmentTemplates.apply_to_all(removeBilphrasesToDeleteFromAts)
		
		if DEBUG:
			print >> sys.stderr, "ATs after removing contradictory ones:"
			for id in finalAlignmentTemplates.get_all_ids():
				print >> sys.stderr, finalAlignmentTemplates.get_by_id(id)
	
	return finalAlignmentTemplates,globalReproducibleBilphrases,t_computingcorrectincorrect

def group_bilphrases_behaving_equal(selectedAts,reproducibleBilphrasesIds,bilphrases):
	tmpmappings=dict()
	mappings=dict()
	inversemappings=dict()
	syntheticBilphraseSet=AlignmentTemplateSet()
	
	for bid in reproducibleBilphrasesIds:
		bilphrase=bilphrases.get_by_id(bid)
		
		#freeze sets so that they can be used as keys
		bilphrase.atsmatchingthisbilphrase=frozenset(bilphrase.atsmatchingthisbilphrase)
		bilphrase.atsreproducingthisbilphrase=frozenset(bilphrase.atsreproducingthisbilphrase)
		key=(bilphrase.atsmatchingthisbilphrase,bilphrase.atsreproducingthisbilphrase)
		
		if not key in tmpmappings:
			tmpmappings[key]=set()
		tmpmappings[key].add(bid)
	
	newbilphrasesid=0
	for key in tmpmappings:
		newbilphrasesid+=1
		mappings[newbilphrasesid]=tmpmappings[key]
		syntheticBilphrase=None
		for oldbilid in mappings[newbilphrasesid]:
			oldbil=bilphrases.get_by_id(oldbilid)
			if syntheticBilphrase == None:
				syntheticBilphrase=oldbil.fast_clone()
				syntheticBilphrase.freq=0
				syntheticBilphrase.id=newbilphrasesid
			syntheticBilphrase.freq+=oldbil.freq
			inversemappings[oldbilid]=newbilphrasesid
		syntheticBilphraseSet.add(syntheticBilphrase)
	
	if DEBUG:
		for newbild in mappings.iterkeys():
			newbilphrase=syntheticBilphraseSet.get_by_id(newbild)
			debug("Group with id="+str(newbild)+" represented by "+str(newbilphrase))
			for oldid in mappings[newbild]:
				oldbilphrase=bilphrases.get_by_id(oldid)
				debug("\t"+str(oldbilphrase))
	
	#update bilphrase ids in selected ats
	for atid in selectedAts.get_all_ids():
		at=selectedAts.get_by_id(atid)
		newcorrectbilphrases=set()
		newincorrectbilphrases=set()
		for bilid in at.correct_bilphrases:
			newcorrectbilphrases.add(inversemappings[bilid])
		for bilid in at.incorrect_bilphrases:
			newincorrectbilphrases.add(inversemappings[bilid])
		at.correct_bilphrases=newcorrectbilphrases
		at.incorrect_bilphrases=newincorrectbilphrases
	
	return mappings,inversemappings,syntheticBilphraseSet

def minimise_linear_programming(finalAlignmentTemplates,globalReproducibleBilphrases,bilphrases,printNumCorrectUnfilteredBilphrases=False,lambdaForCombining=0.00,relaxRestrictions=False,relaxWeight="len(at_list)+1",useNewScoring=False,restrictionSymmetricDifference=False, moreSpecificRequiresLessFrequent=False,mappingsFromSyntheticBilphrases=None,originalBilphraseSet=None):
	
	globalSolution=list()
	
	ts_preferences=list()
	ts_preparing=list()
	ts_solving=list()
	
	# Este bucle es  totalmente inútil
	# actualmente, para cada llamada a la funcion solo hay un valor en finalAlignmentTemplates.get_l2_maps()
	# Para todos ellos se usa el mismo globalReproducibleBilphrases
	for l2mapPair in finalAlignmentTemplates.get_l2_maps():
		posandrestrictions=l2mapPair[0]
		l2map=l2mapPair[1]
		valuelist=list()
		valuelist.extend(l2map.values())
		at_dict=dict()
		#Recalculate ids
		idAt=0
		for i in range(len(valuelist)):
			for at in valuelist[i]:
				idAt+=1
				at.id=idAt
				at_dict[at.id]=at
				at.clean_subsets()
		t_start_preferences=time()
		
		SUBSET_NOT_COMPUTED=0
		SUBSET_YES=1
		SUBSET_NO=2
		subsetMatrix=list()
		subsetSets=list()
		supersetSets=list()
		
		debug("Computing subsets. Valuelist:")
		for i in range(len(valuelist)):
		#for i in []:
			debug(str(i)+": "+str(valuelist[i][0]))
			subsetMatrix.append(list())
			subsetSets.append(set())
			supersetSets.append(set())
			for j in range(len(valuelist)):
				subsetMatrix[i].append(SUBSET_NOT_COMPUTED)
		
		
		for i in range(len(valuelist)):
		#for i in []:
			comparablei=valuelist[i][0]
			for j in range(len(valuelist)):
				if i!=j:
					if subsetMatrix[i][j]==SUBSET_NOT_COMPUTED:
						comparablej=valuelist[j][0]
						isSubset=comparablei.is_subset_of_this(comparablej)
						if isSubset:
							debug("\t"+str(comparablej)+" is subset of "+str(comparablei))
							#j is subset of i
							subsetMatrix[i][j]=SUBSET_YES
							subsetSets[i].add(j)
							supersetSets[j].add(i)
							
							#all the subsets of j are subsets of i
							for subsetIndex in subsetSets[j]:
								subsetMatrix[i][subsetIndex]=SUBSET_YES
								subsetSets[i].add(subsetIndex)
								supersetSets[subsetIndex].add(i)
								if DEBUG:
									debug("\t\t"+str(valuelist[subsetIndex][0])+" is subset of "+str(valuelist[i][0])+" because:")
									debug("\t\t\t"+str(valuelist[subsetIndex][0])+" is subset of "+str(valuelist[j][0]))
									debug("\t\t\t"+str(valuelist[j][0])+" is subset of "+str(valuelist[i][0]))
						else:
							debug("\t"+str(comparablej)+" is NOT subset of "+str(comparablei))
							subsetMatrix[i][j]=SUBSET_NO

							#all the supersets of j are not subsets of i
							for superIndex in supersetSets[j]:
								subsetMatrix[i][superIndex]=SUBSET_NO
			
		for i in range(len(valuelist)):
			comparablei=valuelist[i][0]
			
			if DEBUG:
				debug("Valuelist["+str(i)+"]")
				for at in valuelist[i]:
					debug("\t"+str(at))
			
			for j in range(len(valuelist)):
				if i!=j:
					comparablej=valuelist[j][0]
					#if comparablei.is_subset_of_this(comparablej) and not comparablej.is_subset_of_this(comparablei):
					if subsetMatrix[i][j] == SUBSET_YES and subsetMatrix[j][i] == SUBSET_NO:
						for at in valuelist[i]:
							for atsub in valuelist[j]:
								at.atswhicharesubset.add(atsub.id)
								if DEBUG:
									debug("("+str(atsub.id)+") "+str(atsub)+" is subset of ("+str(at.id)+") "+str(at))
									debug("\tbecause ("+str(valuelist[j][0].id)+") "+str(valuelist[j][0])+" is subset of ("+str(valuelist[i][0].id)+") "+str(valuelist[i][0])+" and not the other way round")
					if restrictionSymmetricDifference:
						if not comparablei.is_symmetric_difference_empty(comparablej):
							for at in valuelist[i]:
								for atsub in valuelist[j]:
									at.atssymmetricdifferencenotempty.add(atsub.id)
			if DEBUG:				
				for at in valuelist[i]:
					print >> sys.stderr, "Subsets of: ("+str(at.id)+") "+str(at)
					for id in at.atswhicharesubset:
						print >> sys.stderr, "("+str(id)+") "+str(at_dict[id])
					print >> sys.stderr, ""
				debug("")
			
		ts_preferences.append(time()-t_start_preferences)
		
		
		if DEBUG:
			print >> sys.stderr, "Bilphrases: "
			for id in globalReproducibleBilphrases:
				print >> sys.stderr, str(id)+": "+str(bilphrases.get_by_id(id))
				
		
		t_start_preparing=time()
		#Create linear programming problem
		prob = LpProblem("Rules", LpMinimize)
		
		
		#compute maximum specifity level
		maximum_specifity_level=max([ max([at.get_specificity_level() for at in ats]) for ats in valuelist ] )
		total_num_ats=sum([ len(ats) for ats in valuelist ])
		specifity_level_divisor=1.0*maximum_specifity_level*total_num_ats
		
		if DEBUG:
			print >> sys.stderr, "Variables: "
		#create variables
		lp_variables=dict()
		at_list=list()
		atIdsAndFactor=dict()
		variablesAndFactor=list()
		for i in range(len(valuelist)):
			for at in valuelist[i]:
				at_list.append(at)
				var=LpVariable("x"+str(at.id), 0, 1,cat='Integer')
				lp_variables[at.id]=var
				factor=1
				if lambdaForCombining > 0.00:
					totalIncorrect=0
					for bilphrase_id in at.incorrect_bilphrases:
						totalIncorrect+=bilphrases.get_by_id(bilphrase_id).freq
					totalCorrect=0
					for bilphrase_id in at.correct_bilphrases:
						totalCorrect+=bilphrases.get_by_id(bilphrase_id).freq
					if totalIncorrect + totalCorrect > 0:
						factor=(1-lambdaForCombining)+lambdaForCombining*(totalIncorrect*1.0/(totalIncorrect+totalCorrect))
				factor=factor*1.0+ ( at.get_specificity_level()/specifity_level_divisor if useNewScoring else 0.0)
				variablesAndFactor.append((var,factor))
				atIdsAndFactor[at.id]=factor
				if DEBUG:
					print >> sys.stderr, str(at.id)+": "+str(at)+" Factor: "+str(factor)+" Spc. level: "+str(at.get_specificity_level())
					print >> sys.stderr, "OK: "+str(at.correct_bilphrases)+" Wrong: "+str(at.incorrect_bilphrases)
		
		if DEBUG:
			print >> sys.stderr, ""
			print >> sys.stderr, "Restrictions: Each bilphrase must be translated"
		
		varsWhichCorrectlyReproduceBilingualPhrases=dict()
		#create restriction: each bilphrase must be translated by at least one AT
		bilphrase_ids=globalReproducibleBilphrases
		for bil_id in bilphrase_ids:
			var_ids=list()
			for at in at_list:
				if bil_id in at.correct_bilphrases:
					var_ids.append(at.id)
			varsWhichCorrectlyReproduceBilingualPhrases[bil_id]=var_ids
			#restriction: sum var_ids > 0
			
			cname="bilphrase"+str(bil_id)
			myexpression=LpAffineExpression( [ (lp_variables[vari],1) for vari in var_ids ] )
			constraint = LpConstraint(myexpression,sense=constants.LpConstraintGE,name=cname,rhs=1)
			#prob += lpSum([ (lp_variables[vari],1) for vari in var_ids ]) >= 1 , cname 
			prob.constraints[cname]=constraint
			if DEBUG:
				print >> sys.stderr, cname+": "+str(constraint)
		
		if DEBUG:
			print >> sys.stderr, ""
			print >> sys.stderr, "Restrictions: Exceptions must be treated"
		#create restriction: exceptions must be translated 
		
		restrictionsExceptionsTranslated=list()
		
		for i in range(len(at_list)):
			at=at_list[i]
			for bil_id in (at.incorrect_bilphrases & globalReproducibleBilphrases):
				#create expression
				listOfVars=list()
				atsMoreParticularOK=list()
				for j in range(len(at_list)):
					if j!=i and bil_id in at_list[j].correct_bilphrases and at_list[j].id in at.atswhicharesubset and ( not moreSpecificRequiresLessFrequent or (at_list[j].num_correct_bilphrases < at.num_correct_bilphrases ) ):
						#add to expression
						listOfVars.append((lp_variables[at_list[j].id],1))
						atsMoreParticularOK.append(at_list[j].id)
				restrictionsExceptionsTranslated.append((at.id,bil_id,atsMoreParticularOK))
				listOfVars.append((lp_variables[at.id],-1))
				cname="exceptions_"+str(at.id)+"_"+str(bil_id)
				myexpression=LpAffineExpression( [ var for var in listOfVars ] )
				constraint = LpConstraint(myexpression,sense=constants.LpConstraintGE,name=cname,rhs=0)
				prob.constraints[cname]=constraint
				#prob += lpSum(listOfVars) >= 0 , cname
				if DEBUG:
					print >> sys.stderr, cname +": " + str(constraint)
		
		if DEBUG:
			print >> sys.stderr, ""
			print >> sys.stderr, "Restrictions: Most general ATs are better"
		#create restriction: more general ATs are better
		
		
		restrictionsMoreGeneralAreBetter=list()	
		#not used anymore!! Found more elegant solution
		for i in range(len(at_list) if useNewScoring == False else 0):
			at=at_list[i]
			for j in range(len(at_list)):
				atj=at_list[j]
				if j!=i and at.id in atj.atswhicharesubset and at.incorrect_bilphrases == atj.incorrect_bilphrases :
					listOfVars=list()
					listOfVars.append((lp_variables[at.id],-1))
					listOfVars.append((lp_variables[atj.id],1))
					restrictionsMoreGeneralAreBetter.append((at.id,atj.id))
					cname="moregeneral_"+str(at.id)+"_"+str(atj.id)
					myexpression=LpAffineExpression( [ var for var in listOfVars ] )
					constraint = LpConstraint(myexpression,sense=constants.LpConstraintGE,name=cname,rhs=0)
					prob.constraints[cname]=constraint
					if DEBUG:
						print >> sys.stderr, constraint
		
		restrictionsSymmetricDifference=list()
		if restrictionSymmetricDifference:
			for i in range(len(at_list) ):
				at=at_list[i]
				for otherid in at.atssymmetricdifferencenotempty:
					listOfVars=list()
					listOfVars.append((lp_variables[at.id],1))
					listOfVars.append((lp_variables[otherid],1))
					restrictionsSymmetricDifference.append((at.id,otherid))
					cname="symdifference_"+str(at.id)+"_"+str(otherid)
					myexpression=LpAffineExpression( [ var for var in listOfVars ] )
					constraint = LpConstraint(myexpression,sense=constants.LpConstraintLE,name=cname,rhs=1)
					prob.constraints[cname]=constraint
					if DEBUG:
						print >> sys.stderr, constraint
			
		#Create expression to be minimises
		#myexpression=LpAffineExpression( [ (var,1) for var in lp_variables.values() ] )
		myexpression=LpAffineExpression( [ pair for pair in variablesAndFactor ] )
		prob.objective=myexpression
		#prob+=lpSum( [ (var,1) for var in lp_variables.values() ] ) ,  "Objective"
		
		ts_preparing.append(time()-t_start_preparing)
		
		solution=list()
		if not relaxRestrictions:
			t_start_solving=time()
			#Solve problem
			status = prob.solve()
			print >> sys.stderr, "Solving problem"
			print >> sys.stderr, "Status: "+str(LpStatus[status])
					
			
			if status == LpStatusOptimal :
			
				#get solution
				if DEBUG:
					print >> sys.stderr, "Solution"
				for at_id in lp_variables.keys():
					if DEBUG:
						print >> sys.stderr, str(at_id)+": "+str(value(lp_variables[at_id]))
					if value(lp_variables[at_id])==1:
						solution.append(at_dict[at_id])
						#print str(at_id)+": "+at_dict[at_id].__repr__()
						#print str(at_dict[at_id].correct_bilphrases)+str(at_dict[at_id].incorrect_bilphrases)
				
				#useless debug code
				#print "Second is subset of first: "+str(solution[0].is_subset_of_this(solution[1],taggroups))
				#print "First is subset of second: "+str(solution[1].is_subset_of_this(solution[0],taggroups))
				
				#sort Ats from solution (topological sort)
				atidsInSolution=set()
				for at in solution:
					atidsInSolution.add(at.id)
				arcs=list()
				for at in solution:
					for atid in atidsInSolution:
						if atid != at.id and atid in at.atswhicharesubset:
							arcs.append((atid,at.id))
							
				sortedSolution=tsort.tsort(arcs)
				
				#append at the end of the solution ats not connected to anyone in the graph
				sortedSolutionSet=set(sortedSolution)
				remaining= atidsInSolution-sortedSolutionSet
				for atid in remaining:
					sortedSolution.append(atid)
					
				for atid in sortedSolution:
					globalSolution.append(at_dict[atid])
				ts_solving.append(time()-t_start_solving)
				
				if printNumCorrectUnfilteredBilphrases:
					print >> sys.stderr, "ATS_AFTER_LINEAR_PROG"
					for at in globalSolution:
						print >> sys.stderr, str(at)+"\t"+str(at.num_correct_bilphrases)+"\t"+str(at.num_matching_bilphrases)
					print >> sys.stderr, "END_ATS_AFTER_LINEAR_PROG"
				#If not relax restrictions, simply print bilingual phrases
			else:
				for bil_id in globalReproducibleBilphrases:
					if mappingsFromSyntheticBilphrases != None:
						for trueBilId in mappingsFromSyntheticBilphrases[bil_id]:
							globalSolution.append(originalBilphraseSet.get_by_id(trueBilId))
					else:
						globalSolution.append(bilphrases.get_by_id(bil_id))
			
				if printNumCorrectUnfilteredBilphrases:
					print >> sys.stderr, "ATS_AFTER_LINEAR_PROG"
					for bilphrase in globalSolution:
						print >> sys.stderr, str(bilphrase)+"\t"+str(bilphrase.freq)+"\t"+str(bilphrase.freq)
					print >> sys.stderr, "END_ATS_AFTER_LINEAR_PROG"
					
		#problem with relaxed restrictions
		else:
			print >> sys.stderr, "Solving with relaxed restriction because option was enabled"
			#Relax restrictions
			#default: len(at_list)
			unityWeight=eval(relaxWeight)
			
			prob = LpProblem("RulesRelaxed", LpMinimize)
			minimisationExpression=list()
			atVars=dict()
			if DEBUG:
				print >> sys.stderr, "AT variables:"
			for at_id in atIdsAndFactor.keys():
				var=LpVariable("x"+str(at_id), 0, 1,cat='Integer')
				minimisationExpression.append((var,atIdsAndFactor[at_id]))
				atVars[at_id]=var
			
			relaxationVariables=list()
			relaxationVariablesDict=dict()
			for bil_id in globalReproducibleBilphrases:
				#add a new variable for each bilingual phrase to be relaxed
				freq = bilphrases.get_by_id(bil_id).freq
				relaxingVar=LpVariable("r"+str(bil_id), 0, 1,cat='Integer')
				minimisationExpression.append((relaxingVar,unityWeight*freq))
				relaxationVariables.append(relaxingVar)
				relaxationVariablesDict[bil_id]=relaxingVar
				
				#add restriction: bilphrase must be reproduced by at least one AT
				#plus relaxing var
				varsWhichCorrectlyReproduceBil=varsWhichCorrectlyReproduceBilingualPhrases[bil_id]
				cname="bilphrase"+str(bil_id)
				listOfVarsAndFactors=[ (atVars[vari],1) for vari in varsWhichCorrectlyReproduceBil ]
				listOfVarsAndFactors.append((relaxingVar,1))
				myexpression=LpAffineExpression( listOfVarsAndFactors )
				constraint = LpConstraint(myexpression,sense=constants.LpConstraintGE,name=cname,rhs=1)
				prob.constraints[cname]=constraint
				if DEBUG:
					print >> sys.stderr, constraint
			
			#add restrictions to treat exceptions				
			for atsInvolved in restrictionsExceptionsTranslated:
				idNegative=atsInvolved[0]
				bil_id=atsInvolved[1]
				idsPositiveList=atsInvolved[2]
				cname="exceptions_"+str(idNegative)+"_"+str(bil_id)
				variablesList=list()
				variablesList.append((atVars[idNegative],-1))
				for idPositive in idsPositiveList:
					variablesList.append((atVars[idPositive],1))
				variablesList.append((relaxationVariablesDict[bil_id],1))
				myexpression=LpAffineExpression( variablesList )
				constraint = LpConstraint(myexpression,sense=constants.LpConstraintGE,name=cname,rhs=0)
				prob.constraints[cname]=constraint
			
			#add restrictions to choose more general ATs	
			for atsInvolved in restrictionsMoreGeneralAreBetter:
				iID=atsInvolved[0]
				jID=atsInvolved[1]
				cname="moregeneral_"+str(iID)+"_"+str(jID)
				myexpression=LpAffineExpression( [ (atVars[iID],-1), (atVars[jID],1) ] )
				constraint = LpConstraint(myexpression,sense=constants.LpConstraintGE,name=cname,rhs=0)
				prob.constraints[cname]=constraint
			
			for atsInvolved in restrictionsSymmetricDifference:
				iID=atsInvolved[0]
				jID=atsInvolved[1]
				cname="symdifference_"+str(iID)+"_"+str(jID)
				myexpression=LpAffineExpression( [ (atVars[iID],1), (atVars[jID],1) ] )
				constraint = LpConstraint(myexpression,sense=constants.LpConstraintLE,name=cname,rhs=1)
				prob.constraints[cname]=constraint
			
			#Add the newly created variables to the expression to be minimised
			myexpression=LpAffineExpression(minimisationExpression)
			prob.objective=myexpression
			
			if DEBUG:
				print >> sys.stderr, prob.objective
			
			t_start_solving=time()
			print >> sys.stderr, "Solving problem"
			status = prob.solve()
			print >> sys.stderr, "Status: "+str(LpStatus[status])
			
			if status == LpStatusOptimal :
				
				totalScore=0.0
				
				#print deleted bilphrases
				print >> sys.stderr, "Relaxed bilingual phrases:"
				print >> sys.stderr, "Penalty = "+str(unityWeight)
				
				totalFreq=0
				totalBil=0
				for relaxationVar in relaxationVariables:
					if value(relaxationVar)==1:
						relaxedBilphraseId=int(relaxationVar.name[1:])
						globalReproducibleBilphrases.remove(relaxedBilphraseId)
						relaxedBilphrase=bilphrases.get_by_id(relaxedBilphraseId)
						totalScore+=relaxedBilphrase.freq*unityWeight
						totalFreq+=relaxedBilphrase.freq
						totalBil+=1
						debug("score= "+str(freq*unityWeight)+" | "+str(relaxedBilphrase))
						print >> sys.stderr, str(relaxedBilphrase.id)+": "+str(relaxedBilphrase.freq)+"  "+str(relaxedBilphrase)
				print >> sys.stderr, str(totalBil)+" different bilphrases. "+str(totalFreq)+" total frequency"
				
				#get solution
				#if DEBUG:
				#	print >> sys.stderr, "Solution"
				debug("Scores of chosen ATs")
				for at_id in atVars.keys():
					#if DEBUG:
					#	print >> sys.stderr, str(at_id)+": "+str(value(atVars[at_id]))
					if value(atVars[at_id])==1:
						totalScore+=atIdsAndFactor[at_id]
						debug("score= "+str(atIdsAndFactor[at_id])+" | "+str(at_dict[at_id]))
						solution.append(at_dict[at_id])
				
				ts_solving.append(time()-t_start_solving)
				
				debug("Total score (chosen ATs + discarded bilphrases): "+str(totalScore))
				
				#detect loops before applying tsort (debug)
				if DEBUG:
					for index1,at1 in enumerate(solution):
						for index2,at2 in enumerate(solution):
							if index1 != index2:
								if at1.id in at2.atswhicharesubset and at2.id in at1.atswhicharesubset:
									debug("WARNING: Found pair of ATs which are mutual subset. tsort will crash. Ats are:")
									debug(str(at1.id)+": "+str(at1))
									debug(str(at2.id)+": "+str(at2))
									debug("")
									debug("checking result of method is_subset_of..")
									debug("at1.is_subset_of_this(at2):"+str(at1.is_subset_of_this(at2)))
									debug("at2.is_subset_of_this(at1):"+str(at2.is_subset_of_this(at1)))
									debug("")

				atidsInSolution=set()
				for at in solution:
					atidsInSolution.add(at.id)
				arcs=list()
				for at in solution:
					for atid in atidsInSolution:
						if atid != at.id and atid in at.atswhicharesubset:
							arcs.append((atid,at.id))
				sortedSolution=tsort.tsort(arcs)
				
				#append at the end of the solution ats not connected to anyone in the graph
				sortedSolutionSet=set(sortedSolution)
				remaining= atidsInSolution-sortedSolutionSet
				for atid in remaining:
					sortedSolution.append(atid)
					
				for atid in sortedSolution:
					globalSolution.append(at_dict[atid])
				
			else:
				ts_solving.append(time()-t_start_solving)
				print >> sys.stderr, "MEGA FATAL BRUTAL ERROR"
	
	#write resulting bilingual phrases. They will be used by "subrule" approach
	print >> sys.stderr, "BILINGUAL_PHRASES"
	for bil_id in globalReproducibleBilphrases:
		if mappingsFromSyntheticBilphrases != None:
			for trueBilId in mappingsFromSyntheticBilphrases[bil_id]:
				bilphrase=originalBilphraseSet.get_by_id(trueBilId)
				print >> sys.stderr, str(bilphrase.freq)+" | "+bilphrase.to_string(removeRestrictionsFromLexicalised=False)
		else:
			bilphrase=bilphrases.get_by_id(bil_id)
			print >> sys.stderr, str(bilphrase.freq)+" | "+bilphrase.to_string(removeRestrictionsFromLexicalised=False)
	print >> sys.stderr, "END_BILINGUAL_PHRASES"
			
	#print times
	print >> sys.stderr, "Number of problems: "+str(len(ts_preferences))
	print >> sys.stderr, "Time spent computing which ATs come before: "+str(sum(ts_preferences))
	print >> sys.stderr, "Time spent preparing linear programming equations: "+str(sum(ts_preparing))
	print >> sys.stderr, "Time spent solving linear programming and topological order: "+str(sum(ts_solving))
	totaltimeinside=sum(ts_preferences)+sum(ts_preparing)+sum(ts_solving)
	
	return globalSolution,totaltimeinside


#OBSOLETO: eliminar en cuanto me asgure de que no va a causar problemas
def generalise_by_linear_program_pulp(bilphrases, finalAlignmentTemplates, taggroups,subsetsGraph,removeContradictoryATs=False, printNumCorrectUnfilteredBilphrases=False, proportionCorrectBilphrasesThreshold=0.00,lambdaForCombining=0.00,stopAfterComputingBilphrases=False):
	myAts, reproducibleBilphrases = filter_pre_minimisation(bilphrases, finalAlignmentTemplates,subsetsGraph,removeContradictoryATs,  proportionCorrectBilphrasesThreshold)
	return minimise_linear_programming(myAts,reproducibleBilphrases,bilphrases,taggroups,printNumCorrectUnfilteredBilphrases,lambdaForCombining)
	

#ATENCION: Ahora siempre devuelve 1
def compute_concreteness_level(sllist):
	level=1
	for sllexform in sllist:
		if len(get_lemma(sllexform).strip())>0:
			level+=1
		tagslist=parse_tags(sllexform)
		for tag in tagslist:
			if not u'*' in tag:
				level+=1
	#return level
	return 1

def group_ats_for_transfer_rule(atlist,taggroups):
	
	DEBUG=False
	
	groups=list()
	error=""
	
	while len(atlist) > 0:
		
		localatlist=list()
		equivalentats=list()
		
		copiedatlist=list()
		copiedatlist.extend(atlist)
		
		while len(copiedatlist) > 0:
			curAt=copiedatlist[0]
			equivalenttothis=list()
			
			copiedatlist=copiedatlist[1:]
			
			for at in copiedatlist:
				if curAt.has_same_left_side(at):
					equivalenttothis.append(at)
			
			for at in equivalenttothis:
				copiedatlist.remove(at)
			
			localatlist.append(curAt)
			equivalentats.append(equivalenttothis)
			
		if DEBUG:
			print >> sys.stderr, "atlist: "+str(atlist)	
			print >> sys.stderr, "Local atlist :"+str(localatlist)
			print >> sys.stderr, "Equivalent :"+str(equivalentats)
		
		#Table[i][j] AT j is subset of AT i
		table= [ [ False for i in range(len(localatlist)) ] for j in range(len(localatlist)) ]
		for i in range(len(localatlist)):
			at=localatlist[i]
			for j in range(len(localatlist)):
				if i != j:
					at2=localatlist[j]
					if DEBUG:
						print >> sys.stderr, "Checking if A is subseto of B."
						print >> sys.stderr, "A: "+str(at2)
						print >> sys.stderr, "B: "+str(at)
					
					table[i][j]=at.is_subset_of_this(at2,checkRestrictions=False)
		
		#Search AT which is not subset of any other
		indexatisnotsubset=None
		for j in range(len(localatlist)):
			trueFound=False
			for i in range(len(localatlist)):
				if table[i][j] == True:
					trueFound=True
					break
			if not trueFound:
				indexatisnotsubset=j
				break
		if DEBUG:
			print >> sys.stderr, "indexatisnotsubset: "+str(indexatisnotsubset)
			
		if indexatisnotsubset!=None:
			group=list()
			detect=localatlist[indexatisnotsubset].sl_lexforms
			group.append(localatlist[indexatisnotsubset])
			for eqat in equivalentats[indexatisnotsubset]:
				group.append(eqat)
			for j in range(len(localatlist)):
				if table[indexatisnotsubset][j]==True:
					group.append(localatlist[j])
					for eqat in equivalentats[j]:
						group.append(eqat)
			groups.append((detect,group))
			
			for gat in group:
				if DEBUG:
					print >> sys.stderr, "Removing from atlist: "+str(gat)
				atlist.remove(gat)
					
		else:
			error="No root found"
			break
			
	return error,groups

def read_tag_groups(inputfile):
	tag_groups=dict()
	for line in inputfile:
		line=line.strip().decode('utf-8')
		parts=line.split(u":")
		if len(parts)==2 or len(parts)==3:
			groupname=parts[0]
			tags=parts[1].split(u",")
			pos=None
			if len(parts)==3:
				pos=parts[2].split(u",")
			tag_groups[groupname]=(tags,pos)
	return tag_groups
	
def read_tag_sequences(inputfile):
	tag_sequences=dict()
	for line in inputfile:
		line=line.strip().decode('utf-8')
		parts=line.split(u":")
		if len(parts)==2:
			pos=parts[0]
			tags=parts[1].split(u",")
			tag_sequences[pos]=tags
	return tag_sequences


def find_tag_from_tag_group_in_tag_sequence(sequence,taggroup_id,taggroups,pos,usingEmptyTags=False):
	for tag in sequence:
		taggroup=get_tag_group_from_tag(tag,taggroups,pos,usingEmptyTags)
		if taggroup == taggroup_id:
			return tag
	return None

def get_tag_group_from_tag(tag,taggroups,pos,usingEmptyTags=True):
	DEBUG=False
	
	#debug("Getting group of '"+tag+"', which is a '"+pos+"'. Using empty tags = "+str(usingEmptyTags))
	
	EMPTY_TAG_PREFIX=u"empty_tag_"
	groupFound=None
	
	typeSpecial,featureName,postion= parse_special_tag(tag)
	
	if tag==pos:
		groupFound=u"__GROUP_PART_OF_SPEECH__"
	elif typeSpecial == AT_SpecialTagType.FOLLOW_ALIGNMENT or typeSpecial == AT_SpecialTagType.CHECK_BIDIX or typeSpecial == AT_SpecialTagType.SPECIFIED_SL or typeSpecial == AT_SpecialTagType.RESTRICTION_CHANGING or typeSpecial == AT_SpecialTagType.RESTRICTION_CONSTANT:
		groupFound=featureName
	else:
		if tag.startswith(EMPTY_TAG_PREFIX) and usingEmptyTags:
			return tag[len(EMPTY_TAG_PREFIX):]
		else:
			numGroupsFound=0
			for groupIndex in taggroups.keys():
				if tag in taggroups[groupIndex][0] and (taggroups[groupIndex][1]==None or pos in taggroups[groupIndex][1]):
					numGroupsFound+=1
					groupFound=groupIndex
			if numGroupsFound!=1:
				#print >> sys.stderr, "ERROR: tag '"+str(tag)+"' found in "+str(numGroupsFound)+" groups != 1"
				#traceback.print_stack()
				raise AT_ParsingError("ERROR: tag '"+str(tag)+"' found in "+str(numGroupsFound)+" groups != 1") 
	
	return groupFound

def can_be_lowercased(tagsstr):
	if tagsstr.startswith(u"<np>") or tagsstr.startswith(u"<num>") or tagsstr.startswith(u"<n><acr>"):
		return False
	else:
		return True

def test_files_exist(files):
	exist=True
	for myfile in files:
		if not os.path.isfile(myfile):
			exist=False
			break
	return exist

def execute_commands(commands):
	for command in commands:
		print >> sys.stderr, "executing '"+command+"'"
		output,error = subprocess.Popen(command, stderr= subprocess.PIPE, shell=True).communicate()
		if len(error) > 0:
			print >> sys.stderr,"WARNING: Err output contents: "+error
		

def execute_command_getoutput(command):
	output,error = subprocess.Popen(command,stdout = subprocess.PIPE, stderr= subprocess.PIPE, shell=True).communicate()
	return output,error

def multipleEqual(clist):
	result=True
	for i in range(len(clist)-1):
		if clist[i] != clist[i+1]:
			result=False
			break
	return result

def lowercase_first_letter(mystr):
	if len(mystr)>0:
		return mystr[0].lower()+mystr[1:]
	else:
		return mystr

def compare_lowercase_first_letter(str1,str2):
	return lowercase_first_letter(str1) == lowercase_first_letter(str2)


def segment_by_marker(listOfLexForms,closetags):
	subsegments=list()
	curSubsegment=list()
	containsNonMarker=False
	for word in listOfLexForms:	
		posStartTags=word.find(u"<")
		if posStartTags > -1:
			tags=word[posStartTags:]
			# Non-marker
			if remove_lemmas(word,closetags) != word:
			#if not tags in closetags:
				curSubsegment.append(word)
				containsNonMarker=True
			# Marker
			else:
				if containsNonMarker:
					subsegments.append(curSubsegment)
					curSubsegment=list()
					containsNonMarker=False
				curSubsegment.append(word)
	if len(curSubsegment)>0:
		if containsNonMarker:
			subsegments.append(curSubsegment)
		else:
			if len(subsegments)>0:
				subsegments[-1].extend(curSubsegment)
			else:
				subsegments.append(curSubsegment)
	return subsegments


def segment_by_unknown(line, keepSurfaceForms, keepLemmas, closetags=None):
	pattern=re.compile(LEXICAL_FORM_RE)
	matchesiter=pattern.finditer(line)
	segments=list()
	curSegment=list()
	curMode=None
	for mymatch in matchesiter:
		lexform=mymatch.group()[1:-1]
		surface_form=u""
		if keepSurfaceForms:
			parts=lexform.split(u"/")
			if len(parts)==2:
				lexform=parts[1]
				surface_form=parts[0]
		entry=(lexform,surface_form)
		
		accepted=True
		if lexform[0]==u'*':
			accepted=False
		else:
			posStartTags=lexform.find(u"<")
			tags=lexform[posStartTags:]
			if can_be_lowercased(tags):
				entry=(lexform.lower(),surface_form.lower())

			if tags.startswith(u"<sent>") or tags.startswith(u"<cm>") or tags.startswith(u"<lpar>") or tags.startswith(u"<rpar>") or tags.startswith(u"<apos>"):
				accepted=False
			elif not keepLemmas:
				#Con esto gestionamos CATEGORÍAS LEXICALIZADAS
				entry=(remove_lemmas(lexform,closetags),surface_form)
		
		if accepted and curMode=="nonsep":
			curSegment.append(entry)
		elif not accepted and curMode=="sep":
			curSegment.append(entry)
		elif curMode==None:
			if accepted:
				curMode="nonsep"
			else:
				curMode="sep"
			curSegment.append(entry)
		else:
			segments.append((curMode,curSegment))
			curSegment=list()
			curSegment.append(entry)
			if accepted:
				curMode="nonsep"
			else:
				curMode="sep"
	if len(curSegment) > 0:
		segments.append((curMode,curSegment))

	return segments


def read_close_tags(closetagsfile):
	closetags=set()
	for line in open(closetagsfile,'r'):
		line=line.decode('utf-8').strip()
		closetags.add(line)
	return closetags

def remove_lemmas(word,closetags):
	if closetags == None:
		closetags=[]
	posStartTags=word.find(u"<")
	firstTag=word[posStartTags:word.find(u">")+1]
	lemma=word[:posStartTags]
	tags=word[posStartTags:]
	if tags in closetags or lemma+firstTag in closetags:
		return word
	else:
		return tags

def get_lemma(word):
	posStartTags=word.find(u"<")
	return word[:posStartTags]

def get_tags(word):
	posStartTags=word.find(u"<")
	return word[posStartTags:]

def remove_lemmas_one(word):
	return remove_lemmas(word,set())

def unparse_lex_form(lemma,tags,replaceSpacesWithUnderscore=False):
	if replaceSpacesWithUnderscore:
		return lemma.replace(u" ",u"_")+unparse_tags(tags)
	else:
		return lemma+unparse_tags(tags)

def unparse_tags(tagsstr):
	return u"<"+u"><".join(tagsstr)+u">"

def escape_lemma(lemmastr):
	if lemmastr == u"[":
		return u"\\["
	if lemmastr == u"]":
		return u"\\]"
	return lemmastr

def parse_tags(tagsstr):
	parsedTags=list()
	REGULAR_EXP=r"<([^>]+)>"
	pattern=re.compile(REGULAR_EXP)
	matchesiter=pattern.finditer(tagsstr)
	for mymatch in matchesiter:
		parsedTags.append(mymatch.group(1))
	return parsedTags

def parse_lexical_form(lexicalForm,removeUnderscoreFromLemma=False):
	if removeUnderscoreFromLemma:
		return (get_lemma(lexicalForm).replace(u"_",u" "),parse_tags(lexicalForm))
	else:
		return (get_lemma(lexicalForm),parse_tags(lexicalForm))

LEXICAL_FORM_RE=r"\^([^$^]*[<|*][^$^]*)\$"

def combine_elements(list_of_lists):
	combinations=list()
	
	numOptions=1
	for mylist in list_of_lists:
		numOptions=numOptions*len(mylist)
	
	for num in range(numOptions):
		option=list()
		denominator=1
		for j in range(len(list_of_lists)):
			comp=list_of_lists[j]
			size=len(comp)
			index=(num/denominator)%size
			option.append(comp[index])
			denominator=denominator*size
		combinations.append(option)

	return combinations	

def generateAT_parse_tagged(inputstr):
	pattern=re.compile(LEXICAL_FORM_RE)
		
	answertaggedWords=list()
	matchesiter=pattern.finditer(inputstr)
	for mymatch in matchesiter:
		anslexform=mymatch.group()[1:-1]
		answordparts=anslexform.split(u"/")
		answertaggedWords.append(answordparts[1])
	
	answertaggedMultiple=list()
	answertaggedMultiple.append([])
	for word in answertaggedWords:
		if word == u".<sent>":
			answertaggedMultiple.append([])
		else:		
			answertaggedMultiple[-1].append(word)
	return answertaggedMultiple,answertaggedWords
	
def generateAT_parse_no_surface(inputstr):
	pattern=re.compile(LEXICAL_FORM_RE)
		
	answertaggedWords=list()
	matchesiter=pattern.finditer(inputstr)
	for mymatch in matchesiter:
		anslexform=mymatch.group()[1:-1]
		answertaggedWords.append(anslexform)
	
	answertaggedMultiple=list()
	answertaggedMultiple.append([])
	for word in answertaggedWords:
		if word == u".<sent>":
			answertaggedMultiple.append([])
		else:
			wordinlist=[word]
			answertaggedMultiple[-1].append(wordinlist)
	while len(answertaggedMultiple) > 0 and len(answertaggedMultiple[-1])==0:
		answertaggedMultiple=answertaggedMultiple[:-1]
	return answertaggedMultiple,answertaggedWords

def generateAT_parse_untagged(inputstr):
	pattern=re.compile(LEXICAL_FORM_RE)
	matchesiter=pattern.finditer(inputstr)

	answerMultiple=list()
	answerMultiple.append([])

	for mymatch in matchesiter:
		anslexform=mymatch.group()[1:-1]
		answordparts=anslexform.split(u"/")
		surfaceform=answordparts[0]
		anslexforms=answordparts[1:]
		
		if surfaceform==u".":
			answerMultiple.append([])
		else:
			answerMultiple[-1].append((surfaceform,anslexforms))
	return answerMultiple

def generateAT_extractAT_old(sllexwords, tlsurfacewords, tllexwords, tllexprefixes, answer, answertagged,answertaggedWords, closetags, closetagsTL, autoAlignSingleUnalignedWord=False):
	at=AlignmentTemplate()
	at.sl_lexforms.extend(sllexwords)
	atOk=True
	causeCode=None
	cause=None
	numMatch=0
	numMatchFromTagger=0			

	containsUnknown=False
	for j in range(len(answer)):
		surfaceform=answer[j][0]
		anslexforms=answer[j][1]
		
		if anslexforms[0].startswith(u'*'):
			containsUnknown=True
	
		if surfaceform in tlsurfacewords:
			index=tlsurfacewords.index(surfaceform)
			tllexform=tllexwords[index]
			at.tl_lexforms.append(tllexform)
			at.alignments.append((index,numMatch))
		else:
			#
			prefixFound=False
			for altanslexform in anslexforms:
				# Ojo! por aquí puede haber un +, tener eso en cuenta!!
				partsofaltlexform=altanslexform.split(u"+")
				totalParts=len(partsofaltlexform)
				curPart=0
				for part in partsofaltlexform:
					prefix=part[:part.find(u">")+1]
					if prefix in tllexprefixes:
						index=tllexprefixes.index(prefix)
						at.tl_lexforms.extend(partsofaltlexform)
						at.alignments.append((index,numMatch+curPart))
						numMatch+=(totalParts-1)
						prefixFound=True
						break
					curPart+=1
				if prefixFound:
					break
			if not prefixFound:
				#Ask tagger, leave word unaligned
				lexformFromTagger=answertaggedWords[numMatchFromTagger]
				at.tl_lexforms.append(lexformFromTagger)
				
		numMatch+=1
		numMatchFromTagger+=1

	if containsUnknown:
		cause="Answer contains unknown word"
		causeCode='containsUnknownWord'
		atOk=False
	else:

		if autoAlignSingleUnalignedWord:
			SLUnalignedSet=set()
			TLUnalignedSet=set()
			for i in range(len(at.sl_lexforms)):
				lexform=at.sl_lexforms[i]
				if remove_lemmas(lexform,closetags) != lexform:
					SLUnalignedSet.add(i)
			for i in range(len(at.tl_lexforms)):
				lexform=at.tl_lexforms[i]
				if remove_lemmas(lexform,closetagsTL) != lexform:
					TLUnalignedSet.add(i)
			for aligment in at.alignments:
				SLUnalignedSet.discard(aligment[0])
				TLUnalignedSet.discard(aligment[1])

			if len(SLUnalignedSet) == 1 and len(TLUnalignedSet) == 1:
				at.alignments.append((SLUnalignedSet.pop(),TLUnalignedSet.pop()))


		position=0
		while position < len(at.sl_lexforms):
			sllex=at.sl_lexforms[position]
			tags=remove_lemmas(sllex,closetags)
			if tags==sllex:
				#Lexicalised word, remove alignments and add __CLOSEWORD__ restriction

				#remove alignments
				newAlignments=list()
				for alignment in at.alignments:
					if alignment[0]!=position:
						newAlignments.append(alignment)
				at.alignments=newAlignments

				#add restriction
				at.restrictions.append(u"__CLOSEWORD__")
	
			else:
				#Add restriction based on translation of the sl word in the bilingual dictionary
			


				firstTag=tags[:tags.find(u">")+1]
				alignmentsFromThisWord=list()
				for alignment in at.alignments:
					if alignment[0]==position:
						alignmentsFromThisWord.append(alignment)

				#Non-aligned: restriction = first tag
				if len(alignmentsFromThisWord) == 0:
					cause="SL word from open category not aligned"
					causeCode='SLNotAligned'
					atOk=False
					break
				else:
					at.sl_lexforms[position]=tags
					tllex=tllexwords[position]
					tltags=remove_lemmas(tllex,set())
					parsedTLTags=parse_tags(tltags)
					parsedSLTags=parse_tags(tags)
					indexSL=len(parsedSLTags)-1
					indexTL=len(parsedTLTags)-1
					while(indexSL>0 and indexTL>0):
						if parsedSLTags[indexSL] != parsedTLTags[indexTL]:
							break
						indexSL-=1
						indexTL-=1
					if indexSL <1:
						indexSL=0
					restrictionList=parsedTLTags[:indexTL+1]
					restrictionsListStr=list()
					for restrictionTag in restrictionList:
						restrictionsListStr.append(u"<"+restrictionTag+u">")
					restrictionStr=u"".join(restrictionsListStr)
					at.restrictions.append(restrictionStr)

					for alignment in alignmentsFromThisWord:
						at.tl_lexforms[alignment[1]]=remove_lemmas(at.tl_lexforms[alignment[1]],set())

		
			position+=1
		if atOk:
			# Check whether there are not open TL words unaligned
			position=0
			while position < len(at.tl_lexforms):
				#check if TL word in position "position" is aligned
				alignmentsToThisWord=list()
				for alignment in at.alignments:
					if alignment[1]==position:
						alignmentsToThisWord.append(alignment)
		
				if len(alignmentsToThisWord)==0:
					#Check whether it belongs to an open category
					tlwordwithoutLemmas=remove_lemmas(at.tl_lexforms[position],closetagsTL)
					if tlwordwithoutLemmas != at.tl_lexforms[position]:
						cause="TL word "+str(position)+" from open category not aligned"
						causeCode='TLNotAligned'
						atOk=False
						break
				elif len(alignmentsToThisWord) > 1:
						cause="More than one alignment for the same TL form"
						causeCode='MultipleTLAlignments'
						atOk=False
						break

				position+=1
	return at, atOk, causeCode, cause

def generateAT_get_best_TL_analysis(analysis_list):
	#TODO: Usar modelo de etiquetas bla bla bla
	return analysis_list[0]

def generateAT_extractAT(sllexwords, tllexwords, tllexnoqueuewords, answer, ignoreCloseTags, closetags, closetagsTL):
	at=AlignmentTemplate()
	at.sl_lexforms.extend(sllexwords)
	atOk=True
	causeCode=None
	cause=None
	numMatch=0
	numMatchFromTagger=0
	lemmassl=list()	
	lemmastl=list()

	tllexprefixes=list()
	for tllexword in tllexwords:
		prefix=tllexword[:tllexword.find(u">")+1]
		tllexprefixes.append(prefix)

#	print >> sys.stderr, "answer: "+str(answer)

	containsUnknown=False
	answerAlternatives=list()
	for j in range(len(answer)):
		
#		surfaceform=answer[j][0]	
		anslexforms=answer[j]
		
		if anslexforms[0].startswith(u'*'):
			containsUnknown=True
			lemmastl.append(anslexforms[0])
		else:
			currentAlternative=list()
			prefixFound=False
			for altanslexform in anslexforms:
				# Ojo! por aquí puede haber un +, tener eso en cuenta!! NO se tiene
				prefix=altanslexform[:altanslexform.find(u">")+1]
				
				#Cuidado! Cuando len(anslexforms)>1 esto puede causar problemas
				lemmastl.append(prefix[:prefix.find(u"<")])
				
				if prefix in tllexprefixes:
					index=tllexprefixes.index(prefix)
					currentAlternative.append((altanslexform,index))
					prefixFound=True
					break
			if not prefixFound:
				for altanslexform in anslexforms:
					currentAlternative.append((altanslexform,-1))
			answerAlternatives.append(currentAlternative)

	if containsUnknown:
		cause="Answer contains unknown word"
		causeCode='containsUnknownWord'
		atOk=False
	else:
		answerOptions=combine_elements(answerAlternatives)
		
		bestOption=generateAT_get_best_TL_analysis(answerOptions)

		numLexform=0
		for tlinfo in bestOption:
			partsoflexform=tlinfo[0].split(u"+")
			at.tl_lexforms.extend(partsoflexform)
			if tlinfo[1] >= 0:
				at.alignments.append((tlinfo[1],numLexform))
			numLexform+=len(partsoflexform)

		position=0
		while position < len(at.sl_lexforms):
			sllex=at.sl_lexforms[position]
			
			lemmassl.append(sllex[:sllex.find(u"<")])
			
			tags=remove_lemmas(sllex,closetags)
			if tags==sllex and not ignoreCloseTags:
				#Lexicalised word, remove alignments and add __CLOSEWORD__ restriction

				#remove alignments
				newAlignments=list()
				for alignment in at.alignments:
					if alignment[0]!=position:
						newAlignments.append(alignment)
				at.alignments=newAlignments

				#add restriction
				at.restrictions.append(u"__CLOSEWORD__")
	
			else:
				#Add restriction based on translation of the sl word in the bilingual dictionary
			
				firstTag=tags[:tags.find(u">")+1]
				alignmentsFromThisWord=list()
				for alignment in at.alignments:
					if alignment[0]==position:
						alignmentsFromThisWord.append(alignment)

				#Non-aligned: restriction = first tag
				if len(alignmentsFromThisWord) == 0:
					if not ignoreCloseTags:
						cause="SL word from open category not aligned"
						causeCode='SLNotAligned'
						atOk=False
						break
					else:
						at.restrictions.append(u"__CLOSEWORD__")
				else:
					if ignoreCloseTags:
						at.sl_lexforms[position]=remove_lemmas(sllex,set())
					else:
						at.sl_lexforms[position]=tags
					
					########### Esto no hace nada ######################
					#######################################################
					if False:
						tllex=tllexwords[position]
						tltags=remove_lemmas(tllex,set())
						parsedTLTags=parse_tags(tltags)
						parsedSLTags=parse_tags(tags)
						indexSL=len(parsedSLTags)-1
						indexTL=len(parsedTLTags)-1
						while(indexSL>0 and indexTL>0):
							if parsedSLTags[indexSL] != parsedTLTags[indexTL]:
								break
							indexSL-=1
							indexTL-=1
						if indexSL <1:
							indexSL=0
						restrictionList=parsedTLTags[:indexTL+1]
						restrictionsListStr=list()
						for restrictionTag in restrictionList:
							restrictionsListStr.append(u"<"+restrictionTag+u">")
						restrictionStr=u"".join(restrictionsListStr)
					###########################################################
					
					at.restrictions.append(remove_lemmas_one(tllexnoqueuewords[position]))

					for alignment in alignmentsFromThisWord:
						at.tl_lexforms[alignment[1]]=remove_lemmas_one(at.tl_lexforms[alignment[1]])

		
			position+=1
		if atOk:
			# Check whether there are not open TL words unaligned
			position=0
			while position < len(at.tl_lexforms):
				#check if TL word in position "position" is aligned
				alignmentsToThisWord=list()
				for alignment in at.alignments:
					if alignment[1]==position:
						alignmentsToThisWord.append(alignment)
		
				if len(alignmentsToThisWord)==0:
					#Check whether it belongs to an open category
					tlwordwithoutLemmas=remove_lemmas(at.tl_lexforms[position],closetagsTL)
					if tlwordwithoutLemmas != at.tl_lexforms[position] and not ignoreCloseTags:
						cause="TL word "+str(position)+" from open category not aligned"
						causeCode='TLNotAligned'
						atOk=False
						break
				elif len(alignmentsToThisWord) > 1:
						cause="More than one alignment for the same TL form"
						causeCode='MultipleTLAlignments'
						atOk=False
						break

				position+=1
	return at, atOk, causeCode, cause, lemmassl, lemmastl

