'''
Created on 12/02/2014

@author: vitaka
'''
#stdinput: sentences to be translated
from beamSearchLib import RuleList, ParallelSentence, RuleApplicationHypothesis
from ruleLearningLib import AlignmentTemplate
import ruleLearningLib
import argparse
import gzip
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--tag_groups_file_name',required=True)
    parser.add_argument('--tag_sequences_file_name',required=True)
    args = parser.parse_args(sys.argv[1:])
    
    ruleLearningLib.AT_LexicalTagsProcessor.initialize(args.tag_groups_file_name,args.tag_sequences_file_name)
    for line in sys.stdin:
        line=line.rstrip('\n').decode('utf-8')
        print "Parsing ..."
        print line.encode('utf-8')
        parallelSentence=ParallelSentence()
        parallelSentence.parse(line, parseTlLemmasFromDic=True)
        parallelSentence.add_explicit_empty_tags()
    print "Everything OK"