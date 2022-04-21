## Customize Makefile settings for mondo-ingest
## 
## If you need to customize your Makefile, make
## changes here rather than in the main Makefile

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

# This section is concerned with transforming the incoming sources into the
# Monarch Ingest schema.

$(IMPORTDIR)/omim_import.owl: $(MIRRORDIR)/omim.owl $(TMPDIR)/omim_relevant_signature.txt
	if [ $(IMP) = true ]; then $(ROBOT) remove -i $< --select imports \
		remove -T $(TMPDIR)/omim_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix_hgnc_mappings.ru \
			--update ../sparql/fix_deprecated.ru \
			--update ../sparql/fix_complex_reification.ru \
		annotate --ontology-iri $(URIBASE)/mondo/sources/omim.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/omim.owl -o $@; fi


$(IMPORTDIR)/ordo_import.owl: $(MIRRORDIR)/ordo.owl $(TMPDIR)/ordo_relevant_signature.txt config/properties.txt
	$(ROBOT) remove -i $(MIRRORDIR)/ordo.owl --select imports \
		merge \
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
	if [ $(IMP) = true ]; then $(ROBOT) remove -i $< --select imports \
		remove -T $(TMPDIR)/ncit_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T config/properties.txt --select complement --select properties --trim true \
		remove --term "http://purl.obolibrary.org/obo/NCIT_C179199" --axioms "equivalent" \
		annotate --ontology-iri $(URIBASE)/mondo/sources/ncit.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/ncit.owl -o $@; fi


$(IMPORTDIR)/doid_import.owl: $(MIRRORDIR)/doid.owl $(TMPDIR)/doid_relevant_signature.txt
	if [ $(IMP) = true ]; then $(ROBOT) remove -i $< --select imports \
		remove -T $(TMPDIR)/doid_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix_hgnc_mappings.ru \
			--update ../sparql/fix_deprecated.ru \
			--update ../sparql/fix_complex_reification.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/doid.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/doid.owl -o $@; fi


$(IMPORTDIR)/icd10cm_import.owl: $(MIRRORDIR)/icd10cm.owl $(TMPDIR)/icd10cm_relevant_signature.txt
	if [ $(IMP) = true ]; then $(ROBOT) remove -i $< --select imports \
		remove -T $(TMPDIR)/icd10cm_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T $(TMPDIR)/icd10cm_relevant_signature.txt --select individuals \
		remove --term "http://www.w3.org/2004/02/skos/core#notation" \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix_hgnc_mappings.ru \
			--update ../sparql/fix_deprecated.ru \
			--update ../sparql/fix_complex_reification.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/icd10cm.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/icd10cm.owl -o $@; fi

$(IMPORTDIR)/icd10who_import.owl: $(MIRRORDIR)/icd10who.owl $(TMPDIR)/icd10who_relevant_signature.txt
	if [ $(IMP) = true ]; then $(ROBOT) remove -i $< --select imports \
		remove -T $(TMPDIR)/icd10who_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T $(TMPDIR)/icd10who_relevant_signature.txt --select individuals \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix_hgnc_mappings.ru \
			--update ../sparql/fix_deprecated.ru \
			--update ../sparql/fix_complex_reification.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/icd10who.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/icd10who.owl -o $@; fi

$(COMPONENTSDIR)/merged.owl: $(IMPORT_OWL_FILES)
	if [ $(IMP) = true ]; then $(ROBOT) merge $(patsubst %, -i %, $(IMPORT_OWL_FILES)) \
		annotate --ontology-iri $(URIBASE)/mondo/sources/merged.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/merged.owl -o $@; fi

#################
# Documentation #
#################
SOURCE_DOC_TEMPLATE=config/source_documentation.md.j2
ALL_SOURCE_DOCS=$(foreach n,$(IMPORTS), ../../docs/sources/$(n).md)

../../docs/sources/:
	mkdir -p $@

../../docs/sources/%.md: metadata/%.yml | ../../docs/sources/
	j2 "$(SOURCE_DOC_TEMPLATE)" $< > $@

documentation: $(ALL_SOURCE_DOCS)
