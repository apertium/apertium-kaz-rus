# coding=utf-8
# -*- encoding: utf-8 -*-

import sys,argparse,gzip

parser = argparse.ArgumentParser(description='Spreads bilingual phrases according to their box.')
parser.add_argument('--dir')
parser.add_argument('--dict')
args = parser.parse_args(sys.argv[1:])

dir=args.dir

pack=u""
index=0

idsDict=dict()
b_createDict=True
b_writeBilphrases=False

if args.dict and args.dir:
	b_createDict=False
	b_writeBilphrases=True
	#parse dict
	for line in open(args.dict):
		line=line.strip()
		parts=line.split()
		if len(parts) == 2:
			idsDict[int(parts[0])]=parts[1]
elif args.dict or args.dir:
	print >> sys.stderr, "ERROR: wrong parameters"

fileDesc=None

writtenBoxes=set()

for line in sys.stdin:
	line=line.rstrip('\n').decode('utf-8')
	parts=line.split(u"|")
	packStr=parts[0]
	bilphrase=u"|".join(parts[1:])	
	
	if packStr != pack:
		
		#close prev file 
		if pack != u"":
			if fileDesc != None:
				fileDesc.close()
		
		index+=1
		pack=packStr
		
		if b_createDict:
			idsDict[index]=pack
		
		#create a new file
		if b_writeBilphrases:
			fileDesc=gzip.open(dir+"/newbilphrases/"+str(index)+".bilphrases.gz","wb")
			writtenBoxes.add(index)
	if b_writeBilphrases:
		fileDesc.write(bilphrase.encode('utf-8')+"\n")

if fileDesc != None:
	fileDesc.close()

if b_writeBilphrases:
	nonWrittenBoxes=set(idsDict.keys())-writtenBoxes
	for nwbox in nonWrittenBoxes:
		fileDesc=gzip.open(dir+"/newbilphrases/"+str(nwbox)+".bilphrases.gz","wb")
		fileDesc.close()

#print index
if b_createDict:
	for boxid  in idsDict.keys():
		print str(boxid)+"\t"+idsDict[boxid].encode('utf-8')
