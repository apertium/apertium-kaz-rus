'''
Created on 30/12/2013

@author: vitaka
'''
import sys, ruleLearningLib, argparse
from collections import defaultdict

inputFile=sys.stdin
parser = argparse.ArgumentParser(description='Counts times attributes change.')
parser.add_argument('--tag_groups_file_name',required=True)
parser.add_argument('--tag_sequences_file_name',required=True)
args = parser.parse_args(sys.argv[1:])
ruleLearningLib.AT_LexicalTagsProcessor.initialize(args.tag_groups_file_name,args.tag_sequences_file_name)

numChangesDict=dict()

incorrectLines=0
allLines=0

for linee in inputFile:
    line=linee.decode('utf-8')
    parts=line.split(u'\t')
    
    allLines+=1
    
    try:     
        lexformsl=ruleLearningLib.AT_LexicalForm()
        lexformsl.parse(parts[0])
        
        lexformtl=ruleLearningLib.AT_LexicalForm()
        lexformtl.parse(parts[1])
        
        lexicalCategory=lexformsl.get_pos()
        if not lexicalCategory in numChangesDict:
            numChangesDict[lexicalCategory]=defaultdict(int)
        
        changingAttributes=set()
        tldict=lexformtl.get_tags_with_feature_names_as_dict()
        sldict=lexformsl.get_tags_with_feature_names_as_dict()
        for attr in sldict.keys():
            if not attr in tldict.keys():
                changingAttributes.add(attr)
            elif sldict[attr] != tldict[attr]:
                changingAttributes.add(attr)
        for attr in tldict.keys():
            if not attr in sldict.keys():
                changingAttributes.add(attr)
            elif sldict[attr] != tldict[attr]:
                changingAttributes.add(attr)
        for attr in changingAttributes:
            numChangesDict[lexicalCategory][attr]+=1
    except Exception:
        incorrectLines+=1 

print >> sys.stderr, "Incorrect lines "+str(incorrectLines)+"/"+str(allLines)  

for lexicalCategory in numChangesDict.keys():
    print lexicalCategory.encode('utf-8')+"\t"+unicode(numChangesDict[lexicalCategory]).encode('utf-8')

        