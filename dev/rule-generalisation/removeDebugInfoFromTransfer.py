#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-

import sys, re;

#DEBUG_LU_REGEXP=r"\^\*executedtule([0-9]+)\$"
#DEBUG_LU_REGEXP_2=r"\^\*wordforword([0-9]+)\$"
#DEBUG_LU_REGEXP_3=r"\^\*isolatedword\$"

DEBUG_LU_REGEXP=r"\^(\*executedtule|\*endexecutedtule|\*wordforword|\*isolatedword|\*endisolatedword)([0-9]*)\$"

START_SOURCE_TOKEN=u"__SL__START__"
END_SOURCE_TOKEN=u"__SL__END__"

MOREDEBUG=False
SILENT=False
global_prevpos=0

#def replacement_function(matchobj):
#	print >> sys.stderr, matchobj.group(1)
#	return ""
#
#def replacement_function_2(matchobj):
#	print >> sys.stderr, "ww"+matchobj.group(1)
#	return ""
#
#def replacement_function_3(matchobj):
#	print >> sys.stderr, "0"
#	return ""

def replacement_function(matchobj):
	global global_prevpos
	
	if matchobj.group(1)==u"*isolatedword":
		if not SILENT:
			print >> sys.stderr, "0"
		if MOREDEBUG:
			if not SILENT:
				print >> sys.stderr, "SINGLETARGET: "+matchobj.string[global_prevpos:matchobj.start()].encode('utf-8')
			global_prevpos=matchobj.end()
			return START_SOURCE_TOKEN
	elif matchobj.group(1)==u"*endisolatedword":
		if MOREDEBUG:
			if not SILENT:
				print >> sys.stderr, "SINGLESOURCE: "+matchobj.string[global_prevpos:matchobj.start()].encode('utf-8')
			global_prevpos=matchobj.end()
			return END_SOURCE_TOKEN
			
	elif matchobj.group(1)==u"*wordforword":
		if not SILENT:
			print >> sys.stderr, "ww"+matchobj.group(2).encode('utf-8')
		global_prevpos=matchobj.end()
	elif matchobj.group(1)==u"*endexecutedtule":
		if MOREDEBUG:
			if not SILENT:
				print >> sys.stderr, "SOURCE: "+matchobj.string[global_prevpos:matchobj.start()].encode('utf-8')
			global_prevpos=matchobj.end()
			return END_SOURCE_TOKEN
	else:
		if not SILENT:
			print >> sys.stderr, matchobj.group(2).encode('utf-8')
		if MOREDEBUG:
			if not SILENT:
				print >> sys.stderr, "TARGET: "+matchobj.string[global_prevpos:matchobj.start()].encode('utf-8')
			global_prevpos=matchobj.end()
			return START_SOURCE_TOKEN
	
	return ""


if len(sys.argv) > 1:
	if sys.argv[1]=="moredebug":
		MOREDEBUG=True

if len(sys.argv) > 2:
	if sys.argv[1]=="silent" or sys.argv[2]=="silent":
		SILENT=True


pattern=re.compile(DEBUG_LU_REGEXP)
#pattern2=re.compile(DEBUG_LU_REGEXP_2)
#pattern3=re.compile(DEBUG_LU_REGEXP_3)
for line in sys.stdin:
	global_prevpos=0
	line=line.decode('utf-8').strip()
	line=re.sub(pattern,replacement_function,line)
	#line=re.sub(pattern2,replacement_function_2,line)
	#line=re.sub(pattern3,replacement_function_3,line)
	if MOREDEBUG:
		newline=list()
		startingPos=0
		posFind=line.find(START_SOURCE_TOKEN,startingPos)
		while posFind>=0:
			posFindEnd=line.find(END_SOURCE_TOKEN,startingPos)
			newline.append(line[startingPos:posFind])
			startingPos=posFindEnd+len(END_SOURCE_TOKEN)
			posFind=line.find(START_SOURCE_TOKEN,startingPos)
		newline.append(line[startingPos:])
		line=u"".join(newline)
	
	print line.encode('utf-8')
