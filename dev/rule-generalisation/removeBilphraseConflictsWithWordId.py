
#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-

import sys

def processBatch(listOfLines):
    if len(listOfLines) > 1:
        #print only the longest right side
        #we can count characters, since all the candidates share the center
        sortedListOfLines=sorted(listOfLines,key=lambda l: len(l[2]),reverse=True)
        print " | ".join(sortedListOfLines[0])
    else:
        print " | ".join(listOfLines[0])
    del listOfLines[:]


if __name__=="__main__": 
    prevLeftSide=None
    curBatch=list()
    for line in sys.stdin:
        parts=line.split(' | ')
        curLeft=" | ".join(parts[:2])
        if curLeft != prevLeftSide and prevLeftSide!=None:
            processBatch(curBatch)
        curBatch.append(parts)
        prevLeftSide=curLeft
    if len(curBatch)>0:
        processBatch(curBatch)


