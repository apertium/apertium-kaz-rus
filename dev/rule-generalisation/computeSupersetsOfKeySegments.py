'''
Created on 07/10/2013

@author: vmsanchez
'''
from beamSearchLib import RuleApplicationHypothesis,RuleList,ParallelSentence
import argparse
import ruleLearningLib
import sys,gzip
from ruleLearningLib import debug,AlignmentTemplate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='obtain supersets of key segments which bring maximum score')
    parser.add_argument('--tag_groups_file_name',required=True)
    parser.add_argument('--tag_sequences_file_name',required=True)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--final_boxes_index',required=True)
    parser.add_argument('--alignment_templates',required=True)
    parser.add_argument('--sentences',required=True)
    parser.add_argument('--target_language',default='ca')
    parser.add_argument('--apertium_data_dir')
    
    args = parser.parse_args(sys.argv[1:])
    
    if args.debug:
        DEBUG=True
        ruleLearningLib.DEBUG=True
        
    ruleLearningLib.AT_LexicalTagsProcessor.initialize(args.tag_groups_file_name,args.tag_sequences_file_name)
    
    RuleApplicationHypothesis.set_target_language(args.target_language)
    RuleApplicationHypothesis.set_apertium_data_dir(args.apertium_data_dir)
    
    #this is useless, I think
    RuleApplicationHypothesis.set_minimum_covered_words(True)
    
    ruleList=RuleList()
    #load alignment templates
    if args.alignment_templates:
        gfile=gzip.open(args.alignment_templates)
        for line in gfile:
            line=line.strip().decode('utf-8')
            at=AlignmentTemplate()
            at.parse(line)
            ruleList.add(at)
        gfile.close()
    
    #load sentences
    sentences=list()
    if args.sentences:
        if args.sentences.lower().endswith('.gz'):
            gfile=gzip.open(args.sentences)
        else:
            gfile=open(args.sentences)
        for line in gfile:
            line=line.strip().decode('utf-8')
            parallelSentence=ParallelSentence()
            parallelSentence.parse(line, parseTlLemmasFromDic=True)
            parallelSentence.add_explicit_empty_tags()
            sentences.append(parallelSentence)
        gfile.close()
    
    boxesDic=dict()
    if args.final_boxes_index:
        for line in open(args.final_boxes_index):
            parts=line.split("\t")
            boxesDic[parts[1].strip()]=int(parts[0])
    
    #read best rule application for each sentence
    bestHypothesisForEachSentence=list()
    emptyIndexes=set()
    numLine=0
    for line in sys.stdin:
        line=line.decode('utf-8').strip()
        if len(line) > 0:
            parts=line.split(u"|||")
            bestHypothesisForEachSentence.append(RuleApplicationHypothesis.create_and_parse(parts[0],parseTranslation=True))
        else:
            bestHypothesisForEachSentence.append(None)
            emptyIndexes.add(numLine)
        numLine+=1
    
    if len(bestHypothesisForEachSentence) != len(sentences):
        print >> sys.stderr, "ERROR: different length of sentences and best hyportheses"
        exit()
    
    for numSentence,bestHyp in enumerate(bestHypothesisForEachSentence):
        sentence=sentences[numSentence]
        if numSentence not in emptyIndexes:
            bestHyp.set_source(sentence.parsed_sl_lexforms)
            bestHyp.set_reference(sentence.parsed_tl_lexforms)
            validHypothesisWithSuperset=bestHyp.compute_supersets_with_maximum_score(sentence,ruleList,boxesDic)
            print u"|||".join([unicode(h) for h in validHypothesisWithSuperset]).encode('utf-8')
        else:
            print ""    
    
    