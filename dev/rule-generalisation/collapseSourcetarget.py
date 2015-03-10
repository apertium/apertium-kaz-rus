import sys

origline=sys.stdin.readline()
while origline:
	numRule=int(origline.strip())
	origline=sys.stdin.readline()
	target=origline.strip().decode('utf-8')[7:]
	origline=sys.stdin.readline()
	source=origline.strip().decode('utf-8')[7:]
	print str(numRule)+" | "+source.encode('utf-8')+" | "+target.encode('utf-8')
	origline=sys.stdin.readline()
