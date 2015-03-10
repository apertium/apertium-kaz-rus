# author: Felipe Sánchez Martínez

bin_PROGRAMS = apertium-xtract-bilingual-phrases apertium-gen-transfer-from-aligment-templates \
               apertium-symmetrize-alignments apertium-posttransfer apertium-apply-biling apertium-add-restrictions-to-sl apertium-xtract-bilingual-phrases-koehn-2003

bin_SCRIPTS = giza++A3-to-apertium apertium-validate-transfer-at apertium-preprocess-corpus-transfer-at apertium-switch-alignments \
              apertium-validate-posttransfer

apertium_transfer_toolsdir=$(prefix)/apertium-transfer-tools-generalisation-$(GENERIC_API_VERSION)
apertium_transfer_tools_DATA = apertium-transfer-at.dtd apertium-posttransfer.dtd

EXTRA_DIST = giza++A3-to-apertium.awk apertium-transfer-at.dtd validate-xml-dtd.sh preprocess-corpus.awk switch-alignments.awk \
             apertium-posttransfer.dtd

apertium_add_restrictions_to_sl_SOURCES=apertium-add-restrictions-to-sl.C Utils.H Utils.C

apertium_add_restrictions_to_sl_LDADD=$(LTTOOLBOX_LIBS) $(APERTIUM_LIBS) $(Z_LIBS)

apertium_apply_biling_SOURCES= apertium-apply-biling.C Utils.H Utils.C

apertium_apply_biling_LDADD= $(LTTOOLBOX_LIBS) $(APERTIUM_LIBS) $(Z_LIBS)

apertium_xtract_bilingual_phrases_SOURCES =  apertium-xtract-bilingual-phrases.C Alignment.H Alignment.C \
       Utils.H Utils.C zfstream.H zfstream.C
apertium_xtract_bilingual_phrases_LDADD = $(LIBXML2_LIBS) $(LTTOOLBOX_LIBS) $(APERTIUM_LIBS) $(Z_LIBS)

apertium_xtract_bilingual_phrases_koehn_2003_SOURCES = apertium-xtract-bilingual-phrases-koehn-2003.C TablesCore.C TablesCore.H \
       SentenceAlignment.C SentenceAlignment.H SafeGetline.h

apertium_xtract_bilingual_phrases_koehn_2003_LDADD = $(LIBXML2_LIBS) $(LTTOOLBOX_LIBS) $(APERTIUM_LIBS) $(Z_LIBS)

apertium_gen_transfer_from_aligment_templates_SOURCES = apertium-gen-transfer-from-aligment-templates.C \
       AlignmentTemplate.H AlignmentTemplate.C Alignment.H Alignment.C LexicalizedWords.H LexicalizedWords.C \
       Utils.H Utils.C zfstream.H zfstream.C TransferRule.H TransferRule.C
apertium_gen_transfer_from_aligment_templates_LDADD = $(LIBXML2_LIBS) $(LTTOOLBOX_LIBS) $(APERTIUM_LIBS) $(Z_LIBS) -lm

apertium_symmetrize_alignments_SOURCES = apertium-symmetrize-alignments.C Alignment.H Alignment.C Utils.H Utils.C \
       zfstream.H zfstream.C 
apertium_symmetrize_alignments_LDADD = $(LTTOOLBOX_LIBS) $(APERTIUM_LIBS) $(Z_LIBS)

apertium_posttransfer_SOURCES = apertium-posttransfer.C PTXReader.H PTXReader.C Utils.H Utils.C
apertium_posttransfer_LDADD = $(LTTOOLBOX_LIBS) $(APERTIUM_LIBS) $(Z_LIBS)

INCLUDES = $(LIBXML2_CFLAGS) $(LTTOOLBOX_CFLAGS) $(APERTIUM_CFLAGS) $(Z_CFLAGS)

CLEANFILES = *~ $(bin_SCRIPTS)

giza++A3-to-apertium:  giza++A3-to-apertium.awk Makefile.am
	@echo "Creating $@ script"
	@echo "#!$(AWK) -f" > $@
	@cat  giza++A3-to-apertium.awk >> $@
	@chmod a+x $@

apertium-switch-alignments: switch-alignments.awk Makefile.am
	@echo "Creating $@ script"
	@echo "#!$(AWK) -f" > $@
	@cat switch-alignments.awk >> $@
	@chmod a+x $@

apertium-analyse-alignments: apertium-analyse-alignments.sh Makefile.am
	@echo "Creating $@ script"
	@echo "#!$(BASH) " > $@
	@cat  apertium-analyse-alignments.sh >> $@
	@chmod a+x $@

apertium-validate-transfer-at: validate-xml-dtd.sh Makefile.am
	@echo "Creating $@ script"
	@echo "#!$(BASH)" > $@
	@echo "XMLLINT=$(XMLLINT)" >> $@
	@echo "DTD=$(apertium_transfer_toolsdir)/apertium-transfer-at.dtd" >> $@
	@cat validate-xml-dtd.sh >> $@
	@chmod a+x $@

apertium-preprocess-corpus-transfer-at:  preprocess-corpus.awk Makefile.am
	@echo "Creating $@ script"
	@echo "#!$(AWK) -f" > $@
	@cat  preprocess-corpus.awk >> $@
	@chmod a+x $@

apertium-validate-posttransfer: validate-xml-dtd.sh Makefile.am
	@echo "Creating $@ script"
	@echo "#!$(BASH)" > $@
	@echo "XMLLINT=$(XMLLINT)" >> $@
	@echo "DTD=$(apertium_transfer_toolsdir)/apertium-posttransfer.dtd" >> $@
	@cat validate-xml-dtd.sh >> $@
	@chmod a+x $@
