'''
Created on 08/12/2013

@author: vitaka
'''
from beamSearchLib import ParallelSentence
import sys, ruleLearningLib, argparse,gzip

if __name__=="__main__":
    DEBUG=False
    parser = argparse.ArgumentParser(description='Selects bilingual phrases.')
    parser.add_argument('--sentences')
    parser.add_argument('--allowed_counts_lextags')
    args = parser.parse_args(sys.argv[1:])
    
    bslSetToRemove=ruleLearningLib.BilingualSequenceLexSet()
    
    #load lextags counts
    allowedCountsLextags=ruleLearningLib.BilingualSequenceLexSet()
    if args.allowed_counts_lextags:
        mystr=open(args.allowed_counts_lextags).read().decode('utf-8')
        allowedCountsLextags.parse(mystr)
        print >> sys.stderr, "Loaded counts for "+str(len(allowedCountsLextags.freqmap.keys()))+" seqs of lexical tags"
    
    
    numSentence=0
    
    countsToRemoveCache=dict()
    
    parallelSentences=list()
    
    #process sentences
    for line in gzip.open(args.sentences):
        
        numSentence+=1
        
        line=line.rstrip('\n').decode('utf-8')
        #parts=line.split(u" | ")
        parallelSentence=ParallelSentence()
        #parallelSentence.parse(u" | ".join(parts[1:]), parseTlLemmasFromDic=False)
        parallelSentence.parse(line, parseTlLemmasFromDic=False)
        parallelSentence.extract_antiphrases()
        parallelSentences.append(parallelSentence)
        
    for numSentence,parallelSentence in enumerate(parallelSentences):
        numSentence+=1
        print >> sys.stderr, "Parallel sentence "+str(numSentence)
        print >> sys.stderr, parallelSentence
        
        for antiphrase in parallelSentence.antiphrases:
            print >> sys.stderr, "\t antiphrase: "+str(antiphrase)
            bilphrasesLeft=parallelSentence.extract_bilphrases_containing_antiphrase(antiphrase,ParallelSentence.SIDE_LEFT)
            probsLeft=list()
            probsIndependentLeft=list()
            print >> sys.stderr, "\tBilphrases left:"
            for bilphrase in bilphrasesLeft:
                if not bilphrase.contains_unk_or_punct():
                    bsla=ruleLearningLib.BilingualSequenceLexTags()
                    bsla.load_from_at(bilphrase)
                    bslb=ruleLearningLib.BilingualSequenceLexTags()
                    bslb.load_from_at(bilphrase,unalignedEdgesBecomeWildcards=True,side=ruleLearningLib.BilingualSequenceLexTags.UNALIGNED_SIDE_RIGHT)
                    freqOfAUndiscounted=allowedCountsLextags.get_freq(bsla) 
                    freqOfA=freqOfAUndiscounted-1
                    freqOfCompatibleUndiscounted=allowedCountsLextags.sum_freqs_of_compatible_seqs(bslb)
                    freqOfCompatible=freqOfCompatibleUndiscounted-1
                    # Find bilphrases, in the whole corpus, attached to the same word classes. they will be 
                    # discounted    
                    # Numerator: bilphrase + first SL and first TL of right side of antiphrase 
                    # Denominator: bilphrase minus antiphrase + * proportional to antiphrase + first SL and first TL of right side of antiphrase
                    slindexattached= antiphrase[0][-1]+1 if len(antiphrase[0]) > 0 else antiphrase[2][1]
                    tlindexattached=antiphrase[1][-1]+1 if len(antiphrase[1]) > 0 else antiphrase[2][1]
                    
                    if slindexattached >=len(parallelSentence.parsed_sl_lexforms) or tlindexattached >=len(parallelSentence.parsed_tl_lexforms):
                         countsToRemoveNumerator=1
                         countsToRemoveDenominator=1
                    else:
                        bslNumerator=bsla.copy()
                        bslNumerator.attach_lexform_sl_right(parallelSentence.parsed_sl_lexforms[slindexattached])
                        bslNumerator.attach_lexform_tl_right(parallelSentence.parsed_tl_lexforms[tlindexattached])
                        
                        bslDenominator=bslb.copy()
                        bslDenominator.attach_lexform_sl_right(parallelSentence.parsed_sl_lexforms[slindexattached])
                        bslDenominator.attach_lexform_tl_right(parallelSentence.parsed_tl_lexforms[tlindexattached])
                        
                        countsToRemoveNumerator=0
                        countsToRemoveDenominator=0
                        
                        for parallelSentence2 in parallelSentences:
                            countNumerator,countDenominator=parallelSentence2.count_bsls(bslNumerator,bslDenominator,allowUnknownAndPunctSide=ParallelSentence.SIDE_RIGHT)
                            countsToRemoveNumerator+=countNumerator
                            countsToRemoveDenominator+=countDenominator
                   
                    freqOfADiscounted=freqOfAUndiscounted-countsToRemoveNumerator
                    freqOfCompatibleDiscounted=freqOfCompatibleUndiscounted-countsToRemoveDenominator
                    prob= freqOfA*1.0/freqOfCompatible if freqOfCompatible > 0 else -1 
                    probIndependent= freqOfADiscounted*1.0/freqOfCompatibleDiscounted if freqOfCompatibleDiscounted > 0 else -1
                    print >> sys.stderr, "\t\t"+str(bilphrase)+" p="+str(freqOfA)+"/"+str(freqOfCompatible)+"="+str(prob)+" p_independent="+str(freqOfADiscounted)+"/"+str(freqOfCompatibleDiscounted)+"="+str( probIndependent )
                    
                    probsLeft.append(prob)
                    probsIndependentLeft.append(probIndependent)
            
            bilphrasesRight=parallelSentence.extract_bilphrases_containing_antiphrase(antiphrase,ParallelSentence.SIDE_RIGHT)
            probsRight =list()
            probsIndependentRight=list()
            print >> sys.stderr, "\tBilphrases right:"
            for bilphrase in bilphrasesRight:
                if not bilphrase.contains_unk_or_punct():
                    bsla=ruleLearningLib.BilingualSequenceLexTags()
                    bsla.load_from_at(bilphrase)
                    bslb=ruleLearningLib.BilingualSequenceLexTags()
                    bslb.load_from_at(bilphrase,unalignedEdgesBecomeWildcards=True,side=ruleLearningLib.BilingualSequenceLexTags.UNALIGNED_SIDE_LEFT) 
                    #freqOfA=allowedCountsLextags.get_freq(bsla)-1
                    #freqOfCompatible=allowedCountsLextags.sum_freqs_of_compatible_seqs(bslb)-1
                    freqOfAUndiscounted=allowedCountsLextags.get_freq(bsla) 
                    freqOfA=freqOfAUndiscounted-1
                    freqOfCompatibleUndiscounted=allowedCountsLextags.sum_freqs_of_compatible_seqs(bslb)
                    freqOfCompatible=freqOfCompatibleUndiscounted-1
                    
                    slindexattached=antiphrase[0][0]-1 if len(antiphrase[0]) > 0 else antiphrase[2][0]
                    tlindexattached=antiphrase[1][0]-1 if len(antiphrase[1]) > 0 else antiphrase[2][0]
                    
                    if slindexattached < 0 or tlindexattached < 0:
                        countsToRemoveNumerator=1
                        countsToRemoveDenominator=1
                    else:
                        bslNumerator=bsla.copy()
                        bslNumerator.attach_lexform_sl_left(parallelSentence.parsed_sl_lexforms[slindexattached])
                        bslNumerator.attach_lexform_tl_left(parallelSentence.parsed_tl_lexforms[tlindexattached])
                        
                        bslDenominator=bslb.copy()
                        bslDenominator.attach_lexform_sl_left(parallelSentence.parsed_sl_lexforms[slindexattached])
                        bslDenominator.attach_lexform_tl_left(parallelSentence.parsed_tl_lexforms[tlindexattached])
                        
                        countsToRemoveNumerator=0
                        countsToRemoveDenominator=0
                        
                        for parallelSentence2 in parallelSentences:
                            countNumerator,countDenominator=parallelSentence2.count_bsls(bslNumerator,bslDenominator,allowUnknownAndPunctSide=ParallelSentence.SIDE_LEFT)
                            countsToRemoveNumerator+=countNumerator
                            countsToRemoveDenominator+=countDenominator
                    
                    freqOfADiscounted=freqOfAUndiscounted-countsToRemoveNumerator
                    freqOfCompatibleDiscounted=freqOfCompatibleUndiscounted-countsToRemoveDenominator
                    
                    prob= freqOfA*1.0/freqOfCompatible if freqOfCompatible > 0 else -1 
                    probIndependent= freqOfADiscounted*1.0/freqOfCompatibleDiscounted if freqOfCompatibleDiscounted > 0 else -1
                    
                    print >> sys.stderr, "\t\t"+str(bilphrase)+" p="+str(freqOfA)+"/"+str(freqOfCompatible)+"="+str( prob )+" p_independent="+str(freqOfADiscounted)+"/"+str(freqOfCompatibleDiscounted)+"="+str( probIndependent)
                    
                    probsRight.append(prob)
                    probsIndependentRight.append(probIndependent)
            
            if len(probsIndependentLeft) > 0 and len(probsIndependentRight) > 0:
                highestLeftindp=max(probsIndependentLeft)
                highestRightindp=max(probsIndependentRight)
                
                THRESHOLD=0.5
                
                removeLeft=True
                removeRight=True
                
                if highestLeftindp >= THRESHOLD and not highestRightindp >= THRESHOLD:
                    #left wins. remove count from right
                    removeLeft=False
                elif not highestLeftindp >= THRESHOLD and  highestRightindp >= THRESHOLD:
                    #right wins, remove count from left
                    removeRight=False
                
                if removeLeft:
                    for bilphrase in bilphrasesLeft:
                        bsl=ruleLearningLib.BilingualSequenceLexTags()
                        bsl.load_from_at(bilphrase)
                        bslSetToRemove.add(bsl)
                if removeRight:
                    for bilphrase in bilphrasesRight:
                        bsl=ruleLearningLib.BilingualSequenceLexTags()
                        bsl.load_from_at(bilphrase)
                        bslSetToRemove.add(bsl)
                
    print bslSetToRemove           
            
    