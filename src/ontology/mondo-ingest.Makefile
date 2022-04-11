## Customize Makefile settings for mondo-ingest
## 
## If you need to customize your Makefile, make
## changes here rather than in the main Makefile

define generate_module
	if [ $(IMP) = true ]; then $(ROBOT) remove -i $(MIRRORDIR)/$(1).owl -T $(TMPDIR)/$(1)_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		query --update ../sparql/fix_omimps.ru --update ../sparql/fix_hgnc_mappings.ru --update ../sparql/fix_deprecated.ru --update ../sparql/fix_complex_reification.ru \
		annotate --ontology-iri $(URIBASE)/mondo/sources/$(1).owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/$(1).owl -o $@; fi
endef

####################################
### Relevant signature #############
####################################

# This section is concerned with identifiying 
# the entities of interest that 
# should be imported from the source

# Obtains the entities of interest from an ontology, as specified in a bespoke sparql query (bespoke
# for that ontology).
$(TMPDIR)/%_relevant_signature.txt: $(MIRRORDIR)/%.owl | $(TMPDIR)
	$(ROBOT) query -i $< -q "../sparql/$*-relevant-signature.sparql" $@

### ORDO needs to be structurally changed before the query can be run..
$(TMPDIR)/ordo_relevant_signature.txt: $(MIRRORDIR)/ordo.owl | $(TMPDIR)
	$(ROBOT) query -i $< --update ../sparql/ordo-construct-subclass-from-part-of.ru \
		query -q "../sparql/ordo-relevant-signature.sparql" $@
.PRECIOUS: $(TMPDIR)/ordo_relevant_signature.txt

####################################
### Ingest Modules #################
####################################

# This section is concerned with identifiying 

$(IMPORTDIR)/omim_import.owl: $(MIRRORDIR)/omim.owl $(TMPDIR)/omim_relevant_signature.txt
	$(call generate_module,omim)
	

$(IMPORTDIR)/ordo_import.owl: $(MIRRORDIR)/ordo.owl $(TMPDIR)/ordo_relevant_signature.txt config/properties.txt
	$(ROBOT) merge -i $(MIRRORDIR)/ordo.owl \
		query \
			--update ../sparql/fix_deprecated.ru \
			--update ../sparql/fix_complex_reification.ru \
			--update ../sparql/fix_xref_prefixes.ru \
			--update ../sparql/ordo-construct-subclass-from-part-of.ru \
			--update ../sparql/ordo-construct-subsets.ru \
			--update ../sparql/ordo-construct-d2g.ru \
		filter -T $(TMPDIR)/ordo_relevant_signature.txt --trim false \
		remove -T config/properties.txt --select complement --select properties --trim true \
		rename --mappings config/property-map-1.sssom.tsv --allow-missing-entities true \
		rename --mappings config/property-map-2.sssom.tsv --allow-missing-entities true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/ordo.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/ordo.owl -o $@

$(IMPORTDIR)/ncit_import.owl: $(MIRRORDIR)/ncit.owl $(TMPDIR)/ncit_relevant_signature.txt
	$(ROBOT) remove -i $< -T $(TMPDIR)/ncit_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove --term "http://purl.obolibrary.org/obo/NCIT_C179199" --axioms "equivalent" \
		annotate --ontology-iri $(URIBASE)/mondo/sources/ncit.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/ncit.owl -o $@

$(IMPORTDIR)/doid_import.owl: $(MIRRORDIR)/doid.owl $(TMPDIR)/doid_relevant_signature.txt
	$(call generate_module,doid)

$(IMPORTDIR)/icd10cm_import.owl: $(MIRRORDIR)/icd10cm.owl $(TMPDIR)/icd10cm_relevant_signature.txt
	$(call generate_module,icd10cm)

$(IMPORTDIR)/icd10who_import.owl: $(MIRRORDIR)/icd10who.owl $(TMPDIR)/icd10who_relevant_signature.txt
	$(call generate_module,icd10who)
