#!/usr/bin/env python

from ruleLearningLib import debug, AT_GeneralisationOptions, powerset,\
    AlignmentTemplateSet
import argparse
import copy
import ruleLearningLib
import sys
from time import time
import gzip


class AlignmentTemplateGenerationMethod():
    FIRST_APPROACH=0
    TL_VARIABLES=1

def process_bilingual_phrases(atListWithLemmasList,bilingualPhrases, generalisationOptions,generationMethod,allowedSLLemmas):
    finalAlignmentTemplates=ruleLearningLib.AlignmentTemplateSet()
    idAt=1
    
    structuralVariationsDictionary=dict()
    lexicalVariationsDictionary=dict()
    afterwardsDictionary=dict()
    
    timeStructuralvariations=0.0
    timeLexicalVariations=0.0
    timeRemovingWrongAlignments=0.0
    timeCorrectAndIncorrect=0.0
    timeAfterwardsRestrictions=0.0
    
    for atWithLemmas in atListWithLemmasList:
        at=atWithLemmas[0]
        sllemmas=atWithLemmas[1]
        tllemmas=atWithLemmas[2]
        tllemmasfromdictionary=atWithLemmas[3]
        
        debug("Generalising "+str(at)+" | "+str(sllemmas)+" | "+str(tllemmas))
        
        if generationMethod==AlignmentTemplateGenerationMethod.FIRST_APPROACH:
            subsetsGraph=ruleLearningLib.SubsetGraph()
            idAt=ruleLearningLib.AlignmentTemplate_generate_all_generalisations_and_add_them(at,sllemmas,tllemmas,tllemmasfromdictionary,finalAlignmentTemplates,idAt,subsetsGraph,True,True,generalisationOptions.get_genWhenEmptyTLCats(),generalisationOptions.get_genWhenEmptySLCats())
        elif generationMethod==AlignmentTemplateGenerationMethod.TL_VARIABLES:
            debug("Checking whether hash '"+str(hash(at))+"' is in the dictionary |d| = "+str(len(structuralVariationsDictionary))+".")
            #wildcard and reference values
            if not at in structuralVariationsDictionary:
                debug("AT not found in structural generalisations")
                starttime=time()
                structuralVariationsAts=ruleLearningLib.AlignmentTemplate_generate_all_structural_generalisations(at,generalisationOptions)
                timeStructuralvariations+=(time()-starttime)
                structuralVariationsDictionary[at]=structuralVariationsAts
            else:
                debug("AT already found in structural generalisations. Not repeating work")
            
            lemmasposandalignments=at.fast_clone()
            lemmasposandalignments.remove_all_inflection_tags()
            cleanAT=lemmasposandalignments.fast_clone()
            lemmasposandalignments.set_lemmas(sllemmas,tllemmas)
            lemmasposandalignments.tl_lemmas_from_dictionary=tllemmasfromdictionary
            
            #lexicalisations
            if not lemmasposandalignments in lexicalVariationsDictionary:
                starttime=time()
                lexicalVariationsAtsF=ruleLearningLib.AlignmentTemplate_generate_all_lexical_generalisations(cleanAT,sllemmas,tllemmas,tllemmasfromdictionary,generalisationOptions.is_unlexicaliseUnalignedSL())
                if allowedSLLemmas:
                    lexicalVariationsAts=[myat for myat in lexicalVariationsAtsF if tuple(myat.get_sl_lemmas()) in allowedSLLemmas]
                else:
                    lexicalVariationsAts=lexicalVariationsAtsF
                    
                timeLexicalVariations+=(time()-starttime)
                lexicalVariationsDictionary[lemmasposandalignments]=lexicalVariationsAts
            
            #removing alignments
            starttime=time()
            for atstruct in structuralVariationsDictionary[at]:
                for atlex in lexicalVariationsDictionary[lemmasposandalignments]:
                    newat=atstruct.fast_clone()
                    newat.set_lemmas_from_other_at(atlex)
                    options=newat.get_unalignment_options_for_multiple_aligned_unlexicalised_tl_words(lemmasposandalignments)
                    for option in options:
                        atcopy=newat.fast_clone()
                        atcopy.remove_alignments(option)
                        atcopy.alignments.sort()
                        debug("Obtained AT: "+str(atcopy))
                        
                        if not atcopy in afterwardsDictionary:
                            afterwardsDictionary[atcopy]=list()
                        afterwardsDictionary[atcopy].append(atcopy.afterwards_restrictions)
                        
                        if not finalAlignmentTemplates.is_in_set(atcopy):
                            debug("is NOT in set")
                            idAt+=1
                            atcopy.id=idAt
                            finalAlignmentTemplates.add(atcopy)
            timeRemovingWrongAlignments+=(time()-starttime)
        else:   
            print >> sys.stderr, "WRONG GENERATION METHOD"
    
    
    idAT=len(finalAlignmentTemplates.get_all_ats_list())
    finalAlignmentTemplatesAfterwardsRestrictions=AlignmentTemplateSet()
    
    
    if ruleLearningLib.DEBUG:
        debug("All the bilingual phrases:")
        for bilphrase in bilingualPhrases.get_all_ats_list():
            debug("\t"+str(bilphrase))
            tllemmaslocal=u" ".join([ "'"+lem+"'" for lem in bilphrase.tl_lemmas_from_dictionary  ])
            debug("TL lemmas: "+tllemmaslocal.encode('utf-8'))
    
    
    matchingBilphrasesDict=dict()
    for at in finalAlignmentTemplates.get_all_ats_list():
        starttime=time()
        idsOk,idMatching,numOk,numMatching=bilingualPhrases.get_ids_of_matching_and_compatible_phrases(at)
        timeCorrectAndIncorrect+=(time()-starttime)
        matchingBilphrasesDict[at]=(idsOk,idMatching,numOk,numMatching)
        at.freq=numOk
        debug("precomputing matching and OK bilingual phrases for at: "+str(at))
        debug("numOK: "+str(numOk)+" numMatching: "+str(numMatching))
        
    
    
    debug("Final ATs:")
    for at in finalAlignmentTemplates.get_all_ats_list():
        if generalisationOptions.is_refToBiling() and not generalisationOptions.is_differentRestrictionOptions() and generalisationOptions.is_generalise() and not generalisationOptions.is_addRestrictionsForEveryTag():
            at.shorten_restrictions()
        
        idsOk,idMatching,numOk,numMatching=matchingBilphrasesDict[at]
        debug(str(at))
        debug("with numOK = "+str(numOk)+" and freq = "+str(at.freq))
        
        if generalisationOptions.get_possibleValuesForRestrictions() == AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_TRIGGERINGCHANGE:
            starttime=time()
            
            atsSharingLeftSide=list()
            for atSharing in finalAlignmentTemplates.get_ats_with_same_sllex_and_restrictions(at):
                if atSharing != at:
                    reproducedBilphrasesOfSharing=AlignmentTemplateSet()
                    incorrectBilphrasesOfSharing=AlignmentTemplateSet()
                    idsOkS,idMatchingS,numOkS,numMatchingS=matchingBilphrasesDict[atSharing]
                    incorrectIds=set(idMatchingS) - set(idsOkS)
                    for incorrectId in incorrectIds:
                        incorrectBilphrasesOfSharing.add(bilingualPhrases.get_by_id(incorrectId))
                    for idOK in idsOkS:
                        reproducedBilphrasesOfSharing.add(bilingualPhrases.get_by_id(idOK))
                    atsSharingLeftSide.append((atSharing,reproducedBilphrasesOfSharing,incorrectBilphrasesOfSharing,numOkS))
            
            incorrectBilphrases=AlignmentTemplateSet()
            incorrectIds=set(idMatching) - set(idsOk)
            for incorrectId in incorrectIds:
                incorrectBilphrases.add(bilingualPhrases.get_by_id(incorrectId))
            
            reproducedBilphrases=AlignmentTemplateSet()
            for idOK in idsOk:
                reproducedBilphrases.add(bilingualPhrases.get_by_id(idOK))
            
            debug("Processing AT to add restrictions: "+str(at))
            debug("Matching bilphrases ("+str(len(idMatching))+"):") 
            if ruleLearningLib.DEBUG:
                for bid in idMatching:
                    debug("\t"+str(bilingualPhrases.get_by_id(bid)))
            debug("Reproduced bilphrases ("+str(len(idsOk))+"):")
            if ruleLearningLib.DEBUG:
                for bid in idsOk:
                    debug("\t"+str(bilingualPhrases.get_by_id(bid)))
            debug("Incorrect bilphrases ("+str(len(incorrectIds))+") :")
            if ruleLearningLib.DEBUG:
                for inat in incorrectBilphrases.get_all_ats_list():
                    debug("\t"+str(inat.id)+": "+inat.to_string(removeRestrictionsFromLexicalised=False))
            
            #represent possible restrictions to be added as tuples
            allOptions=list()
            afterwardsRestrictionItemIndex=0
            for afterwards_restriction_item in afterwardsDictionary[at]:
                afterwardsRestrictionItemIndex+=1
                restrictionsAsTuples=list()
                for i in range(len(afterwards_restriction_item)):
                    #only add restrictions for non-lexicalised words 
                    if not at.parsed_sl_lexforms[i].has_lemma():
                        afterwardDict=afterwards_restriction_item[i]
                        for key in afterwardDict:
                            tuplerep=(i,key,afterwardDict[key])
                            restrictionsAsTuples.append(tuplerep)
            
                debug("Possible values for restrictions "+str(afterwardsRestrictionItemIndex)+": "+str(restrictionsAsTuples))
            
                #compute power set
                options=powerset(restrictionsAsTuples)
                allOptions.extend(options)
            
            allOptionsFrozenUniq=list(set([frozenset(o) for o in allOptions]))
            
            #sort options by number of components
            sortedOptions=sorted(allOptionsFrozenUniq,key=len)
            if generalisationOptions.is_triggeringLimitedLength():
                positionOfFirstInvalidOption=None
                for k in range(len(sortedOptions)):
                    if len(sortedOptions[k]) > len(at.parsed_sl_lexforms):
                        positionOfFirstInvalidOption=k
                        break
                if positionOfFirstInvalidOption!=None:
                    sortedOptions=sortedOptions[:positionOfFirstInvalidOption]
                
            
            incorrectIdsNotMatchingDict=dict()
            
            while len(sortedOptions) > 0:
                opt=sortedOptions.pop(0)
                optlen=len(opt)
                debug("Added restrictions option: "+str(opt))
                
                
                #matchesZero=False
                #for resSetMatchingZero in restrictionsSetsMatchingZero:
                #    if opt <= resSetMatchingZero:
                #        matchesZero=True
                #        break
                #if matchesZero:
                #    break
                
                newAT=at.fast_clone()
                newAT.add_restrictions_from_tuples(opt)    
                
                idsOk,idMatching,numOk,numMatching=incorrectBilphrases.get_ids_of_matching_and_compatible_phrases(newAT)
                incorrectIdsNotMatching=frozenset(incorrectIds - idMatching)
                
                idsOKFromReproducible,idsMatchingFromReproducible,numOkFromRepr,numMatchingFromRepr= reproducedBilphrases.get_ids_of_matching_and_compatible_phrases(newAT)
                totalReproduciblePhrases=len(reproducedBilphrases.get_all_ids())
                numReproduciblePhrasesNowNOtMatching=totalReproduciblePhrases-len(idsOKFromReproducible)
                debug("Reproducible phrases which now don't match: "+str(numReproduciblePhrasesNowNOtMatching))
                
                atLeastOneValid=False
                if generalisationOptions.is_discardRestrictionsNotImproving():
                    for atSharing,reproducedSharing,incorrectSharing,numOkofSharing in atsSharingLeftSide:
                        idsOkS,idMatchingS,numOkS,numMatchingS=incorrectSharing.get_ids_of_matching_and_compatible_phrases(newAT)
                        idsOKFromReproducibleS,idsMatchingFromReproducibleS,numOkFromReprS,numMatchingFromReprS= reproducedSharing.get_ids_of_matching_and_compatible_phrases(newAT)
                        if ruleLearningLib.DEBUG:
                            debug("\tAT sharing left side: "+str(atSharing))
                            debug("\t New AT matches "+str(numMatchingS)+" bilphrases out of "+str(incorrectSharing.get_total_freq())+" incorrect bilphrases" )
                            debug("\t  reproduces "+str(numOkS)+"/"+str(numMatchingS) ) 
                            debug("\t New AT matches "+str(numMatchingFromReprS)+" bilphrases out of "+str(reproducedSharing.get_total_freq())+" reproduced bilphrases" )
                            debug("\t  reproduces "+str(numOkFromReprS)+"/"+str(numMatchingFromReprS) )
                        phrasesCorrectlyReproducedByCombo=set()
                        
                        #first, the bilingual phrases correctly reproduced by atSharing minus the bilingual phrases matched by newAT
                        phrasesCorrectlyReproducedByCombo.update(reproducedSharing.get_all_ids())
                        phrasesCorrectlyReproducedByCombo.difference_update(idMatchingS)
                        phrasesCorrectlyReproducedByCombo.difference_update(idsMatchingFromReproducibleS)
                        
                        #in addition, the bilingual phrases correctly reproduced by 'newAT' which were matched by AtSharing
                        phrasesCorrectlyReproducedByCombo.update(idsOkS)
                        phrasesCorrectlyReproducedByCombo.update(idsOKFromReproducibleS)
                        
                        totalFreqOfPhrasesReproducedByCombo=sum( bilingualPhrases.get_by_id(bid).freq for bid in phrasesCorrectlyReproducedByCombo )
                        totalFreqOfPhrasesReproducedBySharingAT=numOkofSharing
                        debug("\t"+str(totalFreqOfPhrasesReproducedByCombo)+" phrases reproduced by combo vs. "+str(totalFreqOfPhrasesReproducedBySharingAT)+"phrases reproduced by AT sharing left side")
                        debug("\t"+str(numOkFromRepr)+" phrases reproduced by newAT vs. "+str(totalFreqOfPhrasesReproducedBySharingAT)+"phrases reproduced by AT sharing left side")
                        if numOkFromRepr < totalFreqOfPhrasesReproducedBySharingAT and totalFreqOfPhrasesReproducedByCombo > totalFreqOfPhrasesReproducedBySharingAT and numOkS > numMatchingS/2:
                            debug("\tRestriction VALID for this shared AT")
                            atLeastOneValid=True
                        else:
                            debug("\tRestriction NOT valid for this shared AT")

                if (numReproduciblePhrasesNowNOtMatching==0 or not generalisationOptions.is_triggeringNoGoodDiscarded()) and (not generalisationOptions.is_discardRestrictionsNotImproving() or atLeastOneValid or optlen==0):
                    if ruleLearningLib.DEBUG:
                        debug("Incorrect bilphrases which now don't match ("+str(len(incorrectIdsNotMatching))+"):")
                        for bid in incorrectIdsNotMatching:
                            debug("\t"+str(bilingualPhrases.get_by_id(bid)))
                    
                    if len(incorrectIdsNotMatching) > 0:
                        validAT=True
                        if incorrectIdsNotMatching in incorrectIdsNotMatchingDict:
                            debug("The same set of bilingual phrases was removed by other sets of restrictions...")
                            for pastoption in incorrectIdsNotMatchingDict[incorrectIdsNotMatching]:
                                if pastoption <= opt:
                                    debug("... and there is a subset of this one: "+str(pastoption))                                
                                    validAT=False
                                    break
                            if validAT:
                                debug("... but no set is a subset of this one")
                        else:
                            debug("The same set of bilingual phrases was NOT removed by other sets of restrictions.")
                            incorrectIdsNotMatchingDict[incorrectIdsNotMatching]=set()
                            incorrectIdsNotMatchingDict[incorrectIdsNotMatching].add(opt)
                        if validAT:
                            debug("SET OF RESTRICTIONS OK")
                            idAt+=1
                            newAT.id=idAt
                            finalAlignmentTemplatesAfterwardsRestrictions.add(newAT)
                    if len(idMatching) == 0:
                        debug("This AT does not match any incorrect bilingual phrase. Removing all its supersets")
                        #restrictionsSetsMatchingZero.add(opt)
                        sortedOptionsCopy=list()
                        for sopt in sortedOptions:
                            if not opt <= sopt:
                                sortedOptionsCopy.append(sopt)
                        sortedOptions=sortedOptionsCopy
                else:
                    debug("Set of restrictions not generated")
                debug("")
                        
            timeAfterwardsRestrictions+=(time()-starttime)
    
    
    debug("Final ATs with afterwards restrictions:")
    for at in finalAlignmentTemplatesAfterwardsRestrictions.get_all_ats_list():
        starttime=time()
        idsOk,idMatching,numOk,numMatching=bilingualPhrases.get_ids_of_matching_and_compatible_phrases(at)
        timeCorrectAndIncorrect+=(time()-starttime)
        at.freq=numOk
        debug(str(at))
        
    finalAlignmentTemplates.write(sys.stdout)
    finalAlignmentTemplatesAfterwardsRestrictions.write(sys.stdout)
    
    
    print >>sys.stderr, "Time performing structural generalisation: "+str(timeStructuralvariations)
    print >>sys.stderr, "Time performing lexical generalisation: "+str(timeLexicalVariations)
    print >>sys.stderr, "Time removing wrong alignments: "+str(timeRemovingWrongAlignments)
    print >>sys.stderr, "Time computing correct and matching ATs: "+str(timeCorrectAndIncorrect)
    print >>sys.stderr, "Time generating afterwards restrictions: "+str(timeAfterwardsRestrictions)


if __name__=="__main__":
        inputFile=sys.stdin
        #inputFile=open("/home/vitaka/curro/small-unit-test/bilphrases/4.bilphrases")

        DEBUG=False

        parser = argparse.ArgumentParser(description='Generates multiple ATs from each bilingual phrase.')
        parser.add_argument('--tag_groups_generalised_empty_tl',default='__ALL__')
        parser.add_argument('--tag_groups_generalised_empty_sl',default='__ALL__')
        parser.add_argument('--tag_groups_file_name',required=True)
        parser.add_argument('--tag_sequences_file_name',required=True)
        parser.add_argument('--rich_ats',action='store_true')
        #only applies if rich_ats is selected
        parser.add_argument('--ref_to_biling',action='store_true')
        parser.add_argument('--generalise_from_right_to_left',action='store_true')
        parser.add_argument('--add_restrictions_to_every_tag',action='store_true')
        parser.add_argument('--different_restriction_options',action='store_true')
        parser.add_argument('--only_to_be_determined_in_restriction',action='store_true')
        parser.add_argument('--only_to_be_determined_and_mf_in_restriction',action='store_true')
        parser.add_argument('--only_to_be_determined_and_change_in_restriction',action='store_true')
        parser.add_argument('--only_tags_triggering_diference_in_restriction',action='store_true')
        parser.add_argument('--triggering_limited_length',action='store_true')
        parser.add_argument('--triggering_no_good_discarded',action='store_true')
        parser.add_argument('--discard_restrictions_not_improving',action='store_true')
        parser.add_argument('--only_lexical',action='store_true')
        parser.add_argument('--ats_with_allowed_lemmas_file')
        parser.add_argument('--generalise_non_matching_too',action='store_true')
        parser.add_argument('--unlexicalise_unaligned_sl',action='store_true')
        
        parser.add_argument('--dont_generalise_all_instances_together',action='store_true')
        parser.add_argument('--generalisable_attributes_like_in_paper',action='store_true')
        
        parser.add_argument('--times_attributes_change')
        
        parser.add_argument('--debug',action='store_true')
        args = parser.parse_args(sys.argv[1:])
        
        #Process arguments
        if args.debug:                  
            DEBUG=True
            ruleLearningLib.DEBUG=True
        ruleLearningLib.AT_LexicalTagsProcessor.initialize(args.tag_groups_file_name,args.tag_sequences_file_name)
        
        if args.tag_groups_generalised_empty_tl == "__ALL__":
            tagGroupsWhichCanBeGeneralisedWhenEmptyTL=ruleLearningLib.AT_LexicalTagsProcessor.get_tag_group_names()
        else:
            parts=args.tag_groups_generalised_empty_tl.decode('utf-8').split(u",")
            tagGroupsWhichCanBeGeneralisedWhenEmptyTL=set()
            for part in parts:
                    if len(parts)>0:
                            tagGroupsWhichCanBeGeneralisedWhenEmptyTL.add(part)

        if args.tag_groups_generalised_empty_sl  == "__ALL__":
            tagGroupsWhichCanBeGeneralisedWhenEmptySL=ruleLearningLib.AT_LexicalTagsProcessor.get_tag_group_names()
        else:
            parts=args.tag_groups_generalised_empty_sl.decode('utf-8').split(u",")
            tagGroupsWhichCanBeGeneralisedWhenEmptySL=set()
            for part in parts:
                    if len(parts)>0:
                            tagGroupsWhichCanBeGeneralisedWhenEmptySL.add(part)
        
        generalisationOptions=ruleLearningLib.AT_GeneralisationOptions()
        generalisationOptions.set_genWhenEmptySLCats(tagGroupsWhichCanBeGeneralisedWhenEmptySL)
        generalisationOptions.set_genWhenEmptyTLCats(tagGroupsWhichCanBeGeneralisedWhenEmptyTL)
        generalisationOptions.set_fromRightToLeft(args.generalise_from_right_to_left)
        generalisationOptions.set_refToBiling(args.ref_to_biling)
        generalisationOptions.set_addRestrictionsForEveryTag(args.add_restrictions_to_every_tag)
        generalisationOptions.set_generaliseNonMatchingToo(args.generalise_non_matching_too)
        generalisationOptions.set_differentRestrictionOptions(args.different_restriction_options)
        if args.only_to_be_determined_in_restriction:
            generalisationOptions.set_possibleValuesForRestrictions(ruleLearningLib.AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_TBDETERMINED)
        if args.only_to_be_determined_and_mf_in_restriction:
            generalisationOptions.set_possibleValuesForRestrictions(ruleLearningLib.AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_TBDETERMINEDANDMF)
        if args.only_to_be_determined_and_change_in_restriction:
            generalisationOptions.set_possibleValuesForRestrictions(ruleLearningLib.AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_TBDETERMINEDANDCHANGE)
        if args.only_tags_triggering_diference_in_restriction:
            generalisationOptions.set_possibleValuesForRestrictions(ruleLearningLib.AT_GeneralisationOptions.VALUE_FOR_RESTRICTION_TRIGGERINGCHANGE)
        generalisationOptions.set_generalise(not args.only_lexical)
        generalisationOptions.set_triggeringLimitedLength(args.triggering_limited_length)
        generalisationOptions.set_triggeringNoGoodDiscarded(args.triggering_no_good_discarded)
        generalisationOptions.set_discardRestrictionsNotImproving(args.discard_restrictions_not_improving)
        generalisationOptions.set_unlexicaliseUnalignedSL(args.unlexicalise_unaligned_sl)
        generalisationOptions.set_dontGeneraliseAllInstancesTogether(args.dont_generalise_all_instances_together)
        generalisationOptions.set_calculateGeneralisableAttributesLikeInPaper(args.generalisable_attributes_like_in_paper)
        
        generationMethod=AlignmentTemplateGenerationMethod.FIRST_APPROACH
        if args.rich_ats:
            generationMethod=AlignmentTemplateGenerationMethod.TL_VARIABLES
        
        if args.times_attributes_change:
            generalisationOptions.set_count_attribute_changes(open(args.times_attributes_change))
        
        
        allowedSLLemmas=None
        if args.ats_with_allowed_lemmas_file:
            allowedSLLemmas=set()
            gzip_files=False
            if args.ats_with_allowed_lemmas_file[-3:] == ".gz":
                gzip_files=True
            if gzip_files:
                file=gzip.open(args.ats_with_allowed_lemmas_file,'r')
            else:
                file=open(args.ats_with_allowed_lemmas_file,'r')
            for line in file:
                line=line.strip().decode('utf-8')
                at = ruleLearningLib.AlignmentTemplate()
                at.parse(line)
                allowedSLLemmas.add(tuple(at.get_sl_lemmas()))
            file.close()
        
        #Read bilingual phrases
        originalATList=list()
        
        #store bilingual phrases in an efficient way
        bilingualPhrases=ruleLearningLib.AlignmentTemplateSet()

        print >> sys.stderr, "Reading Bilingual Phrases...."
        bilid=0
        for line in inputFile:
            
            line=line.decode('utf-8')
            at = ruleLearningLib.AlignmentTemplate()
            bilphrase=ruleLearningLib.AlignmentTemplate()
            
            piecesOfline=line.split(u'|')
            textat=u'|'.join(piecesOfline[1:5])
            freq=piecesOfline[0].strip()
            
            sllemmastext=piecesOfline[5].strip()
            tllemmastext=piecesOfline[6].strip()
            sllemmas=sllemmastext.split(u'\t')
            tllemmas=tllemmastext.split(u'\t')
            
            at.parse(textat)
            at.add_explicit_empty_tags()
            at.freq=int(freq)
            tl_lemmas_from_dictionary_text=piecesOfline[7]
            tl_lemmas_from_dictionary_list=[ l.strip() for l in tl_lemmas_from_dictionary_text.split(u'\t')]

            originalATList.append((at,sllemmas,tllemmas,tl_lemmas_from_dictionary_list))
            
            bilphrase=copy.deepcopy(at)
            bilphrase.set_lemmas(sllemmas,tllemmas)
            bilphrase.tl_lemmas_from_dictionary=tl_lemmas_from_dictionary_list
            bilid+=1
            bilphrase.id=bilid
            bilingualPhrases.add(bilphrase)

        print >> sys.stderr, " ....."+str(len(originalATList))+" items."
        
        debug("All the bilingual phrases at the beginning:")
        for bilphrase in bilingualPhrases.get_all_ats_list():
            debug("\t"+str(bilphrase))
        
        #process
        process_bilingual_phrases(originalATList,bilingualPhrases,generalisationOptions,generationMethod, allowedSLLemmas)
