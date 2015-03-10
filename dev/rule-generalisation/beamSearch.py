'''
Created on 06/06/2013

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
    parser = argparse.ArgumentParser(description='compute possible coverages of rules and associated 1-BLEU score')
    parser.add_argument('--alignment_templates',required=True)
    parser.add_argument('--alternative_alignment_templates')
    parser.add_argument('--tag_groups_file_name',required=True)
    parser.add_argument('--tag_sequences_file_name',required=True)
    parser.add_argument('--target_language',default='ca')
    parser.add_argument('--apertium_data_dir')
    parser.add_argument('--final_boxes_index')
    parser.add_argument('--beam_size',default='1000')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--minimum_covered_words', action='store_true')
    parser.add_argument('--allow_incompatible_rules', action='store_true')
    args = parser.parse_args(sys.argv[1:])
    
    if args.debug:
        DEBUG=True
        ruleLearningLib.DEBUG=True
    
    ruleLearningLib.AT_LexicalTagsProcessor.initialize(args.tag_groups_file_name,args.tag_sequences_file_name)
    
    ruleList=RuleList()
    
    RuleApplicationHypothesis.set_target_language(args.target_language)
    RuleApplicationHypothesis.set_apertium_data_dir(args.apertium_data_dir)
    RuleApplicationHypothesis.set_minimum_covered_words(args.minimum_covered_words)
    
    #load alignment templates
    gfile=gzip.open(args.alignment_templates)
    for line in gfile:
        line=line.strip().decode('utf-8')
        at=AlignmentTemplate()
        at.parse(line)
        ruleList.add(at)
    gfile.close()
    ruleLists=[ruleList]
    
    if args.alternative_alignment_templates:
        altRuleList=RuleList()
        gfile=gzip.open(args.alternative_alignment_templates)
        for line in gfile:
            line=line.strip().decode('utf-8')
            at=AlignmentTemplate()
            at.parse(line)
            altRuleList.add(at)
        gfile.close()
        ruleLists=[ruleList,altRuleList]
    
    boxesCoverage=False
    boxesDic=dict()
    if args.final_boxes_index:
        for line in open(args.final_boxes_index):
            parts=line.split("\t")
            boxesDic[parts[1].strip()]=int(parts[0])
        boxesCoverage=True
    
    for line in sys.stdin:
        line=line.rstrip('\n').decode('utf-8')
        parts=line.split('|')
        if len(parts) > 5:
            #wrong sentence
            print ""
        else:
            parallelSentence=ParallelSentence()
            parallelSentence.parse(line, parseTlLemmasFromDic=True)
            parallelSentence.add_explicit_empty_tags()
            finalHypotheses=parallelSentence.compute_coverages_and_bleu(ruleLists,int(args.beam_size),boxesCoverage,boxesDic,args.allow_incompatible_rules)
            print u"|||".join([unicode(h) for h in finalHypotheses]).encode('utf-8')
            
