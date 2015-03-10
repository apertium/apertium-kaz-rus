'''
Created on 12/12/2013

@author: vitaka
'''
from beamSearchLib import ParallelSentence
import sys, ruleLearningLib, argparse,gzip
from collections import defaultdict

if __name__=="__main__":
    DEBUG=False
    parser = argparse.ArgumentParser(description='Extracts bilingual phrases.')
    parser.add_argument('--sentences')
    parser.add_argument('--advisors_method',action='store_true')
    parser.add_argument('--closed_categories')
    parser.add_argument('--variant')
    parser.add_argument('--extremes_variant',default='antiphrases')
    args = parser.parse_args(sys.argv[1:])
    
    singleAlignedtoConsiderContrary=True
    openMustBeAlignedWithOpen=False
    if args.variant == "paper" or args.variant == "paperopenwithopen":
        singleAlignedtoConsiderContrary=False
    if args.variant == "paperplusmax1openwithopen" or args.variant == "paperopenwithopen":
        openMustBeAlignedWithOpen=True
    
    closedCategoriesSet=set()
    if (not args.closed_categories or args.closed_categories == ""):
            print >> sys.stderr, "ERROR: Closed categories set not provided"
            exit()
    else:
        closedCategoriesSet=set( [ rawcat.decode('utf-8').strip()[1:-1] for rawcat in open(args.closed_categories)] )
        print >> sys.stderr, str(closedCategoriesSet)
    
    bslSet=ruleLearningLib.BilingualSequenceLexSet()
    
    parallelSentences=list()
    
    MYMETHOD=True
    if args.advisors_method:
        MYMETHOD=False
    
    #load sentences
    for line in gzip.open(args.sentences):
        line=line.rstrip('\n').decode('utf-8')
        #parts=line.split(u" | ")
        parallelSentence=ParallelSentence()
        #parallelSentence.parse(u" | ".join(parts[1:]), parseTlLemmasFromDic=False)
        parallelSentence.parse(line, parseTlLemmasFromDic=True)
        parallelSentence.add_special_start_end_words()
        parallelSentence.extract_antiphrases()
        parallelSentence.extract_bslt()
        parallelSentences.append(parallelSentence)
    
    #count bsl assuming all the phrases compatible with
    #the alignments can be extracted
    #for parallelSentence in parallelSentences:
        #parallelSentence.count_all_bsls(bslSet)
    
    #extract and store bilingual phrases
    #store also starting point in the sentence
    bilphrasesFromEachSentence=list()
    for parallelSentence in parallelSentences:
        bilphrases=parallelSentence.extract_all_biphrases()
        bilphrasesFromEachSentence.append(bilphrases)
    
    
    
    numSentence=0
    
    if MYMETHOD:
        for numSentence,parallelSentence in enumerate(parallelSentences):
            
            antiphraseResults=list()
            
            if args.extremes_variant == "antiphrases":
                print >> sys.stderr, "Parallel sentence "+str(numSentence)
                print >> sys.stderr, parallelSentence
                for antiphrase in parallelSentence.antiphrases:
                    print >> sys.stderr, "\tantiphrase: "+str(antiphrase)
                    
                    existsBestLeft=False
                    existsBestLeftAll=False
                    existsBestRight=False
                    existsBestRightAll=False
                    
                    bilphrasesLeft=parallelSentence.extract_bilphrases_containing_antiphrase(antiphrase,ParallelSentence.SIDE_LEFT)
                    bannedRightLexSL=parallelSentence.bslt.slseq[antiphrase[0][-1]+1] if len(antiphrase[0]) > 0 else parallelSentence.bslt.slseq[antiphrase[2][1]]
                    bannedRightLexTL=parallelSentence.bslt.tlseq[antiphrase[1][-1]+1] if len(antiphrase[1]) > 0 else parallelSentence.bslt.tlseq[antiphrase[2][1]]
                    print >> sys.stderr, "\tBilphrases left:"
                    for bilphrase in bilphrasesLeft:
                        #bslt=ruleLearningLib.BilingualSequenceLexTags()
                        #bslt.load_from_at(bilphrase)
                        bsltWildcards=ruleLearningLib.BilingualSequenceLexTags()
                        bsltWildcards.load_from_at(bilphrase,unalignedEdgesBecomeWildcards=True,side=ruleLearningLib.BilingualSequenceLexTags.UNALIGNED_SIDE_RIGHT)
                        
                        wildCardValuesReferenceSL=list()
                        wildCardValuesReferenceTL=list()
                        startSLIndex=len(bilphrase.parsed_sl_lexforms)-len(antiphrase[0])
                        for i in range(len(antiphrase[0])):
                            wildCardValuesReferenceSL.append(bilphrase.bslt.slseq[startSLIndex+i])
                        startTLIndex=len(bilphrase.parsed_tl_lexforms)-len(antiphrase[1])
                        for i in range(len(antiphrase[1])):
                            wildCardValuesReferenceTL.append(bilphrase.bslt.tlseq[startTLIndex+i])
                        wilcardValuesReferenceStr=str((wildCardValuesReferenceSL,wildCardValuesReferenceTL))
                        
                        countsForThisBilphrase=defaultdict(int)
                        countsAllForThisBilphrase=defaultdict(int)
                        
                        for sentencei,parallelSentence2 in enumerate(parallelSentences):
                            for bilphrase2 in  bilphrasesFromEachSentence[sentencei]:
                                if len(bilphrase2.parsed_sl_lexforms) == len(bilphrase.parsed_sl_lexforms) and len(bilphrase2.parsed_tl_lexforms) == len(bilphrase.parsed_tl_lexforms):
                                    if bilphrase2.bslt.matches_wildcards(bsltWildcards):
                                        #check right side
                                        rightSideLexSL=parallelSentence2.bslt.slseq[bilphrase2.sl_position_in_sentence+len(bilphrase2.parsed_sl_lexforms)]
                                        rightSideLexTL=parallelSentence2.bslt.tlseq[bilphrase2.tl_position_in_sentence+len(bilphrase2.parsed_tl_lexforms)]
                                        
                                        
                                        wildcardValuesSL=list()
                                        wildcardValuesTL=list()
                                        startSLIndex=len(bilphrase2.parsed_sl_lexforms)-len(antiphrase[0])
                                        for i in range(len(antiphrase[0])):
                                            wildcardValuesSL.append(bilphrase2.bslt.slseq[startSLIndex+i])
                                        startTLIndex=len(bilphrase2.parsed_tl_lexforms)-len(antiphrase[1])
                                        for i in range(len(antiphrase[1])):
                                            wildcardValuesTL.append(bilphrase2.bslt.tlseq[startTLIndex+i])
                                        countsAllForThisBilphrase[str((wildcardValuesSL,wildcardValuesTL))]+=1
                                        
                                        #if rightSideLexSL != bannedRightLexSL and rightSideLexTL != bannedRightLexTL:
                                        if rightSideLexSL != bannedRightLexSL or rightSideLexTL != bannedRightLexTL:
                                            countsForThisBilphrase[str((wildcardValuesSL,wildcardValuesTL))]+=1
                        
                        #sort wildcarded values by freq
                        sortedCounts=sorted(countsForThisBilphrase.items(),key=lambda i: i[1], reverse=True)
                        winners=list()
                        if len(sortedCounts) > 0:
                            if len(sortedCounts) == 1 or sortedCounts[1][1]<sortedCounts[0][1]:
                                winners.append(sortedCounts[0][0])
                            #for i in xrange(1,len(sortedCounts)):
                            #    if sortedCounts[i][1] == sortedCounts[0][1]:
                            #        winners.append(sortedCounts[0])
                            #    else:
                            #        break
                        
                        #discount myself
                        countsAllForThisBilphrase[wilcardValuesReferenceStr]-=1 
                        sortedCountsAll=sorted([item for item in countsAllForThisBilphrase.items() if item[1] > 0],key=lambda i: i[1], reverse=True)
                        winnersAll=list()
                        if len(sortedCountsAll) > 0:
                            if len(sortedCountsAll) == 1 or sortedCountsAll[1][1]<sortedCountsAll[0][1]:
                                winnersAll.append(sortedCountsAll[0][0])
                            
                        print >> sys.stderr, "\t\t"+str(bilphrase)+" values for antiphrase slots: "+str(sortedCounts) 
                        print >> sys.stderr, "\t\t"+str(bilphrase)+" values for antiphrase slots (all): "+str(sortedCountsAll)
                        
                        #decide whether option is 
                        if wilcardValuesReferenceStr in winners:
                            existsBestLeft=True
                            print >> sys.stderr, "\t\tantiphrase subbilphrase is the most common one"
                        if wilcardValuesReferenceStr in winnersAll:
                            existsBestLeftAll=True
                            print >> sys.stderr, "\t\tantiphrase subbilphrase is the most common one (all)"
                        
                    bilphrasesRight=parallelSentence.extract_bilphrases_containing_antiphrase(antiphrase,ParallelSentence.SIDE_RIGHT)
                    bannedLeftLexSL=parallelSentence.bslt.slseq[antiphrase[0][0]-1] if len(antiphrase[0]) > 0 else parallelSentence.bslt.slseq[antiphrase[2][0]]
                    bannedLeftLexTL=parallelSentence.bslt.tlseq[antiphrase[1][0]-1] if len(antiphrase[1]) > 0 else parallelSentence.bslt.tlseq[antiphrase[2][0]]
                    print >> sys.stderr, "\tBilphrases right:"
                    for bilphrase in bilphrasesRight:
                        bsltWildcards=ruleLearningLib.BilingualSequenceLexTags()
                        bsltWildcards.load_from_at(bilphrase,unalignedEdgesBecomeWildcards=True,side=ruleLearningLib.BilingualSequenceLexTags.UNALIGNED_SIDE_LEFT)
                        
                        wildCardValuesReferenceSL=list()
                        wildCardValuesReferenceTL=list()
                        startSLIndex=0
                        for i in range(len(antiphrase[0])):
                            wildCardValuesReferenceSL.append(bilphrase.bslt.slseq[startSLIndex+i])
                        startTLIndex=0
                        for i in range(len(antiphrase[1])):
                            wildCardValuesReferenceTL.append(bilphrase.bslt.tlseq[startTLIndex+i])
                        wilcardValuesReferenceStr=str((wildCardValuesReferenceSL,wildCardValuesReferenceTL))
                        
                        countsForThisBilphrase=defaultdict(int)
                        countsAllForThisBilphrase=defaultdict(int)
                        
                        for sentencei,parallelSentence2 in enumerate(parallelSentences):
                            for bilphrase2 in  bilphrasesFromEachSentence[sentencei]:
                                if len(bilphrase2.parsed_sl_lexforms) == len(bilphrase.parsed_sl_lexforms) and len(bilphrase2.parsed_tl_lexforms) == len(bilphrase.parsed_tl_lexforms):
                                    if bilphrase2.bslt.matches_wildcards(bsltWildcards):
                                        #check left side
                                        leftSideLexSL=parallelSentence2.bslt.slseq[bilphrase2.sl_position_in_sentence-1]
                                        leftSideLexTL=parallelSentence2.bslt.tlseq[bilphrase2.tl_position_in_sentence-1]
                                        
                                        
                                        wildcardValuesSL=list()
                                        wildcardValuesTL=list()
                                        startSLIndex=0
                                        for i in range(len(antiphrase[0])):
                                            wildcardValuesSL.append(bilphrase2.bslt.slseq[startSLIndex+i])
                                        startTLIndex=0
                                        for i in range(len(antiphrase[1])):
                                            wildcardValuesTL.append(bilphrase2.bslt.tlseq[startTLIndex+i])
                                        countsAllForThisBilphrase[str((wildcardValuesSL,wildcardValuesTL))]+=1
                                        #if leftSideLexSL != bannedLeftLexSL and leftSideLexTL != bannedLeftLexTL:
                                        if leftSideLexSL != bannedLeftLexSL or leftSideLexTL != bannedLeftLexTL:
                                            countsForThisBilphrase[str((wildcardValuesSL,wildcardValuesTL))]+=1
                        
                        #sort wildcarded values by freq
                        sortedCounts=sorted(countsForThisBilphrase.items(),key=lambda i: i[1], reverse=True)
                        winners=list()
                        if len(sortedCounts) > 0: 
                            if len(sortedCounts) == 1 or sortedCounts[1][1]<sortedCounts[0][1]:
                                winners.append(sortedCounts[0][0])               
                            #for i in xrange(1,len(sortedCounts)):
                            #    if sortedCounts[i][1] == sortedCounts[0][1]:
                            #        winners.append(sortedCounts[0])
                            #    else:
                            #        break
                            
                        #discount myself
                        countsAllForThisBilphrase[wilcardValuesReferenceStr]-=1
                        sortedCountsAll=sorted([ item for item in countsAllForThisBilphrase.items() if item[1] > 0 ],key=lambda i: i[1], reverse=True)
                        winnersAll=list()
                        if len(sortedCountsAll) > 0: 
                            if len(sortedCountsAll) == 1 or sortedCountsAll[1][1]<sortedCountsAll[0][1]:
                                winnersAll.append(sortedCountsAll[0][0])               
                        
                        print >> sys.stderr, "\t\t"+str(bilphrase)+" values for antiphrase slots: "+str(sortedCounts) 
                        print >> sys.stderr, "\t\t"+str(bilphrase)+" values for antiphrase slots (all): "+str(sortedCountsAll)
                        
                        #decide whether option is 
                        if wilcardValuesReferenceStr in winners:
                            existsBestRight=True
                            print >> sys.stderr, "\t\tantiphrase subbilphrase is the most common one"
                        if wilcardValuesReferenceStr in winnersAll:
                            existsBestRightAll=True
                            print >> sys.stderr, "\t\tantiphrase subbilphrase is the most common one (all)"
                    
                    if existsBestLeft and not existsBestRight:
                        antiphraseResults.append(parallelSentence.SIDE_LEFT)
                        print >> sys.stderr, "\tAntiphrase attached to left"
                    elif  not existsBestLeft and existsBestRight:
                        antiphraseResults.append(parallelSentence.SIDE_RIGHT)
                        print >> sys.stderr, "\tAntiphrase attached to right"
                    else:
                        antiphraseResults.append(parallelSentence.SIDE_NONE)
                        print >> sys.stderr, "\tAntiphrase not attached"
                    
                    if existsBestLeftAll and not existsBestRightAll:
                        print >> sys.stderr, "\tAntiphrase attached to left (all)"
                    elif  not existsBestLeftAll and existsBestRightAll:
                        print >> sys.stderr, "\tAntiphrase attached to right (all)"
                    elif not existsBestLeftAll and not existsBestRightAll:
                        print >> sys.stderr, "\tAntiphrase not attached (all)"
                    else:
                        print >> sys.stderr, "\tAntiphrase not attached: backoff (all)"
            
            #extract bilphrases with edges aligned or
            #containing chosen antiphrases
            for bilphrase in bilphrasesFromEachSentence[numSentence]:
                extremesOK=False
                if args.extremes_variant == "antiphrases":
                    if not bilphrase.is_contiguous_to_antiphrase(parallelSentence.antiphrases,antiphraseResults) and (bilphrase.is_ends_aligned() or bilphrase.unaligned_edges_match_antiphrase(parallelSentence.antiphrases,antiphraseResults)):
                        extremesOK=True
                elif args.extremes_variant == "ends_aligned":
                    if bilphrase.is_ends_aligned():
                        extremesOK=True
                elif args.extremes_variant == "all":
                    extremesOK=True
                else:
                    print >> sys.stderr, "Wrong extremes variant"
                if extremesOK:
                    if bilphrase.aligned_words_of_open_categories_match_dictionary_translation(closedCategoriesSet,bilphrase.tl_lemmas_from_dictionary,singleAlignedtoConsiderContrary,openMustBeAlignedWithOpen) or args.variant == "allowincompwithbildic":
                        sl_lemmas,tl_lemmas=bilphrase.extract_lemmas()
                        print bilphrase.to_string(removeRestrictionsFromLexicalised=False,printDictionaryTranslations=False,useSecondEmptyRepresentation=True)+" | "+u"\t".join(sl_lemmas).encode('utf-8')+" | "+u"\t".join(tl_lemmas).encode('utf-8')+" | "+u"\t".join(bilphrase.tl_lemmas_from_dictionary).encode('utf-8')
                        #print bilphrase.to_string(removeRestrictionsFromLexicalised=False,printDictionaryTranslations=True,useSecondEmptyRepresentation=True)
    else:
        #decide about antiphrases
        antiphrasesResultsCache=dict()
        for parallelSentence in parallelSentences:
            numSentence+=1
            print >> sys.stderr, "Parallel sentence "+str(numSentence)
            print >> sys.stderr, parallelSentence
            for antiphrase in parallelSentence.antiphrases:
                lexPrevSL,lexPrevTL,lexListSL,lexListTL,lexPostSL,lexPostTL = parallelSentence.extract_lex_and_context_from_antiphrase(antiphrase)
                cacheKey=u"|".join([lexPrevSL,lexPrevTL,unicode(lexListSL),unicode(lexListTL),lexPostSL,lexPostTL])
                
                if cacheKey  not in antiphrasesResultsCache:
                    leftCount=0
                    rightCount=0
                    otherCount=0
                    
                    for parallelSentence2 in parallelSentences:
                        for antiphrase2 in parallelSentence2.antiphrases:
                            lexPrevSL2,lexPrevTL2,lexListSL2,lexListTL2,lexPostSL2,lexPostTL2 = parallelSentence2.extract_lex_and_context_from_antiphrase(antiphrase2)                        
                            if lexListSL == lexListSL2 and lexListTL == lexListTL2:
                                print >> sys.stderr, "\tComparing with: "+lexPrevSL2+" [ "+str(lexListSL2)+" ] "+lexPostSL2+" -> "+lexPrevTL2+" [ "+str(lexListTL2)+" ] "+lexPostTL2
                                if lexPrevSL == lexPrevSL2 and lexPrevTL == lexPrevTL2 and lexPostSL != lexPostSL2 and lexPostTL != lexPostTL2:
                                    leftCount+=1
                                elif lexPrevSL != lexPrevSL2 and lexPrevTL != lexPrevTL2 and lexPostSL == lexPostSL2 and lexPostTL == lexPostTL2:
                                    rightCount+=1
                                else:
                                    otherCount+=1
                    antiphrasesResultsCache[cacheKey]=(leftCount,rightCount,otherCount)
                    if leftCount > rightCount and leftCount > otherCount:
                        winner="LEFT"
                    elif rightCount > leftCount and rightCount > otherCount:
                        winner="RIGHT"
                    else:
                        winner="OTHER"
                    print lexPrevSL+" [ "+str(lexListSL)+" ] "+lexPostSL+" -> "+lexPrevTL+" [ "+str(lexListTL)+" ] "+lexPostTL+" | "+"left: "+str(leftCount)+"; right: "+str(rightCount)+"; other: "+str(otherCount)+" Winner="+winner
                
                leftc,rightc,otherc=antiphrasesResultsCache[cacheKey]
                print >> sys.stderr, "Antiphrase: "+str(antiphrase)
                print >> sys.stderr, lexPrevSL+" [ "+str(lexListSL)+" ] "+lexPostSL+" -> "+lexPrevTL+" [ "+str(lexListTL)+" ] "+lexPostTL
                print >> sys.stderr, "left: "+str(leftc)+"; right: "+str(rightc)+"; other: "+str(otherc)
                
                
            
            
    
