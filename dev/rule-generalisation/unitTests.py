#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-

import ruleLearningLib,unittest, sys, copy
from ruleLearningLib import AT_GeneralisationOptions, AlignmentTemplateSet

class TestAlignmentTemplates(unittest.TestCase):

	def setUp(self):
		self.at1 = ruleLearningLib.AlignmentTemplate()
		self.at2 = ruleLearningLib.AlignmentTemplate()
		self.at3 = ruleLearningLib.AlignmentTemplate()
		self.at4 = ruleLearningLib.AlignmentTemplate()
		self.at5 = ruleLearningLib.AlignmentTemplate()
		self.at6 = ruleLearningLib.AlignmentTemplate()
		self.at7 = ruleLearningLib.AlignmentTemplate()
		self.at8 = ruleLearningLib.AlignmentTemplate()
		self.at9 = ruleLearningLib.AlignmentTemplate()
		self.at10 = ruleLearningLib.AlignmentTemplate()
		self.at11 = ruleLearningLib.AlignmentTemplate()
		self.at12 = ruleLearningLib.AlignmentTemplate()
		self.at13 = ruleLearningLib.AlignmentTemplate()
		self.at14 = ruleLearningLib.AlignmentTemplate()
		self.at15 = ruleLearningLib.AlignmentTemplate()
		self.at16 = ruleLearningLib.AlignmentTemplate()
		self.at17 = ruleLearningLib.AlignmentTemplate()
		
		self.at18 = ruleLearningLib.AlignmentTemplate()
		self.bil18 = ruleLearningLib.AlignmentTemplate()
		
		self.at19= ruleLearningLib.AlignmentTemplate()
		self.bil19= ruleLearningLib.AlignmentTemplate()
		
		self.at20= ruleLearningLib.AlignmentTemplate()
		self.bil20= ruleLearningLib.AlignmentTemplate()

		self.at1.parse(u"<det><ind><m><sg> <n><m><sg> | <det><ind><f><pl> <n><f><pl> | 0:0 1:1 | <det> <n><f><pl>")
		self.at2.parse(u"<det><def><m><sg> dinero<n><m><sg> | <det><def><m><pl> diner<n><m><pl> | 0:0 1:1 | <det><def> <n><m><pl>")
		self.at3.parse(u"<det><def><m><sg> <n><m><sg> | <det><def><f><pl> <n><f><pl> | 0:0 1:1 | <det><def> <n><f><pl>")
		self.at4.parse(u"<det><ind><*gender><*numberat> <n><*gender><*numberat> | <det><ind><*gender><*numberat> <n><*gender><*numberat> | 0:0 1:1 | <det> <n>")
		self.at5.parse(u"<det><def><*gender><*numberat> <n><*gender><*numberat> | <det><def><*gender><*numberat> <n><*gender><*numberat> | 0:0 1:1 | <det><def> <n>")
		self.at6.parse(u"<vbser><ifi><p3><sg> <vblex><pp><m><sg> | anar<vaux><p3><sg> <vbser><inf> <vblex><pp><m><sg> | 0:1 1:2 | <vbser> <vblex>")
		self.at7.parse(u"<det><def><m><*numberat> <n><m><*numberat> | <det><def><m><*numberat> <n><m><*numberat> | 0:0 1:1 | <det><def> <n>")
		self.at8.parse(u"<det><def><m><*numberat> <n><f><*numberat> | <det><def><m><*numberat> <n><m><*numberat> | 0:0 1:1 | <det><def> <n>")
		self.at9.parse(u"<det><*determinertype><*gender><*numberat> <n><*gender><*numberat> | <det><*determinertype><*gender><*numberat> <n><*gender><*numberat> | 0:0 1:1 | <det> <n>")
		self.at10.parse(u"<det><def><f><sg> <n><f><sg> | <det><def><f><pl> <n><f><pl> | 0:0 1:1 | <det><def> <n><f><pl>")
		
		self.at13.parse(u"el<det><def><m><*numberat> <n><f><*numberat> | <det><def><m><*numberat> <n><m><*numberat> | 0:0 1:1 | <det><def> <n>")
		self.at14.parse(u"el<det><def><*gender><*numberat> <n><f><sg> | <det><def><m><*numberat> <n><m><*numberat> | 0:0 1:1 | <det><def> <n>")
		self.at15.parse(u"el<det><def><*gender><*numberat> <n><m><sg> | <det><def><m><*numberat> <n><m><*numberat> | 0:0 1:1 | <det><def> <n>")
		self.at16.parse(u"<det><*determinertype><*gender><*numberat> <n><*gender><*numberat> | <det><)000determinertype><)001gender><)001numberat> <n><)001gender><)001numberat> | 0:0 1:1 | <det> <n>")
		self.at17.parse(u"<det><ind><m><sg> <n><m><sg> | <det><ind><f><pl> <n><f><pl> | 0:0 1:1 | <det> <n><f><pl>")
		
		self.at11.parse(u"<vbser><ifi><p3><sg> <vblex><pp><m><sg> | anar<vaux><p3><sg> <vbser><inf> <vblex><pp><m><sg> | 0:1 1:2 | <vbser> <vblex>")
		
		self.at12.parse(u"suyo<det><pos><mf><sp> <n><empty_tag_ntype><f><sg> <pr> | el<det><def><f><sp> <n><empty_tag_ntype><f><sg> <pr> | 0:0 1:1 2:2 | __CLOSEWORD__ <n> <pr>")
		
		self.at18.parse(u"<det><def><f><*numberat> <n><empty_tag_ntype><f><*numberat> | <det><def><f><)000numberat> <n><empty_tag_ntype><f><)001numberat> | 0:0 1:1 | <det><def><f><pl> <n>")
		self.bil18.parse(u"el<det><def><f><pl> casa<n><empty_tag_ntype><f><pl> | el<det><def><f><pl> casa<n><empty_tag_ntype><f><pl> | 0:0 1:1 | <det><def> <n>")
		self.bil18.tl_lemmas_from_dictionary=[u"el",u"casa"]
		
		self.at19.parse(u"el<det><def><*gender><*numberat> <n><empty_tag_ntype><*gender><*numberat> | <n><empty_tag_ntype><)001gender><)000numberat> | 0:0 1:0 | <det> <n>")
		self.bil19.parse(u"el<det><def><f><sg> casa<n><empty_tag_ntype><f><sg> | casa<n><empty_tag_ntype><f><sg> | 0:0 1:0 | <det> <n>")
		self.bil19.tl_lemmas_from_dictionary=[u"el",u"casa"]
		
		self.at20.parse(u"<n><empty_tag_ntype><f><*numberat> <adj><empty_tag_adjtype><f><*numberat> | <n><empty_tag_ntype><f><)000numberat> <adj><empty_tag_adjtype><f><)001numberat> | 0:0 1:1 | <n><empty_tag_ntype><f> <adj><empty_tag_adjtype><f>")
		self.bil20.parse(u"companyia<n><empty_tag_ntype><f><pl> elèctric<adj><empty_tag_adjtype><f><pl> | compañía<n><empty_tag_ntype><f><pl> eléctrico<adj><empty_tag_adjtype><f><pl> | 0:0 1:1 | <n> <adj>")
		self.bil20.tl_lemmas_from_dictionary=[u"compañía",u"eléctrico"]
		
		self.atlist=[self.at1,self.at2,self.at3,self.at4,self.at5]
		
		myfile=open("taggroups",'r')
		self.taggroups=ruleLearningLib.read_tag_groups(myfile)
		myfile.close()
		
		ruleLearningLib.AT_LexicalTagsProcessor.initialize("taggroups","tagsequences")
		
	def test_subset(self):
		print "nada"
		#revisar
		#self.assertFalse(self.at1.is_subset_of_this(self.at2,self.taggroups))
		#self.assertFalse(self.at2.is_subset_of_this(self.at1,self.taggroups))
		#self.assertFalse(self.at3.is_subset_of_this(self.at2,self.taggroups))
		#self.assertTrue(self.at5.is_subset_of_this(self.at2,self.taggroups))
		#self.assertFalse(self.at4.is_subset_of_this(self.at2,self.taggroups))
		#self.assertTrue(self.at4.is_subset_of_this(self.at1,self.taggroups))
		#self.assertFalse(self.at2.is_subset_of_this(self.at3,self.taggroups))
	
	def test_compare(self):
		mylist=list()
		mylist.append(self.at1)
		
		mylist2=list()
		mylist2.append(self.at1)
		myat=mylist2[0]
		
		mylist.remove(myat)
		
		self.assertTrue(len(mylist)==0)
	
	def test_lexical_forms(self):
		self.assertEqual(2, self.at4.parsed_sl_lexforms[0].get_num_generalised_tags())
	
	def test_union_intersection_empty(self):
		self.assertTrue(self.at1.is_symmetric_difference_empty(self.at2))
		self.assertTrue(self.at1.is_symmetric_difference_empty(self.at4))
		self.assertTrue(self.at5.is_symmetric_difference_empty(self.at4))
		self.assertFalse(self.at14.is_symmetric_difference_empty(self.at13))
		self.assertTrue(self.at15.is_symmetric_difference_empty(self.at13))
	
	def no_test_groupats(self):
		errorCode,groups=ruleLearningLib.group_ats_for_transfer_rule(self.atlist,self.taggroups)
		self.assertTrue(len(errorCode)==0)
		
	def no_test_generalise(self):
		self.at6.generalise(self.taggroups)
		self.assertTrue(self.at6.sl_lexforms[0]==u"<vbser><ifi><p3><sg>")
		self.assertTrue(self.at6.sl_lexforms[1]==u"<vblex><pp><m><sg>")
		
		self.at1.generalise(self.taggroups)
		self.assertTrue(self.at1.sl_lexforms[0]==u"<det><ind><m><sg>")
		self.assertTrue(self.at1.sl_lexforms[1]==u"<n><m><sg>")
		
		self.at2.generalise(self.taggroups)
		self.assertTrue(self.at2.sl_lexforms[0]==u"<det><def><m><sg>")
		self.assertTrue(self.at2.sl_lexforms[1]==u"dinero<n><m><sg>")
		
		self.at7.generalise(self.taggroups)
		self.assertTrue(self.at7.sl_lexforms[0]==u"<det><def><*gender><*numberat>")
		self.assertTrue(self.at7.sl_lexforms[1]==u"<n><*gender><*numberat>")
		
		self.at8.generalise(self.taggroups)
		self.assertTrue(self.at8.sl_lexforms[0]==u"<det><def><m><*numberat>")
		self.assertTrue(self.at8.sl_lexforms[1]==u"<n><f><*numberat>")
		
		self.at9.generalise(self.taggroups)
		self.assertTrue(self.at9.sl_lexforms[0]==u"<det><*determinertype><*gender><*numberat>")
		self.assertTrue(self.at9.sl_lexforms[1]==u"<n><*gender><*numberat>")
		
		self.at10.generalise(self.taggroups,False,False)
		self.assertTrue(self.at10.sl_lexforms[0]==u"<det><def><f><*numberat>")
		self.assertTrue(self.at10.tl_lexforms[0]==u"<det><def><f><pl>")
		self.at10.generalise(self.taggroups,False,False)
		self.assertTrue(self.at10.sl_lexforms[0]==u"<det><def><*gender><*numberat>")
		self.assertTrue(self.at10.tl_lexforms[0]==u"<det><def><*gender><pl>")
		self.at10.generalise(self.taggroups,False,False)
		self.assertTrue(self.at10.sl_lexforms[0]==u"<det><*determinertype><*gender><*numberat>")
		self.assertTrue(self.at10.tl_lexforms[0]==u"<det><*determinertype><*gender><pl>")
		self.at10.generalise(self.taggroups,False,False)
		self.assertTrue(self.at10.sl_lexforms[0]==u"<det><*determinertype><*gender><*numberat>")
		self.assertTrue(self.at10.tl_lexforms[0]==u"<det><*determinertype><*gender><pl>")
		
		self.at12.generalise(self.taggroups)
		
		
	def no_test_autoalign(self):
		alignmentoptions=self.at11.get_alignment_options_for_unaligned_words(self.taggroups)
		self.assertTrue(len(alignmentoptions)==3)
		self.assertTrue(len(alignmentoptions[0])==1)
		self.assertTrue(alignmentoptions[0][0][0]==0)
		self.assertTrue(alignmentoptions[0][0][1]==0)
		
		self.assertTrue(len(alignmentoptions[1])==1)
		self.assertTrue(alignmentoptions[1][0][0]==1)
		self.assertTrue(alignmentoptions[1][0][1]==0)
		
		self.assertTrue(len(alignmentoptions[2])==0)
	
	def no_test_tonto(self):
		
		taggroups=self.taggroups
		
		bilphrasesSet=ruleLearningLib.AlignmentTemplateSet(taggroups)
		originalATList=list()
		
		numAt=0
		print >> sys.stderr, "Reading ALignment Templates/ Bilingual Phrases...."
		for line in sys.stdin:
			numAt+=1
			
			line=line.decode('utf-8').strip()
			at = ruleLearningLib.AlignmentTemplate()
			
			piecesOfline=line.split(u'|')
			textat=u'|'.join(piecesOfline[1:5])
			freq=piecesOfline[0].strip()
			
			sllemmastext=piecesOfline[5].strip()
			tllemmastext=piecesOfline[6].strip()
			sllemmas=sllemmastext.split(u'\t')
			tllemmas=tllemmastext.split(u'\t')
			
			at.parse(textat)
			
			
			at.freq=int(freq)
							
			tl_lemmas_from_dictionary_text=piecesOfline[7].strip()
			tl_lemmas_from_dictionary_list=tl_lemmas_from_dictionary_text.split(u'\t')
			
			bilphrase=copy.deepcopy(at)
			bilphrase.tl_lemmas_from_dictionary=tl_lemmas_from_dictionary_list
			bilphrase.lexicalise_all(sllemmas,tllemmas)
			bilphrase.id=numAt
			bilphrasesSet.add(bilphrase)
			
			originalATList.append((at,sllemmas,tllemmas,tl_lemmas_from_dictionary_list))
			
			#print bilphrase.tl_lemmas_from_dictionary
			
		print >> sys.stderr, " ....."+str(len(originalATList))+" items."
		solution=generaliseATs.generalise_by_linear_program(bilphrasesSet,originalATList,taggroups)
		
		for at in solution:
			print at
	
	def test_specifity(self):
		pass
		#self.assertEqual(self.at1.get_specificity_level(),7)
	
	def test_structural_generalisations(self):
		generalisationOptions=AT_GeneralisationOptions()
		generalisationOptions.set_fromRightToLeft(True)
		generalisationOptions.set_refToBiling(True)
		structuralGeneraisations=ruleLearningLib.AlignmentTemplate_generate_all_structural_generalisations(self.at1, generalisationOptions)
		print >> sys.stderr, "Structural generalisations:"
		for structuralGenAt in structuralGeneraisations:
			print >> sys.stderr, structuralGenAt
		self.assertGreater(len(structuralGeneraisations), 1)
		self.assertTrue(self.at16 in structuralGeneraisations)
	
	def test_lexical_generalisations(self):
		ruleLearningLib.DEBUG=True
		
		finalAlignmentTemplates=AlignmentTemplateSet()
		generalisationOptions=AT_GeneralisationOptions()
		lastId=ruleLearningLib.AlignmentTemplate_generate_all_lexical_generalisations_and_add_them(self.at1,self.at1, [u"el",u"dinero"], [u"el",u"diners"], [u"el",u"diners"], finalAlignmentTemplates, 0, generalisationOptions)
		print >> sys.stderr, "Lexical generalisations 1:"
		for at in finalAlignmentTemplates.get_all_ats_list():
			print >> sys.stderr, at
		self.assertEqual(len(finalAlignmentTemplates.get_all_ats_list()),4)
		
		
		finalAlignmentTemplates=AlignmentTemplateSet()
		generalisationOptions=AT_GeneralisationOptions()
		lastId=ruleLearningLib.AlignmentTemplate_generate_all_lexical_generalisations_and_add_them(self.at16,self.at1, [u"el",u"dinero"], [u"el",u"diners"], [u"el",u"diners"], finalAlignmentTemplates, 0, generalisationOptions)
		print >> sys.stderr, "Lexical generalisations 2:"
		for at in finalAlignmentTemplates.get_all_ats_list():
			print sys.stderr, at
		self.assertEqual(len(finalAlignmentTemplates.get_all_ats_list()),4)
		
	def test_hash(self):
		myDict=dict()
		myDict[self.at1]=1
		self.assertTrue(self.at17 in myDict.keys())
	
	def test_reproducible(self):
		self.assertTrue(self.at18.is_bilphrase_reproducible(self.bil18))
		self.assertTrue(self.at20.is_bilphrase_reproducible(self.bil20))
	
	def test_unalignment_options(self):
		unoptions=self.at19.get_unalignment_options_for_multiple_aligned_unlexicalised_tl_words(self.bil19)
		print >> sys.stderr, str(unoptions)
		self.assertEqual(len(unoptions),1)
		self.assertEqual(len(unoptions[0]),1)
		unoptions0list=list()
		unoptions0list.extend(unoptions[0])
		self.assertEqual(unoptions0list[0][0],0)
		self.assertEqual(unoptions0list[0][1],0)
	
	def test_explicit_restrictions(self):
		myat=self.at1.fast_clone()
		myat.add_explicit_restrictions()
		expectedAT=ruleLearningLib.AlignmentTemplate()
		expectedAT.parse(u"<det><ind><m><sg> <n><m><sg> | <det><ind><f><pl> <n><f><pl> | 0:0 1:1 | <det><ind><m><sg> <n><f><pl>")
		self.assertEqual(myat, expectedAT)
		
	
if __name__ == '__main__':
    unittest.main()
