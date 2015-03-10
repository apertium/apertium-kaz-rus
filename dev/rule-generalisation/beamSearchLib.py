'''

Created on 07/06/2013

@author: vitaka
'''
from pulp import constants
from pulp.constants import LpStatusOptimal, LpMaximize
from pulp.pulp import LpProblem, LpVariable, LpAffineExpression, LpConstraint, \
    value
from ruleLearningLib import AT_LexicalForm, debug
from tempfile import mkstemp, NamedTemporaryFile
import os
import ruleLearningLib
import subprocess
import sys,numpy
from collections import defaultdict

class RuleList(object):
    
    isRestrictionsIncluded=False
    
    @classmethod
    def is_restrictions_included(cls):
        return cls.isRestrictionsIncluded
    @classmethod
    def set_restrictions_included(cls,p_resIncluded):
        cls.isRestrictionsIncluded=p_resIncluded
    
    def __init__(self):
        self.catSequenceDict=dict()
        self.maxLength=0
        self.ruleList=[None]
    
    def add(self,at):
        poslistStr=str(at.get_pos_list(self.__class__.is_restrictions_included()))
        if not poslistStr in self.catSequenceDict:
            self.catSequenceDict[poslistStr]=list()
        at.id=len(self.ruleList)
        self.catSequenceDict[poslistStr].append(at)
        self.maxLength=max(self.maxLength,len(at.parsed_sl_lexforms))
        self.ruleList.append(at)
    
    def get_max_length(self):
        return self.maxLength
    
    def get_by_id(self,id):
        if id <=0 or id >= len(self.ruleList):
            raise RuntimeError("ID not in range")
        return self.ruleList[id]
    
    def add_rules_with_seq_of_cats(self,originalRuleList,seqCatsStr):
        seqCatsIndex=str(seqCatsStr.split(u"__"))
        for at in originalRuleList.catSequenceDict[seqCatsIndex]:
            self.add(at)
    
    #returns the rules matching the segment, sorted in decreasing priority order
    def get_rules_matching_segment(self,segment,restrictions,exactMatch=False):
        rulesMatching=list()
        
        if len(segment) > 0 and not segment[0].is_unknown():
            listOfCats=list()
            for i in range(len(segment)):
                sllex=segment[i]
                restriction=restrictions[i]
                if self.__class__.is_restrictions_included():
                    listOfCats.append((sllex.get_pos(),restriction.get_tags()))
                else:
                    listOfCats.append(sllex.get_pos())
            
            
            if exactMatch:
                prefixes=[len(segment)-1]
            else:
                prefixes=reversed(range(len(segment)))
            
            for i in prefixes:
                prefixCatsStr=str(listOfCats[:i+1])
                prefixSegment=segment[:i+1]
                prefixRestriction=restrictions[:i+1]
                if prefixCatsStr in self.catSequenceDict:
                    for at in self.catSequenceDict[prefixCatsStr]:
                        if at.matches_segment(prefixSegment,prefixRestriction, self.__class__.is_restrictions_included()):
                            rulesMatching.append(at)
        return rulesMatching
    
    
class RuleApplicationHypothesis(object):
    
    totalNumRules=1
    
    maxLength=1
    config_tl="ca"
    apertium_data_dir=None
    minimumCoverdedWords=False
    boxesInvDict=dict()
    
    WORDFORWORDRULEID=-1
    
    def __init__(self,p_lengthOfSentence=1):
        self.appliedRules=set()
        self.discardedRules=set()
        self.source=list()
        self.translation=list()
        self.reference=list()
        self.score=0.0
        self.processedSlWords=0
        self.lengthOfSentence=p_lengthOfSentence
        self.rulesList=list()
    
    def is_empty(self):
        return len(self.appliedRules) == 0 and len(self.discardedRules) == 0
    
    def get_applied_rules(self):
        return self.appliedRules
    
    def get_rules_list(self):
        return self.rulesList
    
    def get_discarded_rules(self):
        return self.discardedRules
    
    def set_translation(self,p_translation):
        self.translation=p_translation
    
    def get_translation(self):
        return self.translation
    
    def set_reference(self,p_reference):
        self.reference=p_reference
    
    def get_reference(self):
        return self.reference
    
    def set_source(self,p_source):
        self.source=p_source
    
    def get_source(self):
        return self.source
    
    def set_score(self,p_score):
        self.score=p_score
    def get_score(self):
        return self.score
    
    def get_score_with_num_rules(self):
        if RuleApplicationHypothesis.minimumCoverdedWords:
            #assuming a maximum of 
            #100 words per sentence,
            #the minimum difference between two rule applications
            #of the proportion of words covered would be:
            # 1/100 = 0.01
            #So we only need 2 digits to represent it. Anyway, we will use 3
            #just in case there is a sentence longer than 100 words
            ruleApps=[ruleApp[1] for ruleApp in self.rulesList if ruleApp[0] != RuleApplicationHypothesis.WORDFORWORDRULEID] 
            mean=0
            if len(ruleApps) > 0:
                mean =numpy.mean( [ len(ruleApp) for ruleApp in ruleApps ] )
            return self.score*10000+ 0.1*(1 - (sum( len(ruleApp) for ruleApp in ruleApps )*1.0/self.lengthOfSentence)) + 0.0001*( 1 - (mean*1.0/RuleApplicationHypothesis.maxLength ))
        else:
            return self.score*10000+ 0.1*(1 - (len(self.discardedRules)*1.0/RuleApplicationHypothesis.totalNumRules))

    def get_processed_sl_words(self):
        return self.processedSlWords
    def set_processed_sl_words(self,p_numpslwords):
        self.processedSlWords=p_numpslwords
    
    def can_be_combined_with(self,otherhyp):
        return len(self.appliedRules & otherhyp.discardedRules) == 0 and len(otherhyp.appliedRules & self.discardedRules)==0 
    
    def get_rules_list(self):
        return self.rulesList
    
    def add_to_rules_list(self,ruleid,posSequence,setOfAtsId=[]):
        self.rulesList.append((ruleid,posSequence,setOfAtsId))
    
    def add_to_applied_rules(self,ruleid,setOfAtsId=[0]):
        self.appliedRules.add(RuleApplicationIdentifier(ruleid,setOfAtsId))
    
    #Concatenate two hypothesis
    def create_new_combined_with(self,otherhyp):
        combined=RuleApplicationHypothesis(self.lengthOfSentence)
        combined.appliedRules=self.appliedRules | otherhyp.appliedRules
        combined.discardedRules=self.discardedRules | otherhyp.discardedRules
        combined.translation=self.translation + otherhyp.translation
        combined.processedSlWords=self.processedSlWords+otherhyp.processedSlWords
        combined.rulesList.extend(self.rulesList)
        combined.rulesList.extend(otherhyp.rulesList)
        return combined
    
    def to_str_for_scoring(self):
        source=u" ".join(slf.unparse(replaceSpacesWithUnderscore=True,removeEmptyTags=True) for slf in self.source)
        test=u" ".join(u"^"+lf.unparse(replaceSpacesWithUnderscore=False,removeEmptyTags=True)+u"$" for lf in self.translation)
        ref=u" ".join(u"^"+lf.unparse(replaceSpacesWithUnderscore=False,removeEmptyTags=True)+u"$" for lf in self.reference)
        return u"|".join([source,test,ref]).encode('utf-8')
        
    def __repr__(self):
        return unicode(self.score)+u" | "+unicode(self.appliedRules)+u" | "+unicode(self.discardedRules)+u" | "+unicode(self.rulesList)+u" | "+u"\t".join([ lf.unparse() for lf in self.translation])
    
    def to_str_for_debug(self):
        return unicode(self.score)+u" | "+unicode(self.appliedRules)+u" | "+unicode(self.discardedRules)+u" | "+unicode(self.rulesList)+u" | "+ u" ".join([ lf.unparse() for lf in self.source]) +" | " + u" ".join([ lf.unparse() for lf in self.translation])+" |ref: "+u" ".join([ lf.unparse() for lf in self.reference])
    def parse(self,rawstr,parseTranslation=False):
        parts=rawstr.split(u"|")
        if len(parts) >=4:
            self.score=float(parts[0].strip())
            setOfTuplesAppliedRules=eval(parts[1].strip())
            self.appliedRules=set()
            for tup in setOfTuplesAppliedRules:
                identifier=RuleApplicationIdentifier()
                identifier.create_from_tuple(tup)
                self.appliedRules.add(identifier)
            
            self.discardedRules=eval(parts[2].strip())
            self.rulesList=eval(parts[3].strip())
            if parseTranslation and len(parts) >= 5:
                lexicalFormsStr=parts[4].strip().split(u"\t")
                for lxStr in lexicalFormsStr:
                    lf =ruleLearningLib.AT_LexicalForm()
                    lf.parse(lxStr)
                    self.translation.append(lf)
                
        else:
            raise Exception()
    
    @classmethod
    def create_and_parse(cls,rawstr,parseTranslation=False):
        hyp=RuleApplicationHypothesis()
        hyp.parse(rawstr,parseTranslation)
        return hyp

    @classmethod
    def set_target_language(cls,p_tl):
        cls.config_tl=p_tl
    
    @classmethod
    def set_num_total_rules(cls,p_totalNumRules):
        cls.totalNumRules=p_totalNumRules
    
    @classmethod
    def set_apertium_data_dir(cls,p_datadir):
        if p_datadir != "":
            cls.apertium_data_dir=p_datadir
    
    @classmethod
    def set_minimum_covered_words(cls,p_isminimum):
        cls.minimumCoverdedWords=p_isminimum
    
    @classmethod
    def set_max_length(cls,p_maxLength):
        cls.maxLength=p_maxLength
    
    @classmethod
    def set_inv_boxes_dict(cls,p_boxesdict):
        cls.boxesInvDict=p_boxesdict
    
    @classmethod
    def score_hypotheses(cls,hypothesisList,sentenceLevelScores=True):
        #create tmp file
        fileobj=NamedTemporaryFile(delete=False)
        
        if sentenceLevelScores:
            listOfstrHyps=list(set([hyp.to_str_for_scoring() for hyp in hypothesisList]))
        else:
            listOfstrHyps=[hyp.to_str_for_scoring() for hyp in hypothesisList]
        
        debug("\nScoring hypotheses")
        
        for strhyp in listOfstrHyps:
            fileobj.write(strhyp+"\n")
        fileobj.close()
        
        corpusLevelScoreFlag=""
        if sentenceLevelScores == False:
            corpusLevelScoreFlag="-c"
        command="bash "+os.getcwdu()+"/evaluateBeamSearchHypothesis.sh -f "+fileobj.name+" -t "+cls.config_tl+" "+corpusLevelScoreFlag
        if cls.apertium_data_dir:
            command+=" -d "
            command+=cls.apertium_data_dir

        output,error = subprocess.Popen(command,stdout= subprocess.PIPE ,stderr= subprocess.PIPE, shell=True).communicate()
        
        os.remove(fileobj.name)
        
        lines=output.strip().split("\n")
        
        if ruleLearningLib.DEBUG:
            debug("BLEU debug info:")
            debug(error)
        
        if sentenceLevelScores:  
            if len(lines) != len(listOfstrHyps):
                print >> sys.stderr, "ERROR. NUmber of lines ("+str(len(lines))+") does not match hypothesis list ("+str(len(listOfstrHyps))+")"
                print >> sys.stderr, "Dump:"
                print >> sys.stderr, output
                print >> sys.stderr, "Error output:"
                print >> sys.stderr, error
                exit()
            
            resultsDictionary=dict()
            for i in range(len(lines)):
                if len(lines[i]) == 0:
                    print >> sys.stderr, "Line with length 0"
                    print >> sys.stderr, "command output"
                    print >> sys.stderr, error
                    exit()
                resultsDictionary[listOfstrHyps[i]]=float(lines[i])
                debug(str(float(lines[i]))+" | "+listOfstrHyps[i])
            
            for hyp in hypothesisList:
                hyp.set_score(resultsDictionary[hyp.to_str_for_scoring()])
        else:
            if len(lines) != 1:
                print >> sys.stderr, "ERROR. NUmber of lines ("+str(len(lines))+") does not match hypothesis list ("+str(len(listOfstrHyps))+")"
                print >> sys.stderr, "Dump:"
                print >> sys.stderr, output
                print >> sys.stderr, "Error output:"
                print >> sys.stderr, error
                exit()
            return float(lines[0])
    
    @classmethod
    def select_boxes_from_alternative_at_sets(cls,l_best_hypothesis):
        
        ##########################################
        ## boxid -> countsForBoxMap             ##
        ##                                      ##
        ## countsForBoxMap: altAtSetId -> count ##
        ##                                      ##
        countsMap=dict()
        
        for hyp in l_best_hypothesis:
            for ruleAppIdObj in hyp.get_applied_rules():
                boxid=ruleAppIdObj.get_box_id()
                altAtSetsUsed=ruleAppIdObj.get_alt_at_sets()
                if not boxid in countsMap:
                    countsMap[boxid]=defaultdict(int)
                for altAtSetId in altAtSetsUsed:
                    countsMap[boxid][altAtSetId]+=1
        
        result=list()
        for boxid in countsMap.keys():
            countsForBoxid=countsMap[boxid]
            debug("box "+str(boxid)+": "+str(countsForBoxid))
            sortedItems=sorted(countsForBoxid.items(),key=lambda item: item[1],reverse=True)
            bestItem=sortedItems[0]
            itemsWithMaxCount=[item for item in sortedItems if item[1]==bestItem[1]]
            #from the items with max count, select the lower 
            #altAtSetId
            winner=sorted(itemsWithMaxCount,key=lambda item: item[0])[0]
            result.append((boxid,winner[0]))
        
        return result
    
    @classmethod
    def select_rules_maximize_score(cls,ll_hypothesis):
        #Create linear programming problem
        prob = LpProblem("maxbleu", LpMaximize)
        
        numSentences=len(ll_hypothesis)
        maxExecutedRules=max( max(len(hyp.get_applied_rules()) for hyp in hypothesesOfSentence ) for hypothesesOfSentence in ll_hypothesis)
        
        debug("Max executed rules per hypothesis: "+str(maxExecutedRules))
        
        varList=list()
        hypList=list()
        inverseVarDict=dict()
        numSentenceDict=dict()
        
        #one variable per rule set
        for numSentence,hypothesesOfSentence in enumerate(ll_hypothesis):
            for hyp in hypothesesOfSentence:
                hyp.id=len(varList)
                var=LpVariable("x"+str(hyp.id), 0, 1,cat='Integer')
                varList.append(var)
                hypList.append(hyp)
                inverseVarDict[hyp]=var
                numSentenceDict[hyp.id]=numSentence
        
        #expression to maximise: sum of chosen rule sets
        myexpression=LpAffineExpression( [ (varList[i],hypList[i].get_score()*10000 + (1.0*maxExecutedRules-len(hypList[i].get_applied_rules()))/(numSentences*maxExecutedRules+1)  )   for i in range(len(varList) )  ] )
        prob.objective=myexpression
        
        #restriction: at most one rule set per sentence   
        for i,hypothesesOfSentence in enumerate(ll_hypothesis):
            cname="atmost"+str(i)
            myexpression=LpAffineExpression( [ (varList[hyp.id],1) for hyp in hypothesesOfSentence ] )
            constraint = LpConstraint(myexpression,sense=constants.LpConstraintLE,name=cname,rhs=1) 
            prob.constraints[cname]=constraint
        
        #restriction: compatible rules
        for i,hyp in enumerate(hypList):
            incompHyps=[ ihyp for ihyp in hypList if hyp != ihyp and numSentenceDict[hyp.id] != numSentenceDict[ihyp.id] and len(hyp.appliedRules & ihyp.discardedRules) > 0 ]
            cname="incompatible"+str(i)
            myexpression=LpAffineExpression( [ (varList[ihyp.id],1) for ihyp in incompHyps ] + [(varList[hyp.id],len(incompHyps))] )
            constraint = LpConstraint(myexpression,sense=constants.LpConstraintLE,name=cname,rhs=len(incompHyps)) 
            prob.constraints[cname]=constraint
        
        #solve
        status = prob.solve()
        
        solution=list()
        valueOfSolution=0.0
        if status == LpStatusOptimal :
            for i in range(len(hypList)):
                if value(varList[i])==1:
                    solution.append(hypList[i])
                    valueOfSolution+=hypList[i].get_score()*10000 + (1.0*maxExecutedRules-len(hypList[i].get_applied_rules()))/(numSentences*maxExecutedRules+1)
            
            print >> sys.stderr, "Chosen rule applications" 
            for hypsol in solution:
                print >> sys.stderr, "Sentence "+str(numSentenceDict[hypsol.id])+": "+unicode(hypsol).encode('utf-8') 
            return status,solution,valueOfSolution
        else:
            return status,None
    
    @classmethod
    def select_rules_maximize_score_boxes_applied(cls,ll_hypothesis,boxesInvDict,allruleList,sentences,supersegmentsWithMaxScore,outputProbBreakingKey):
        
        oldDebugvalue=ruleLearningLib.DEBUG
        ruleLearningLib.DEBUG=True
        
        probMap=dict()
        
        if len(ll_hypothesis) != len(sentences):
            print >> sys.stderr, "ERROR: different length of sentences and hypothesis"
            return []
        
        usePrecomputedSupersegments=False
        if len(supersegmentsWithMaxScore) > 0:
            usePrecomputedSupersegments=True
            if len(ll_hypothesis) != len(supersegmentsWithMaxScore):
                print >> sys.stderr, "ERROR: different length of supersegments and hypothesis"
                return []
        
        if allruleList.get_max_length() > 1:
            MAX_LENGTH=allruleList.get_max_length()
        else:
            #if the alignment template parameter was not provided
            MAX_LENGTH=5
            
        boxesDict=dict()
        for key in boxesInvDict:
            boxesDict[boxesInvDict[key]]=key
        
        countsApplied=defaultdict(int)
        countsBanned=defaultdict(int)
        rulesMinimumAtLeastOneTime=set()
        
        for numSentence,hypothesesOfSentence in enumerate(ll_hypothesis):
            if len(hypothesesOfSentence) == 0:
                continue
            bestHyp=hypothesesOfSentence[0]
            currentSentence=sentences[numSentence]
            #for ruleid in bestHyp.get_applied_rules():
            #    countsApplied[ruleid]+=1
            ruleList=bestHyp.rulesList
            
            optimalRuleApplicationsSet=set()
            if usePrecomputedSupersegments:
                hypsWithSupersegments=supersegmentsWithMaxScore[numSentence]
            else:
                hypsWithSupersegments=hypothesesOfSentence[1:]
            
            for otherHyp in hypsWithSupersegments:
                currentPosition=0
                for ruleApp in otherHyp.rulesList:
                    if ruleApp[0] != RuleApplicationHypothesis.WORDFORWORDRULEID:
                        optimalRuleApplicationsSet.add((currentPosition,len(ruleApp[1]),ruleApp[0]))
                    currentPosition+=len(ruleApp[1])
            
            #build list of lexical categories
            bannedStartPositions=set()
            bannedEndPositions=set()
            listOfPos=list()
            positionsWhereRuleStartAndLength=list()
            currentPosition=0
            for ruleApp in ruleList:
                listOfPos.extend(ruleApp[1])
                if ruleApp[0] != RuleApplicationHypothesis.WORDFORWORDRULEID:
                    countsApplied[ruleApp[0]]+=1
                    rulesMinimumAtLeastOneTime.add(ruleApp[0])
                    positionsWhereRuleStartAndLength.append((currentPosition,len(ruleApp[1])))
                    
                    #Not explained in the paper = not implemented
                    #for l in range(len(ruleApp[1])-1):
                    #    bannedEndPositions.add(currentPosition+l)
                    #    bannedStartPositions.add(currentPosition+l+1)
                    
                currentPosition+=len(ruleApp[1])
            
            debug("List of lexical categories of sentence "+str(numSentence+1)+": "+" ".join(listOfPos))
            debug("positionsWhereRuleStartAndLength: "+str(positionsWhereRuleStartAndLength))
            
            debug("Supersets added:")
            #increase also frequency of supersegments of minimum set
            for pos,length,ruleid in optimalRuleApplicationsSet:
                if length > 1 and pos not in bannedStartPositions and pos+length-1 not in bannedEndPositions:
                    #it must be a superset of an existing sequence
                    isSuperset=False
                    for minStartPosition,minLength in positionsWhereRuleStartAndLength:
                        if pos<=minStartPosition and pos+length >= minStartPosition+minLength:
                            isSuperset=True
                    if isSuperset:
                        countsApplied[ruleid]+=1
                        debug("\t" +str(pos)+": "+"__".join(listOfPos[pos:pos+length]))
            
            #for each applied rule, compute 
            #rules left-intersecting with it 
            #rulesLeftIntersecting=set()
            
            for startPosition,length in positionsWhereRuleStartAndLength:
                debug("Discarded rules for ("+str(startPosition)+") "+"__".join(listOfPos[startPosition:startPosition+length]))
                for endingPositionOffset in range(length-1):
                    endingPositionIncluded=startPosition+endingPositionOffset
                    for lengthOfLeftIntersectinRule in range(2,MAX_LENGTH+1):
                        startingPositinoOfIntersecting=endingPositionIncluded-lengthOfLeftIntersectinRule +1
                        if startingPositinoOfIntersecting >= 0 and startingPositinoOfIntersecting < startPosition:
                            seqOfPosOfIntersecting=listOfPos[startingPositinoOfIntersecting:endingPositionIncluded+1]
                            
                            #check whether the intersecting segment matches any AT
                            ruleMatchingList=allruleList.get_rules_matching_segment(currentSentence.parsed_sl_lexforms[startingPositinoOfIntersecting:endingPositionIncluded+1],currentSentence.parsed_restrictions[startingPositinoOfIntersecting:endingPositionIncluded+1])
                            
                            if len(ruleMatchingList) > 0:
                                strForm="__".join(seqOfPosOfIntersecting)
                                debug("\t"+strForm)
                                if strForm in boxesDict:
                                    ruleid=boxesDict[strForm]
                                    #rulesLeftIntersecting.add(ruleid)
                                    countsBanned[ruleid]+=1

                #discard also longer rules starting in the same position
                #not belonging to K_BLEU
                for otherRuleLength in range(length+1,MAX_LENGTH+1):
                    seqOfPosOfIntersecting=listOfPos[startPosition:startPosition+otherRuleLength+1]
                    strForm="__".join(seqOfPosOfIntersecting)
                    if strForm in boxesDict:
                        ruleid=boxesDict[strForm]
                        if not (startPosition,otherRuleLength,ruleid) in optimalRuleApplicationsSet:
                            ruleMatchingList=allruleList.get_rules_matching_segment(currentSentence.parsed_sl_lexforms[startPosition:startPosition+otherRuleLength+1],currentSentence.parsed_restrictions[startPosition:startPosition+otherRuleLength+1])
                            if len(ruleMatchingList) > 0:
                                debug("\t"+strForm)
                                countsBanned[ruleid]+=1
                                
                #discard also rules starting before and ending in the same position
                #or after, not belonging to K_BLEU
                for startingPositionOffset in range(1,MAX_LENGTH-length+1):
                    startOfRuleEvaluated=startPosition-startingPositionOffset
                    for endingPosition in range(startPosition+length+1,startPosition-startingPositionOffset+MAX_LENGTH+1):
                        seqOfPosOfIntersecting=listOfPos[startOfRuleEvaluated:endingPosition]
                        if len(seqOfPosOfIntersecting) > MAX_LENGTH:
                            print >> sys.stderr, "ERROR: seq of categories too long. Error in algorithm"
                            exit()
                        if strForm in boxesDict:
                            ruleid=boxesDict[strForm]
                            if not (startOfRuleEvaluated,len(seqOfPosOfIntersecting),ruleid) in optimalRuleApplicationsSet:
                                ruleMatchingList=allruleList.get_rules_matching_segment(currentSentence.parsed_sl_lexforms[startOfRuleEvaluated:endingPosition],currentSentence.parsed_restrictions[startOfRuleEvaluated:endingPosition])
                                if len(ruleMatchingList) > 0:
                                    debug("\t"+strForm)
                                    countsBanned[ruleid]+=1
                        
            #for ruleid in rulesLeftIntersecting:
                #countsBanned[ruleid]+=1
                    
        if ruleLearningLib.DEBUG:
            debug("Frequencies of applied pos sequences:")
            for key in countsApplied.keys():
                posSeq=""
                if key in boxesInvDict:
                    posSeq=boxesInvDict[key]
                isMininimumStr=""
                if key in rulesMinimumAtLeastOneTime:
                    isMininimumStr="m "
                debug(isMininimumStr+"id="+str(key)+" "+posSeq+" : "+str(countsApplied[key])+" - "+str(countsBanned[key])+" = "+str(countsApplied[key]-countsBanned[key]))
        
        ruleLearningLib.DEBUG=oldDebugvalue
        
        if outputProbBreakingKey:
            return [ (key, countsBanned[key]*1.0/(countsApplied[key]+countsBanned[key])) for key in rulesMinimumAtLeastOneTime]
        else:
            return [ key for key in countsApplied.keys() if countsApplied[key] > countsBanned[key] and key in rulesMinimumAtLeastOneTime ]
        
    @classmethod
    def select_rules_maximize_score_with_super_heuristic(cls,ll_hypothesis):
        #hypothesis are already sorted by score and num. of discarded rules
        
        #create set of frozensets of rules to be removed to obtain the maximum score
        countsApplied=defaultdict(int)
        countsDiscarded=defaultdict(int)
        totalRules=set()
        setsOfRulesToDiscard=set()
        for hypothesesOfSentence in ll_hypothesis:
            for hyp in hypothesesOfSentence:
                totalRules.update(set(hyp.get_applied_rules()))
            bestHyp=hypothesesOfSentence[0]
            for ruleid in bestHyp.get_applied_rules():
                countsApplied[ruleid]+=1
            for ruleid in bestHyp.get_discarded_rules():
                countsDiscarded[ruleid]+=1
        
        finalDiscardedRules=set()
        for discardedRule in countsDiscarded.keys():
            if countsDiscarded[discardedRule] > countsApplied[discardedRule]:
                finalDiscardedRules.add(discardedRule) 
        
        debug("Final discarded rules: "+str(finalDiscardedRules))
        
        return totalRules - finalDiscardedRules
        
    @classmethod
    def select_rules_maximize_score_with_beam_search(cls,ll_hypothesis,beamSize=10000, isDiff=True):
        
        totalRules=set()
        for hypothesesOfSentence in ll_hypothesis:
            for hyp in hypothesesOfSentence:
                totalRules.update(set(hyp.get_discarded_rules()))

        #numSentences=len(ll_hypothesis)
        #PartitionSelectionHypothesis.set_parameters_for_minimised_num_rules(numSentences, maxExecutedRules)
        RuleApplicationHypothesis.set_num_total_rules(len(totalRules))
        
        
        #debug("Max executed rules per hypothesis: "+str(maxExecutedRules))
        debug("Total rules: "+str(len(totalRules)))
        
        hypothesisList=set()
        hypothesisList.add(PartitionSelectionHypothesis())
        
        for i in range(len(ll_hypothesis)):         
            ##### DEBUG ####
            debug("")
            debug("Starting beam search step "+str(i)) 
            debug(str(len(hypothesisList))+" hypothesis from previous steps before pruning")
            ##### DEBUG ####
            
            #prune hypothesis
            sortedHypothesisList=sorted(list(hypothesisList),key=lambda h: h.get_total_score() ,reverse=True)
            
            if isDiff:
                #find index whose difference exceeds threshold
                firstOutIndex=len(sortedHypothesisList)
                bestScore=sortedHypothesisList[0].get_total_score()
                
                #only perform search if necessary
                if  bestScore - sortedHypothesisList[-1].get_total_score() > beamSize:
                    index=1
                    while index < len(sortedHypothesisList):
                        if bestScore - sortedHypothesisList[index].get_total_score() > beamSize:
                            firstOutIndex=index
                            break
                        else:
                            index+=1  
                hypothesisList=sortedHypothesisList[:firstOutIndex]
            else:
                hypothesisList=sortedHypothesisList[:beamSize]
            
            ##### DEBUG ####
            debug(str(len(hypothesisList))+" hypothesis from previous steps after pruning")
            debug("Showing some of them:")
            if ruleLearningLib.DEBUG:
                for hyp in hypothesisList[:10]:
                    debug("\t"+unicode(hyp.get_total_score())+": "+unicode(hyp.get_total_applied_rules())+" | "+unicode(hyp.get_total_discarded_rules()))
            ##### DEBUG ####    
            
            ruleApplicationHypothesesInThisStep=ll_hypothesis[i]+[RuleApplicationHypothesis()]
            
            newMembers=set()
            for hyp in hypothesisList:
                for raph in ruleApplicationHypothesesInThisStep:
                    if raph.is_empty() or hyp.can_be_combined_with(raph):
                        newMembers.add(hyp.create_new_combined_with(raph))
            
            hypothesisList=newMembers
        
        winner=sorted(list(hypothesisList),key=lambda h: h.get_total_score() ,reverse=True)[0]
        
        print >> sys.stderr, "Chosen rule applications" 
        for numSentence,rahyp in enumerate(winner.ruleAppliccationHyps):
            print >> sys.stderr, "Sentence "+str(numSentence)+": "+unicode(rahyp).encode('utf-8')
        return winner.get_total_applied_rules(),winner.get_total_score()
    
    @classmethod
    def create_by_translating_segments(cls,ruleList,parsed_sl_lexforms,parsed_restrictions,listOfChunks,parsed_tl_lexforms,tllemmas_from_dictionary,boxesDic):
        
        newHyp=RuleApplicationHypothesis()
        foundEmptyMatchingRule=False
        
        #sort chunks by starting position
        sortedChunks= sorted(listOfChunks,key= lambda c: c[0])
        
        #obtain target lexical forms
        target_lexforms=list()
        nextChunk=sortedChunks[0]
        sortedChunks=sortedChunks[1:]
        index=0
        while index < len(parsed_sl_lexforms):
            debug("Index: "+str(index))
            debug("next chunk"+str(nextChunk))
            debug("list of chunks"+str(sortedChunks))
            if nextChunk != None:
                if index==nextChunk[0]:
                    length=nextChunk[1]
                    
                    #go to next chunk
                    if len(sortedChunks) > 0:
                        nextChunk=sortedChunks[0]
                        sortedChunks=sortedChunks[1:]
                    else:
                        nextChunk=None
                    
                    while nextChunk!=None and nextChunk[0]==index:
                        if nextChunk[1] > length:
                            length=nextChunk[1]    
                        #go to next chunk
                        if len(sortedChunks) > 0:
                            nextChunk=sortedChunks[0]
                            sortedChunks=sortedChunks[1:]
                        else:
                            nextChunk=None
                        
                    
                    matchingRules=ruleList.get_rules_matching_segment(parsed_sl_lexforms[index:index+length],parsed_restrictions[index:index+length],exactMatch=True)
                    if len(matchingRules) == 0:
                        foundEmptyMatchingRule=True
                        break
                    at=matchingRules[0]
                    tlsegment=at.apply(parsed_sl_lexforms[index:index+length],tllemmas_from_dictionary[index:index+length],parsed_restrictions[index:index+length])
                    target_lexforms.extend(tlsegment)
                    
                    boxid=boxesDic[at.get_pos_list_str()]
                    newHyp.add_to_applied_rules(boxid)
                    newHyp.add_to_rules_list(boxid, at.get_pos_list_str().split("__"))
                    
                    index+=length
                    continue
            
            #translate word for word
            if parsed_sl_lexforms[index].is_unknown():
                bilDicTranslation=parsed_sl_lexforms[index]
            else:
                bilDicTranslation=AT_LexicalForm()
                bilDicTranslation.set_lemma(tllemmas_from_dictionary[index])
                bilDicTranslation.set_pos(parsed_sl_lexforms[index].get_pos())
                bilDicTags=list()
                bilDicTags.extend(parsed_restrictions[index].get_tags())
                bilDicTags.extend(parsed_sl_lexforms[index].get_tags()[len(bilDicTags):])
                bilDicTranslation.set_tags(bilDicTags)
            target_lexforms.append(bilDicTranslation)
            newHyp.add_to_rules_list(RuleApplicationHypothesis.WORDFORWORDRULEID, [ parsed_sl_lexforms[index].get_pos() ])
            index+=1
        
        if not foundEmptyMatchingRule:
            newHyp.set_source(parsed_sl_lexforms)
            newHyp.set_translation(target_lexforms)
            newHyp.set_reference(parsed_tl_lexforms)
        else:
            newHyp.appliedRules=set()
        return newHyp
    
    def compute_supersets_with_maximum_score(self,sentence,ruleList,boxesDic):
        
        maxLength=ruleList.get_max_length()
        
        newRuleApplicationHypotheses=list()
        
        if ruleLearningLib.DEBUG:
            debug("Computing supersets for hypothesis: "+unicode(self).encode('utf-8'))
        
        #obtain more information about key segments
        keysegments=list()
        currentPosition=0
        for ruleApp in self.rulesList:
            if ruleApp[0] != RuleApplicationHypothesis.WORDFORWORDRULEID:
                #keysegment= ( position, length, ruleid )
                keysegments.append((currentPosition,len(ruleApp[1]),ruleApp[0]))
            currentPosition+=len(ruleApp[1])
        
        #compute supersets of each key segment
        #each position of the list: list of supersets which keep the maximum score
        
        #first, compute all supersets
        allSuperSetsOfKeySegments=list()
        for ksPos,ksLen,ksId in keysegments:
            supersetsOfThisKey=list()
            maxLengthToAdd=maxLength-ksLen
            for lengthToAdd in range(1,maxLengthToAdd+1):
                for leftSideLength in range(lengthToAdd+1):
                    #rightSideLengh=lengthToAdd-leftSideLength
                    startingPos=ksPos-leftSideLength
                    if startingPos >= 0 and  startingPos+ksLen+lengthToAdd <= len(sentence.parsed_sl_lexforms):
                        supersetsOfThisKey.append((startingPos,ksLen+lengthToAdd))
            allSuperSetsOfKeySegments.append(supersetsOfThisKey)       
        
        #remove supersets intersecting with other key segments.
        #no problem if they totally enclose other key segments
        notIntersectingSuperSetsOfKeySegments=list()
        for keySegmentIndex,allSupersets in enumerate(allSuperSetsOfKeySegments):
            notIntersectingOfThisKey=list()
            for startingPos,length in allSupersets:
                valid=True
                for otherKeySegmentIndex,keySegmentData in enumerate(keysegments):
                    if otherKeySegmentIndex != keySegmentIndex:
                        ksPos=keySegmentData[0]
                        ksLen=keySegmentData[1]
                        if ksPos < startingPos and startingPos < ksPos+ksLen :
                            valid=False
                            break
                        if ksPos < startingPos+length and ksPos +ksLen > startingPos+length:
                            valid=False
                            break
                if valid:
                    notIntersectingOfThisKey.append((startingPos,length))
            notIntersectingSuperSetsOfKeySegments.append(notIntersectingOfThisKey)
        
        if ruleLearningLib.DEBUG:
            debug("Supersets not intersecting: ")
            for keyindex,supersets in enumerate(notIntersectingSuperSetsOfKeySegments):
                debug("For ks "+str(keyindex)+": "+str(supersets))
            
        
        #check whether, when translating the SL sentence with a supersegment
        #and the remaining key segments, the same score is obtained
        for keySegmentIndex,allSupersets in enumerate(notIntersectingSuperSetsOfKeySegments):
            otherKeySegments=list()
            for otherKeySegmentIndex,keySegment in enumerate(keysegments):
                if otherKeySegmentIndex != keySegmentIndex:
                    otherKeySegments.append((keySegment[0],keySegment[1]))
                                            
            for keySegmentSuperset in allSupersets:
                listOfChunks=list()
                listOfChunks.append(keySegmentSuperset)
                listOfChunks.extend(otherKeySegments)
                
                debug("Creating hypothesis with these segments: "+str(listOfChunks))
                
                ruleAppWithSuperset=RuleApplicationHypothesis.create_by_translating_segments(ruleList,sentence.parsed_sl_lexforms,sentence.parsed_restrictions,listOfChunks,sentence.parsed_tl_lexforms,sentence.tl_lemmas_from_dictionary,boxesDic)
                if not ruleAppWithSuperset.is_empty():
                    debug(unicode(ruleAppWithSuperset).encode('utf-8'))
                    newRuleApplicationHypotheses.append(ruleAppWithSuperset)
                else:
                    debug("RULES NOT MATCHING")
        
        #it is not necessary to combine the different supersegments for 
        #each key segment. see how this result is used by the maximiseScore.py program
        
        if ruleLearningLib.DEBUG and False:
            debug("Rule application hypotheses to be scored:")
            for index,hyp in enumerate(newRuleApplicationHypotheses):
                debug("hyp "+str(index)+": "+unicode(hyp).encode('utf-8'))
            debug("")
        RuleApplicationHypothesis.score_hypotheses([self]+newRuleApplicationHypotheses)
        
        return [hyp for hyp in newRuleApplicationHypotheses if hyp.get_score() >= self.get_score()]

class PartitionSelectionHypothesis(object):
    
    numSentences=1
    maxExecutedRules=1
    
    def __init__(self):
        self.ruleAppliccationHyps=list()
        self.totalScore=0.0
        self.totalScoreWithoutNum=0.0
        self.totalAppliedRules=frozenset()
        self.totalDiscardedRules=frozenset()
    
    def can_be_combined_with(self,ruleApplicationHypothesis):
        return len(self.totalAppliedRules & ruleApplicationHypothesis.get_discarded_rules()) == 0 and len(self.totalDiscardedRules & ruleApplicationHypothesis.get_applied_rules()) == 0
    
    def create_new_combined_with(self,ruleApplicationHypothesis):
        partitionSelectionHypothesis= PartitionSelectionHypothesis()
        partitionSelectionHypothesis.ruleAppliccationHyps = self.ruleAppliccationHyps +  [ruleApplicationHypothesis]
        partitionSelectionHypothesis.totalScoreWithoutNum= self.totalScoreWithoutNum +ruleApplicationHypothesis.get_score()
        #partitionSelectionHypothesis.totalScore = self.totalScore+ (ruleApplicationHypothesis.get_score()*10000 + (1.0*PartitionSelectionHypothesis.maxExecutedRules-len(ruleApplicationHypothesis.get_applied_rules()))/(PartitionSelectionHypothesis.numSentences*PartitionSelectionHypothesis.maxExecutedRules+1))
        partitionSelectionHypothesis.totalAppliedRules = frozenset(self.totalAppliedRules | ruleApplicationHypothesis.get_applied_rules())
        partitionSelectionHypothesis.totalDiscardedRules = frozenset(self.totalDiscardedRules | ruleApplicationHypothesis.get_discarded_rules())
        partitionSelectionHypothesis.compute_score_with_num_rules()
        return partitionSelectionHypothesis
    
    def compute_score_with_num_rules(self):
        self.totalScore=self.totalScoreWithoutNum+  0.1*(RuleApplicationHypothesis.totalNumRules-len(self.totalDiscardedRules))/RuleApplicationHypothesis.totalNumRules
    
    def get_total_score(self):
        return self.totalScore
    
    def get_total_applied_rules(self):
        return self.totalAppliedRules
    
    def get_total_discarded_rules(self):
        return self.totalDiscardedRules
    
    @classmethod
    def set_parameters_for_minimised_num_rules(cls,p_numSentences,p_maxExecutedRules):
        cls.numSentences=p_numSentences
        cls.maxExecutedRules=p_maxExecutedRules
    
    def __hash__(self):
        return hash((self.totalAppliedRules,self.totalDiscardedRules,len(self.ruleAppliccationHyps)))
        #return hash(self.__repr__())
    
    def __cmp__(self,obj):
        return cmp(self.__hash__(),obj.__hash__())

class RuleApplicationIdentifier():
    def __init__(self,p_boxId=-10,p_listOfAtSets=[]):
        tupleSets=tuple(sorted(p_listOfAtSets))
        self.create_from_tuple((p_boxId,tupleSets))
    
    def create_from_tuple(self,tuple):
        self.boxId=tuple[0]
        self.atSets=set()
        for atSet in tuple[1]:
            self.atSets.add(atSet)
        self.hashValue=tuple
    
    def get_box_id(self):
        return self.boxId
    
    def get_alt_at_sets(self):
        return self.atSets

    def __hash__(self):
        return hash(self.hashValue)
    
    def __cmp__(self,obj):
        return cmp(self.hashValue,obj.hashValue)
    
    def __repr__(self):
        return unicode(self.hashValue)


class ParallelSentence(ruleLearningLib.AlignmentTemplate):
    
    def count_all_bsls(self,bslSet,maxLen=sys.maxint):
        for bilphrase in self.extract_all_biphrases(maxLen):
            bslSet.add_from_bilphrase(bilphrase)
    
    def count_bsls(self,bslNumerator,bslDenominator,allowUnknownAndPunctSide):
        
        countNumerator=0
        countDenominator=0
        
        offsetLeftForCheckingPunct=0
        offsetRightForCheckingPunct=0
        if allowUnknownAndPunctSide==ParallelSentence.SIDE_LEFT:
            offsetLeftForCheckingPunct+=1
        elif allowUnknownAndPunctSide==ParallelSentence.SIDE_RIGHT:
            offsetRightForCheckingPunct+=1
        
        bslOfSentence=ruleLearningLib.BilingualSequenceLexTags()
        bslOfSentence.load_from_at(self)
        
        for i in xrange(len(self.parsed_sl_lexforms)-len(bslDenominator.slseq)+1):
            #check that SL sequence does not contain punctuation or 
            if not any( lex.is_unk_or_punct() for lex in self.parsed_sl_lexforms[i+offsetLeftForCheckingPunct:i+len(bslDenominator.slseq)-offsetRightForCheckingPunct] ):
                #check whether sequence of SL classes matches
                matches=True
                for off in xrange(len(bslDenominator.slseq)):
                     if bslDenominator.slseq[off] != u"*":
                         if bslDenominator.slseq[off] != bslOfSentence.slseq[i+off]:
                             matches=False
                             break
                if matches:
                    #select TL sequences compatible with the alignments
                    for j in xrange(len(self.parsed_tl_lexforms)-len(bslDenominator.tlseq)+1):
                        if self.is_bilphrase_compatible_with_alignments(i, len(bslDenominator.slseq), j, len(bslDenominator.tlseq)):
                            #check not punctuation or unknown
                            if not any( lex.is_unk_or_punct() for lex in self.parsed_tl_lexforms[j+offsetLeftForCheckingPunct:j+len(bslDenominator.tlseq)-offsetRightForCheckingPunct] ):
                                #if the TL sequence is compatible with the alignments and punct, check if it matches bsl
                                matches=True
                                for off in xrange(len(bslDenominator.tlseq)):
                                    if bslDenominator.tlseq[off] != u"*":
                                         if bslDenominator.tlseq[off] != bslOfSentence.tlseq[j+off]:
                                             matches=False
                                             break
                                if matches:
                                    #increase count of denominator 
                                    countDenominator+=1
                                    
                                    #check whether numerator matches
                                    matchesSL=True
                                    for off in xrange(len(bslDenominator.slseq)):
                                        if bslNumerator.slseq[off] != u"*":
                                            if bslNumerator.slseq[off] != bslOfSentence.slseq[i+off]:
                                                matchesSL=False
                                                break
                                    matchesTL=True
                                    for off in xrange(len(bslDenominator.tlseq)):
                                        if bslNumerator.tlseq[off] != u"*":
                                            if bslNumerator.tlseq[off] != bslOfSentence.tlseq[j+off]:
                                                matchesTL=False
                                                break
                                    if matchesSL and matchesTL:
                                        countNumerator+=1
                        
        return countNumerator,countDenominator                     
    
    def is_bilphrase_compatible_with_alignments(self,slStart,sllen,tlStart,tllen):
        
        if slStart < 0 or slStart+sllen > len(self.parsed_sl_lexforms) or tlStart < 0 or tlStart+tllen > len(self.parsed_tl_lexforms):
            return False
        
        wordsAlignedWithSL=set()
        for i in xrange(slStart,slStart+sllen):
            wordsAlignedWithSL.update(self.get_tl_words_aligned_with(i))
        
        for j in wordsAlignedWithSL:
            if j < tlStart or j >= tlStart+tllen:
                return False
        
        wordsAlignedWithTL=set()
        for j in xrange(tlStart,tlStart+tllen):
            wordsAlignedWithTL.update(self.get_sl_words_aligned_with(j))
        
        for i in wordsAlignedWithTL:
            if i < slStart or i >= slStart+sllen:
                return False
        return True
    
    def extract_all_biphrases(self,maxLen=5):
        
        bilphrases=list()
        
        #koehn(2003) algorithm
        for sl_start in xrange(len(self.parsed_sl_lexforms)):
            for sl_end in xrange(sl_start+1,len(self.parsed_sl_lexforms)):
                #slstart is the first SL word of the phrase
                #slend is the the word after the last SL word of the phrase
                #the length of the phrase is slend-slstart
                if sl_end -sl_start <= maxLen:
                    tlwordsaligned=set()
                    for sli in xrange(sl_start,sl_end):
                        tlwordsaligned.update(self.get_tl_words_aligned_with(sli))
                    
                    if len(tlwordsaligned) > 0:
                        #find leftmost TL word aligned with a SL from the phrase
                        leftmost=min(tlwordsaligned)
                        #find rightmost TL word aligned with a SL from the phrase
                        rightmost=max(tlwordsaligned)
                        
                        #check whether phrase is compatible with the alignments
                        if self.is_bilphrase_compatible_with_alignments(sl_start, sl_end-sl_start, leftmost, rightmost-leftmost+1):
                            #extract bilphrases including unaliged tl edges
                            #check lenth
                            numUnalignedLeft=0
                            while leftmost-numUnalignedLeft-1 >= 0 and len(self.get_sl_words_aligned_with(leftmost-numUnalignedLeft-1)) == 0:
                                numUnalignedLeft+=1
                            numUnalignedRight=0
                            while rightmost+numUnalignedRight+1 <= len(self.parsed_tl_lexforms) and len(self.get_sl_words_aligned_with(rightmost+numUnalignedRight+1)) == 0:
                                numUnalignedRight+=1
                            
                            for offleft in xrange(numUnalignedLeft+1):
                                for offright in xrange(numUnalignedRight+1):
                                    tl_start=leftmost-offleft
                                    tl_end=rightmost+1+offright
                                    #check length before extracting bilphrase
                                    if tl_end -tl_start <= maxLen:
                                        #extract actual bilphrase
                                        bilphrases.append(self.extract_bilphrase(sl_start, sl_end-sl_start, tl_start, tl_end-tl_start))
        return bilphrases                                                        
                            
                        
    
    def extract_bilphrase(self,slStart,sllen,tlStart,tllen):
        self.extract_bslt()
        bilphrase=ruleLearningLib.AlignmentTemplate()
        for i in xrange(slStart,slStart+sllen):
            newlexform=ruleLearningLib.AT_LexicalForm()
            newlexform.parse(self.parsed_sl_lexforms[i].unparse())
            newrestriction=ruleLearningLib.AT_Restriction()
            newrestriction.parse(self.parsed_restrictions[i].unparse())
            
            bilphrase.parsed_sl_lexforms.append(newlexform)
            bilphrase.parsed_restrictions.append(newrestriction)
        
        for j in xrange(tlStart,tlStart+tllen):
            newlexform=ruleLearningLib.AT_LexicalForm()
            newlexform.parse(self.parsed_tl_lexforms[j].unparse())
            bilphrase.parsed_tl_lexforms.append(newlexform)
        
        for a in self.alignments:
            if a[0] >= slStart and a[0] < slStart+sllen and a[1] >=tlStart and a[1] < tlStart+tllen:
                bilphrase.alignments.append((a[0]-slStart,a[1]-tlStart))
        
        bilphrase.sl_position_in_sentence=slStart
        bilphrase.tl_position_in_sentence=tlStart
        
        bilphrase.bslt=self.bslt.sub(slStart,sllen,tlStart,tllen)    
        
        if len(self.tl_lemmas_from_dictionary) > 0:
            bilphrase.tl_lemmas_from_dictionary.extend(self.tl_lemmas_from_dictionary[slStart:slStart+sllen])
        
        return bilphrase
    
    def extract_bilphrases_containing_antiphrase(self,antiphrase,side,maxLength=5):
        
        bilphrases=[]
        
        positionsAntiSL,positionsAntiTL,leftMostAndRightMost=antiphrase
        maxlenSL=maxLength-len(positionsAntiSL)
        maxlenTL=maxLength-len(positionsAntiTL)
        
        if side == ParallelSentence.SIDE_LEFT:
            if len(positionsAntiSL) > 0:
                positionStartAntiSL=positionsAntiSL[0]
            else:
                positionStartAntiSL=leftMostAndRightMost[1]
            
            if len(positionsAntiTL) > 0:
                positionStartAntiTL=positionsAntiTL[0]
            else:
                positionStartAntiTL=leftMostAndRightMost[1]
            
            for sllen in xrange(1,maxlenSL+1):
                for tllen in xrange(1,maxlenTL+1):
                    startSLsegment=positionStartAntiSL-sllen
                    startTLsegment=positionStartAntiTL-tllen
                    if self.is_bilphrase_compatible_with_alignments(startSLsegment,sllen+len(positionsAntiSL),startTLsegment,tllen+len(positionsAntiTL)):
                        bilphrases.append(self.extract_bilphrase(startSLsegment,sllen+len(positionsAntiSL),startTLsegment,tllen+len(positionsAntiTL)))
                    
        elif side == ParallelSentence.SIDE_RIGHT:
            if len(positionsAntiSL) > 0:
                positionStartAntiSL=positionsAntiSL[0]
                positionEndAntiSL=positionsAntiSL[-1]+1
            else:
                positionStartAntiSL=leftMostAndRightMost[1]
                positionEndAntiSL=leftMostAndRightMost[1]
            
            if len(positionsAntiTL) > 0:
                positionStartAntiTL=positionsAntiTL[0]
                positionEndAntiTL=positionsAntiTL[-1]+1
            else:
                positionStartAntiTL=leftMostAndRightMost[1]
                positionEndAntiTL=leftMostAndRightMost[1]
            
            for sllen in xrange(1,maxlenSL+1):
                for tllen in xrange(1,maxlenTL+1):
                    endSLsegment=positionEndAntiSL+sllen
                    endTLsegment=positionEndAntiTL+tllen
                    if self.is_bilphrase_compatible_with_alignments(positionStartAntiSL,sllen+len(positionsAntiSL),positionStartAntiTL,tllen+len(positionsAntiTL)):
                        bilphrases.append(self.extract_bilphrase(positionStartAntiSL,sllen+len(positionsAntiSL),positionStartAntiTL,tllen+len(positionsAntiTL)))
        else:
            print >> sys.stderr, "WARNING: Incorrect side parameter"
        
        return bilphrases
    
    def compute_coverages_and_bleu(self,ruleLists,beamSize,boxesCoverage=False,boxesDic=dict(),allowIncompatibleRules=False):
        
        #debug("Keys in boxesDic: "+str(boxesDic.keys()))
        
        if boxesCoverage:
            RuleApplicationHypothesis.set_num_total_rules(len(boxesDic))
        else:
            RuleApplicationHypothesis.set_num_total_rules(len(ruleList))
        RuleApplicationHypothesis.set_max_length( max(ruleList.get_max_length() for ruleList in ruleLists))
        
        boxesInverseDic=dict()
        for key in boxesDic.keys():
            boxesInverseDic[boxesDic[key]]=key
        RuleApplicationHypothesis.set_inv_boxes_dict(boxesInverseDic) 
        
        #Compute rightmost TL word aligned with any SL word for each SL prefix
        tlprefixes=list()
        for i in range(len(self.sl_lexforms)):
            tlWordsAligned=[ a[1] for a in self.alignments if a[0] <= i ]
            rightmostTL=max(tlWordsAligned) if len(tlWordsAligned) > 0 else -1
            tlprefixes.append(self.parsed_tl_lexforms[:rightmostTL+1])
        
        #initialise pools
        #pool[i] is the result of processing the SL words in position < i
        #pool[0] contains the initial, empty hypothesis
        ruleApplicationPools=list()
        for i in range(len(self.parsed_sl_lexforms)+1):
            ruleApplicationPools.append([])
        ruleApplicationPools[0].append(RuleApplicationHypothesis(len(self.parsed_sl_lexforms)))

        #Beam search
        for i in range(len(self.parsed_sl_lexforms)):
            
            ##### DEBUG ####
            debug("")
            debug("Starting beam search step "+str(i))
            debug("Processed SL prefix:")
            debug(" ".join( lf.unparse().encode('utf-8') for lf in self.parsed_sl_lexforms[:i])) 
            debug(str(len(ruleApplicationPools[i]))+" hypothesis from previous steps before pruning")
            if i > 0:
                #score previous hypothesis and remove
                RuleApplicationHypothesis.score_hypotheses(ruleApplicationPools[i])
                ruleApplicationPools[i]=sorted(ruleApplicationPools[i],key=lambda h: h.get_score_with_num_rules() ,reverse=True)[:beamSize]
            debug(str(len(ruleApplicationPools[i]))+" hypothesis from previous steps after pruning")
            debug("Showing them:")
            if ruleLearningLib.DEBUG:
                position=0
                for hyp in ruleApplicationPools[i]:
                    position+=1
                    debug("\t"+str(position)+" "+hyp.to_str_for_debug().encode('utf-8'))
                    for id in hyp.get_applied_rules():
                        if boxesCoverage:
                            debug("\t\t"+str(id)+" "+boxesInverseDic[id])
                        else:
                            debug("\t\t"+str(id)+" "+unicode(ruleList.get_by_id(id)).encode('utf-8'))
            ##### DEBUG ####            
            
            #compute rules which match
            
            rulesMatchingListForEachATSset=list()
            for index,ruleList in enumerate(ruleLists):
                ruleMatchingList=ruleList.get_rules_matching_segment(self.parsed_sl_lexforms[i:],self.parsed_restrictions[i:])
                debug("AT set "+str(index)+" :"+str(len(ruleMatchingList))+" new rules/boxes can be applied")
                rulesMatchingListForEachATSset.append(ruleMatchingList)
            
            newPartialHypotheses=list()
            #for each rule, compute ats to be added to applied rules, ats to be discarded and resulting segment
            
            newHypothesesByTLSegment=defaultdict(list)
            for ruleListIndex,ruleMatchingList in enumerate(rulesMatchingListForEachATSset):
                prevAppliedBoxes=set()
                for j in range(len(ruleMatchingList)):
                    at=ruleMatchingList[j]
                    if boxesCoverage:
                        boxid=boxesDic[at.get_pos_list_str()]
                        if not boxid in prevAppliedBoxes:
                            hyp=RuleApplicationHypothesis(len(self.parsed_sl_lexforms))
                            hyp.add_to_applied_rules(boxid,[ruleListIndex])
                            for prevBox in prevAppliedBoxes:
                                hyp.discardedRules.add(prevBox)
                            hyp.set_processed_sl_words(len(at.parsed_sl_lexforms))
                            hyp.add_to_rules_list(boxid, at.get_pos_list_str().split("__"),[ruleListIndex])
                            
                            #apply at to matching segment
                            tlsegment=at.apply(self.parsed_sl_lexforms[i:],self.tl_lemmas_from_dictionary[i:],self.parsed_restrictions[i:])
                            hyp.set_translation(tlsegment)
                            
                            newHypothesesByTLSegment[str(tlsegment)].append(hyp)
                            #newPartialHypotheses.append(hyp)
                            
                            prevAppliedBoxes.add(boxid)
                    else:
                        #TODO: adapt to multiple lists of Ats
                        hyp=RuleApplicationHypothesis(len(self.parsed_sl_lexforms))
                        hyp.add_to_applied_rules(at.id)
                        for discAt in ruleMatchingList[:j]:
                            hyp.discardedRules.add(discAt.id)
                        hyp.set_processed_sl_words(len(at.parsed_sl_lexforms))
                        
                        #apply at to matching segment
                        tlsegment=at.apply(self.parsed_sl_lexforms[i:],self.tl_lemmas_from_dictionary[i:],self.parsed_restrictions[i:])
                        hyp.set_translation(tlsegment)
                        
                        newPartialHypotheses.append(hyp)
            
            if boxesCoverage:
                #join translations with same boxid and tl segment
                for listOfHyps in newHypothesesByTLSegment.values():
                    hypsByBoxId=defaultdict(list)
                    for hyp in listOfHyps:
                        hypsByBoxId[hyp.get_rules_list()[0][0]].append(hyp)
                    for lisfOfHypsWithSameBoxId in hypsByBoxId.values():
                        #never empty
                        appliedATIndexes=set()
                        firsthyp=lisfOfHypsWithSameBoxId[0]
                        appliedATIndexes.update(firsthyp.get_rules_list()[0][2])
                        for althyp in lisfOfHypsWithSameBoxId[1:]:
                            firsthyp.get_rules_list()[0][2].append(althyp.get_rules_list()[0][2][0])
                            appliedATIndexes.update(althyp.get_rules_list()[0][2])
                        firsthyp.get_applied_rules().clear()
                        firsthyp.add_to_applied_rules(firsthyp.get_rules_list()[0][0],appliedATIndexes)
                        newPartialHypotheses.append(firsthyp)
            
            #take into account also the case in which no rule is applied
            hyp=RuleApplicationHypothesis(len(self.parsed_sl_lexforms))
            if boxesCoverage:
                #TODO: fix this. Empty discarded boxes.
                #No problem as I am not using discerded boxes right now
                #but it's ugly
                for boxid in prevAppliedBoxes:
                    hyp.discardedRules.add(boxid)
            else:
                for at in ruleMatchingList:
                    hyp.discardedRules.add(at.id)
            hyp.add_to_rules_list(RuleApplicationHypothesis.WORDFORWORDRULEID, [ self.parsed_sl_lexforms[i].get_pos() ])
            tlsegment=list()
            if self.parsed_sl_lexforms[i].is_unknown():
                bilDicTranslation=self.parsed_sl_lexforms[i]
            else:
                bilDicTranslation=AT_LexicalForm()
                bilDicTranslation.set_lemma(self.tl_lemmas_from_dictionary[i])
                bilDicTranslation.set_pos(self.parsed_restrictions[i].get_pos() if not self.parsed_restrictions[i].is_special() else self.parsed_sl_lexforms[i].get_pos())
                bilDicTags=list()
                bilDicTags.extend(self.parsed_restrictions[i].get_tags())
                #bilDicTags.extend(self.parsed_sl_lexforms[i].get_tags()[len(bilDicTags):])
                bilDicTranslation.set_tags(bilDicTags)
            tlsegment.append(bilDicTranslation)
            hyp.set_translation(tlsegment)
            hyp.set_processed_sl_words(1)
            newPartialHypotheses.append(hyp)
            
            debug(str(len(newPartialHypotheses))+" new hypotheses to be combined with prev ones")
            
            #combine previous hypothesis
            for hyp in ruleApplicationPools[i]:
                for hyp2 in newPartialHypotheses:
                    if allowIncompatibleRules or hyp.can_be_combined_with(hyp2):
                        newhyp=hyp.create_new_combined_with(hyp2)
                        newhyp.set_source(self.parsed_sl_lexforms[:newhyp.get_processed_sl_words()])
                        newhyp.set_reference(tlprefixes[newhyp.get_processed_sl_words()-1])
                        ruleApplicationPools[newhyp.get_processed_sl_words()].append(newhyp)
        
        #final step
        ##### DEBUG ####
        debug("")
        debug("Finishing beam search")
        debug("Processed SL prefix: all")
        debug(" ".join( lf.unparse().encode('utf-8') for lf in self.parsed_sl_lexforms)) 
        debug(str(len(ruleApplicationPools[-1]))+" hypothesis from previous steps before pruning")
        #score previous hypothesis and remove
        RuleApplicationHypothesis.score_hypotheses(ruleApplicationPools[-1])
        ruleApplicationPools[-1]=sorted(ruleApplicationPools[-1],key=lambda h: h.get_score_with_num_rules(),reverse=True)[:beamSize]
        debug(str(len(ruleApplicationPools[-1]))+" hypothesis from previous steps after pruning")
        
        if ruleLearningLib.DEBUG:
            debug("Final result with score with num. rules")
            for ryp in ruleApplicationPools[-1]:
                debug(str(ryp.get_score_with_num_rules())+" -> "+unicode(ryp).encode('utf-8'))
        
        return ruleApplicationPools[-1]
    
    @classmethod
    def optimize_boxes_applied_rescoring_bleu(cls,sentences,ruleList,boxesAndProbs,boxesInvIndex):
        #sort boxes by increasing logprob of breaking key segments 
        sortedBoxesAndProbs=sorted(boxesAndProbs,key= lambda entry: entry[1])
        
        increasingRuleList=RuleList()
        results=[]
        
        index=0
        while index < len(sortedBoxesAndProbs):
            box=sortedBoxesAndProbs[index][0]
            increasingRuleList.add_rules_with_seq_of_cats(ruleList, boxesInvIndex[box])
            if index == len(sortedBoxesAndProbs)-1 or sortedBoxesAndProbs[index][1] < sortedBoxesAndProbs[index+1][1]:
                #translate all the sentences
                translationHyps=[]
                for parallelSentence in sentences:
                    wordIndex=0
                    translation=[]
                    while wordIndex < len(parallelSentence.parsed_sl_lexforms):
                        slwords=parallelSentence.parsed_sl_lexforms[wordIndex:]
                        restrictions=parallelSentence.parsed_restrictions[wordIndex:]
                        lemmasFromBil=parallelSentence.tl_lemmas_from_dictionary[wordIndex:]
                        rulesMatching=increasingRuleList.get_rules_matching_segment(slwords, restrictions, exactMatch=False)
                        if len(rulesMatching) > 0:
                            ruleLength=len(rulesMatching[0].parsed_sl_lexforms)
                            translation.extend(rulesMatching[0].apply(slwords[:ruleLength],lemmasFromBil[:ruleLength],restrictions[:ruleLength]))
                            wordIndex+=ruleLength
                        else:
                            if slwords[0].is_unknown():
                                bilDicTranslation=slwords[0]
                            else:
                                bilDicTranslation=ruleLearningLib.AT_LexicalForm()
                                bilDicTranslation.set_lemma(lemmasFromBil[0])
                                bilDicTranslation.set_pos(restrictions[0].get_pos())
                                bilDicTags=list()
                                bilDicTags.extend(restrictions[0].get_tags())
                                bilDicTranslation.set_tags(bilDicTags)
                            translation.append(bilDicTranslation)
                            wordIndex+=1
                    translationHypothesis=RuleApplicationHypothesis()
                    translationHypothesis.set_source(parallelSentence.parsed_sl_lexforms)
                    translationHypothesis.set_translation(translation)
                    translationHypothesis.set_reference(parallelSentence.parsed_tl_lexforms)
                    translationHyps.append(translationHypothesis)
                #score translations
                score=RuleApplicationHypothesis.score_hypotheses(translationHyps,sentenceLevelScores=False)
                results.append((index,score))
            index+=1
        # loop finished
        
        #print some information about BLEU scores
        print >> sys.stderr, "Scores of different thresholds"
        for index,BLEU in results:
            print >> sys.stderr, "threshold="+str(sortedBoxesAndProbs[index][1])+", BLEU="+str(BLEU)+", "+str([e[0] for e in sortedBoxesAndProbs[:index+1]])
        
        #return set of boxes with maximum BLEU
        sortedResults=sorted(results,key=lambda r: r[1],reverse=True)
        if len(sortedResults) > 0:
            bestIndex,bestBLEU=sortedResults[0]
            print >> sys.stderr, "BEST THRESHOLD: p(break key segment) <= "+str(sortedBoxesAndProbs[bestIndex][1])+", BLEU="+str(bestBLEU)
            return [ e[0] for e in sortedBoxesAndProbs[:bestIndex+1] ]
        else:
            return []
           
            
