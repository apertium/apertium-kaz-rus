'''
Created on 04/12/2013

@author: vitaka
'''
from beamSearchLib import ParallelSentence
import sys


print "digraph aligments{"
prevSubgraph=None
for line in sys.stdin:
    line=line.rstrip('\n').decode('utf-8')
    #parts=line.split(u" | ")
    parallelSentence=ParallelSentence()
    #parallelSentence.parse(u" | ".join(parts[1:]), parseTlLemmasFromDic=False)
    parallelSentence.parse(line, parseTlLemmasFromDic=False)
    parallelSentence.extract_antiphrases()
    
    for antiphrase in parallelSentence.antiphrases:
        print >> sys.stderr, antiphrase
    
    content,subgraphName = parallelSentence.draw_dot()
    print content
    if prevSubgraph!=None:
        print "DUMMY_"+prevSubgraph+" -> DUMMY_"+subgraphName+" [style=invis];"
    prevSubgraph=subgraphName
print "}"