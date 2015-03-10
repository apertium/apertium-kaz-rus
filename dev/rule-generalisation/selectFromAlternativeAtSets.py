'''
Created on 14/11/2013

@author: vitaka
'''
from beamSearchLib import RuleApplicationHypothesis,RuleList,ParallelSentence
import argparse
import ruleLearningLib
import sys,gzip
from ruleLearningLib import debug,AlignmentTemplate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='select alternative sets of Ats which maximise 1-BLEU score')
    parser.add_argument('--tag_groups_file_name',required=True)
    parser.add_argument('--tag_sequences_file_name',required=True)
    parser.add_argument('--debug', action='store_true')
    
    args = parser.parse_args(sys.argv[1:])
    
    if args.debug:
        DEBUG=True
        ruleLearningLib.DEBUG=True
        
    ruleLearningLib.AT_LexicalTagsProcessor.initialize(args.tag_groups_file_name,args.tag_sequences_file_name)
    
    l_best_hypothesis=list()
    for line in sys.stdin:
        line=line.decode('utf-8').strip()
        parts=line.split(u"|||")
        l_best_hypothesis.append(RuleApplicationHypothesis.create_and_parse(parts[0]))
        
    resultTuples=RuleApplicationHypothesis.select_boxes_from_alternative_at_sets(l_best_hypothesis)
    for boxid,altatset in resultTuples:
        print str(boxid)+"\t"+str(altatset)
