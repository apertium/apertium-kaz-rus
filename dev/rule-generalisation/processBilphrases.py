#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-

import sys, ruleLearningLib, argparse,gzip
from ruleLearningLib import  AllowedStructuresSet

if __name__=="__main__":
    DEBUG=False
    parser = argparse.ArgumentParser(description='Selects bilingual phrases.')
    parser.add_argument('--extract_structures',action='store_true')
    parser.add_argument('--extract_counts_lextags',action='store_true')
    parser.add_argument('--closed_categories')
    parser.add_argument('--ends_must_be_aligned',action='store_true')
    parser.add_argument('--allowed_structures')
    parser.add_argument('--allowed_counts_lextags')
    parser.add_argument('--counts_lextags_to_remove')
    parser.add_argument('--allow_all_alignments',action='store_true')
    parser.add_argument('--variant',default='')
    parser.add_argument('--input')
    #value = dir in which bilphrases will be written
    #ATs = std output
    args = parser.parse_args(sys.argv[1:])
    
    singleAlignedtoConsiderContrary=True
    openMustBeAlignedWithOpen=False
    if args.variant == "paper" or args.variant == "paperopenwithopen":
        singleAlignedtoConsiderContrary=False
    if args.variant == "paperplusmax1openwithopen" or args.variant == "paperopenwithopen":
        openMustBeAlignedWithOpen=True
        
    
    closedCategoriesSet=set()
    if (not args.closed_categories or args.closed_categories == ""):
        if not args.allow_all_alignments and not args.extract_counts_lextags:
            print >> sys.stderr, "ERROR: Closed categories set not provided"
            exit()
    else:
        closedCategoriesSet=set( [ rawcat.decode('utf-8').strip()[1:-1] for rawcat in open(args.closed_categories)] )
        print >> sys.stderr, str(closedCategoriesSet)
    
    allKindsOfAlignmentsAreAllowed=args.allow_all_alignments
    
    allowedStructuresSet=AllowedStructuresSet()
    if args.allowed_structures:
        structfile=gzip.open(args.allowed_structures)
        for line in structfile:
            line=line.decode('utf-8').strip()
            at = ruleLearningLib.AlignmentTemplate()
            at.parse(line)
            allowedStructuresSet.add(at)
        structfile.close()
    
    bslSet=ruleLearningLib.BilingualSequenceLexSet()
    
    allowedCountsLextags=ruleLearningLib.BilingualSequenceLexSet()
    allowedCountsLextagsToRemove=ruleLearningLib.BilingualSequenceLexSet()
    if args.allowed_counts_lextags:
        mystr=open(args.allowed_counts_lextags).read().decode('utf-8')
        allowedCountsLextags.parse(mystr)
        print >> sys.stderr, "Loaded counts for "+str(len(allowedCountsLextags.freqmap.keys()))+" seqs of lexical tags"
    
    allowedCountsLextagsToRemove=ruleLearningLib.BilingualSequenceLexSet()
    if args.counts_lextags_to_remove:
        mystr=open(args.counts_lextags_to_remove).read().decode('utf-8')
        allowedCountsLextagsToRemove.parse(mystr)
        print >> sys.stderr, "Loaded counts for "+str(len(allowedCountsLextagsToRemove.freqmap.keys()))+" seqs of lexical tags for removing"
    
    if args.input:
        input=open(args.input)
    else:
        input=sys.stdin
    for line in input:
        line=line.decode('utf-8')
        pieces=line.split(u'|')
        freqstr=pieces[0]
        
        for i in range(4):
            pieces[i]=pieces[i].strip()
        
        atstr=u'|'.join(pieces[1:4])+" | "
        at = ruleLearningLib.AlignmentTemplate()
        at.parse(atstr)
        
        if args.extract_counts_lextags:
            #if not at.is_ends_aligned():
            #    sllex,tllex = at.get_sequences_of_lextags()
            #    sllexendsal,tllexendsal = at.get_sequences_of_lextags_ends_aligned()
            #    print " ".join([str(lf) for lf in sllex])+" -> "+" ".join([str(lf) for lf in tllex])+" | "+" ".join([str(lf) for lf in sllexendsal])+" -> "+" ".join([str(lf) for lf in tllexendsal])
            bslt = ruleLearningLib.BilingualSequenceLexTags()
            bslt.load_from_at(at)
            bslSet.add(bslt)
            
        else:
            #add restrictions
            tllemmasFromDic=list()
            #split(u"/") makes the system work with bildics with multiple entries
            wordsFromBiling= [ w.strip().split(u"/")[0] for w in pieces[4].split(u"\t") ]
            at.parsed_restrictions=[]
            for word in wordsFromBiling:
                restriction=ruleLearningLib.AT_Restriction()
                restriction.parse(word)
                at.parsed_restrictions.append(restriction)
                tllemmasFromDic.append(ruleLearningLib.get_lemma(word))
            atOK=True
            if len(at.parsed_restrictions) != len(at.parsed_sl_lexforms):
                print >> sys.stderr, "Discarding line due to different length of restrictions and SL lexical forms: "+line.encode('utf-8')
                atOK=False
            #check that aligned words of open categories match dictionary translation
            if atOK and (allKindsOfAlignmentsAreAllowed or at.aligned_words_of_open_categories_match_dictionary_translation(closedCategoriesSet,tllemmasFromDic,singleAlignedtoConsiderContrary,openMustBeAlignedWithOpen)):
                validAT=False
                if args.allowed_counts_lextags:
                    
                    if not args.ends_must_be_aligned or at.is_ends_aligned():
                        validAT=True
                    else:
                        bsla=ruleLearningLib.BilingualSequenceLexTags()
                        bsla.load_from_at(at)
                        bslb=ruleLearningLib.BilingualSequenceLexTags()
                        bslb.load_from_at(at,unalignedEdgesBecomeWildcards=True)
                        
                        freqOfA=allowedCountsLextags.get_freq(bsla)-1-allowedCountsLextagsToRemove.get_freq(bsla)
                        freqOfCompatible=allowedCountsLextags.sum_freqs_of_compatible_seqs(bslb)-1
                        
                        print >> sys.stderr, "Biphrase: "+str(at)
                        print >> sys.stderr, "Tag sequences: "+str(bsla)
                        print >> sys.stderr, "Freq in the corpus of tag sequences (excluding myself): "+str(freqOfA)
                        print >> sys.stderr, "Wildcarded version: "+str(bslb)
                        print >> sys.stderr, "Freq of tag sequences compatible w/ wildcarded (excluding myself): "+str(freqOfCompatible)
                        print >> sys.stderr, "Probability: "+str( (freqOfA*1.0 /freqOfCompatible) if freqOfCompatible > 0 else -1  )
                        print >> sys.stderr, ""
                    
                elif not args.ends_must_be_aligned or at.is_ends_aligned() or allowedStructuresSet.is_at_allowed(at):
                    validAT=True 
                
                if validAT:
                    sl_lemmas,tl_lemmas=at.extract_lemmas()
                    
                    if args.extract_structures:
                        at.remove_all_inflection_tags()
                        at.remove_all_lemmas()
                        print at
                    else:
                        extensionMarker=""
                        #if not at.is_ends_aligned() and allowedStructuresSet.is_at_allowed(at):
                        #    extensionMarker=" | extension"
                        print freqstr.strip().encode('utf-8')+" | "+at.__repr__()+" | "+u"\t".join(sl_lemmas).encode('utf-8')+" | "+u"\t".join(tl_lemmas).encode('utf-8')+" | "+u"\t".join(tllemmasFromDic).encode('utf-8')+extensionMarker
    if args.extract_counts_lextags:
        #print statitics
        print bslSet
                 
            