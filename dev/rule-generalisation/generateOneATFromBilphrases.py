'''
Created on 09/10/2013

@author: vmsanchez
'''
import ruleLearningLib,sys,argparse,copy
if __name__=="__main__":
    inputFile=sys.stdin
    DEBUG=False

    parser = argparse.ArgumentParser(description='Generates one AT from each bilingual phrase.')
    parser.add_argument('--tag_groups_file_name',required=True)
    parser.add_argument('--tag_sequences_file_name',required=True)
    parser.add_argument('--closed_categories',required=True)
    parser.add_argument('--debug',action='store_true')
    args = parser.parse_args(sys.argv[1:])
    
    #Process arguments
    if args.debug:                  
        DEBUG=True
        ruleLearningLib.DEBUG=True
    ruleLearningLib.AT_LexicalTagsProcessor.initialize(args.tag_groups_file_name,args.tag_sequences_file_name)
    
    closedCategoriesSet=set( [ rawcat.decode('utf-8').strip()[1:-1] for rawcat in open(args.closed_categories)] )
    print >> sys.stderr, str(closedCategoriesSet)
    
    for line in inputFile:    
        line=line.decode('utf-8').strip()
        at = ruleLearningLib.AlignmentTemplate()
        bilphrase=ruleLearningLib.AlignmentTemplate()
        
        piecesOfline=line.split(u'|')
        textat=u'|'.join(piecesOfline[1:5])
        freq=piecesOfline[0].strip()
        
        sllemmastext=piecesOfline[5].strip()
        tllemmastext=piecesOfline[6].strip()
        sllemmas=sllemmastext.split(u'\t')
        tllemmas=tllemmastext.split(u'\t')
        
        at.parse(textat)
        at.add_explicit_empty_tags()
        at.add_explicit_restrictions()
        at.freq=int(freq)
        tl_lemmas_from_dictionary_text=piecesOfline[7]
        tl_lemmas_from_dictionary_list=[ l.strip() for l in tl_lemmas_from_dictionary_text.split(u'\t')]
        
        at.lexicalise_from_categories(closedCategoriesSet,sllemmas,tllemmas)
        
        bilphrase=copy.deepcopy(at)
        bilphrase.set_lemmas(sllemmas,tllemmas)
        bilphrase.tl_lemmas_from_dictionary=tl_lemmas_from_dictionary_list
        
        
        unalignmentOptions=at.get_unalignment_options_for_multiple_aligned_unlexicalised_tl_words(bilphrase)
        
        unalignmentCorrectATs=list()
        for unalOption in unalignmentOptions:
            unat=at.fast_clone()
            unat.remove_alignments(unalOption)
            if unat.is_bilphrase_reproducible(bilphrase):
                unalignmentCorrectATs.append(unat)
        
        if len(unalignmentCorrectATs) == 0:
            print >> sys.stderr, "Cannot generate correct AT from: "+line.encode('utf-8')
        else:
            sortedList=sorted(unalignmentCorrectATs,key= lambda a: len(a.alignments))
            print "1 | "+sortedList[0].to_string()
            
        