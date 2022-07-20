## Customize Makefile settings for mondo-ingest
## 
## If you need to customize your Makefile, make
## changes here rather than in the main Makefile
.PHONY: deploy-mondo-ingest build-mondo-ingest documentation mappings update-jinja-sparql-queries \
report-mapping-annotations

####################################
### Standard constants #############
####################################
MAPPINGSDIR=../mappings
####################################
### Relevant signature #############
####################################

# This section is concerned with identifiying 
# the entities of interest that 
# should be imported from the source

# Obtains the entities of interest from an ontology, as specified in a bespoke sparql query (bespoke
# for that ontology).
$(TMPDIR)/%_relevant_signature.txt: component-download-%.owl | $(TMPDIR)
	if [ $(COMP) = true ]; then $(ROBOT) query -i "$(TMPDIR)/$<.owl" -q "../sparql/$*-relevant-signature.sparql" $@; fi
.PRECIOUS: $(TMPDIR)/%_relevant_signature.txt

### ORDO needs to be structurally changed before the query can be run..
$(TMPDIR)/ordo_relevant_signature.txt: component-download-ordo.owl | $(TMPDIR)
	if [ $(COMP) = true ]; then $(ROBOT) query -i $(TMPDIR)/$<.owl --update ../sparql/ordo-construct-subclass-from-part-of.ru \
		query -q "../sparql/ordo-relevant-signature.sparql" $@; fi
.PRECIOUS: $(TMPDIR)/ordo_relevant_signature.txt

#######################################
### Ingest Components #################
#######################################

# This section is concerned with transforming the incoming sources into the
# Monarch Ingest schema.
# https://github.com/monarch-initiative/omim/issues/60
$(COMPONENTSDIR)/omim.owl: $(TMPDIR)/omim_relevant_signature.txt
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-omim.owl.owl --select imports \
		remove -T $(TMPDIR)/omim_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T config/remove.txt --axioms equivalent \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix_hgnc_mappings.ru \
			--update ../sparql/fix_deprecated.ru \
			--update ../sparql/fix_complex_reification.ru \
			--update ../sparql/fix_illegal_punning_omim.ru \
		annotate --ontology-iri $(URIBASE)/mondo/sources/omim.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/omim.owl -o $@; fi

$(COMPONENTSDIR)/ordo.owl: $(TMPDIR)/ordo_relevant_signature.txt config/properties.txt
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-ordo.owl.owl --select imports \
		merge \
		query \
			--update ../sparql/fix_deprecated.ru \
			--update ../sparql/fix_complex_reification.ru \
			--update ../sparql/fix_xref_prefixes.ru \
			--update ../sparql/ordo-construct-subclass-from-part-of.ru \
			--update ../sparql/ordo-construct-subsets.ru \
			--update ../sparql/ordo-construct-d2g.ru \
			--update ../sparql/ordo-replace-annotation-based-mappings.ru \
		filter -T $(TMPDIR)/ordo_relevant_signature.txt --trim false \
		remove -T config/properties.txt --select complement --select properties --trim true \
		rename --mappings config/property-map-1.sssom.tsv --allow-missing-entities true \
		rename --mappings config/property-map-2.sssom.tsv --allow-missing-entities true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/ordo.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/ordo.owl -o $@; fi

$(COMPONENTSDIR)/ncit.owl: $(TMPDIR)/ncit_relevant_signature.txt
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-ncit.owl.owl --select imports \
		remove -T $(TMPDIR)/ncit_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T config/properties.txt --select complement --select properties --trim true \
		remove --term "http://purl.obolibrary.org/obo/NCIT_C179199" --axioms "equivalent" \
		annotate --ontology-iri $(URIBASE)/mondo/sources/ncit.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/ncit.owl -o $@; fi

$(COMPONENTSDIR)/doid.owl: $(TMPDIR)/doid_relevant_signature.txt
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-doid.owl.owl --select imports \
		remove -T $(TMPDIR)/doid_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix_hgnc_mappings.ru \
			--update ../sparql/fix_deprecated.ru \
			--update ../sparql/fix_complex_reification.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/doid.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/doid.owl -o $@; fi

ICD10CM_URL="https://data.bioontology.org/ontologies/ICD10CM/submissions/21/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb"

component-download-icd10cm.owl: | $(TMPDIR)
	if [ $(MIR) = true ]; then wget $(ICD10CM_URL) -O $(TMPDIR)/icd10cm.tmp.owl && $(ROBOT) remove -i $(TMPDIR)/icd10cm.tmp.owl --select imports \
	annotate --ontology-iri $(ONTBASE)/$@ $(ANNOTATE_ONTOLOGY_VERSION) -o $(TMPDIR)/$@.owl; fi

$(COMPONENTSDIR)/icd10cm.owl: $(TMPDIR)/icd10cm_relevant_signature.txt
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-icd10cm.owl.owl --select imports \
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

$(COMPONENTSDIR)/icd10who.owl: $(TMPDIR)/icd10who_relevant_signature.txt
	if [ $(COMP) = true ] ; then $(ROBOT) remove -i $(TMPDIR)/component-download-icd10who.owl.owl --select imports \
		remove -T $(TMPDIR)/icd10who_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T $(TMPDIR)/icd10who_relevant_signature.txt --select individuals \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix_hgnc_mappings.ru \
			--update ../sparql/fix_deprecated.ru \
			--update ../sparql/fix_complex_reification.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/icd10who.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/icd10who.owl -o $@; fi

$(ONT)-full.owl: $(SRC) $(OTHER_SRC) $(IMPORT_FILES)
	$(ROBOT) merge $(patsubst %, -i %, $^) \
		reason --reasoner ELK --equivalent-classes-allowed asserted-only --exclude-tautologies structural \
		relax \
		reduce -r ELK \
		$(SHARED_ROBOT_COMMANDS) annotate --ontology-iri $(ONTBASE)/$@ $(ANNOTATE_ONTOLOGY_VERSION) --output $@.tmp.owl && mv $@.tmp.owl $@

ALL_COMPONENT_IDS=$(strip $(patsubst components/%.owl,%, $(OTHER_SRC)))

#################
# Mappings ######
#################

.PHONY: sssom
sssom:
	python3 -m pip install --upgrade pip setuptools && python3 -m pip install --upgrade --force-reinstall git+https://github.com/mapping-commons/sssom-py.git@master

ALL_MAPPINGS=$(foreach n,$(ALL_COMPONENT_IDS), ../mappings/$(n).sssom.tsv)

$(TMPDIR)/component-%.json: components/%.owl
	$(ROBOT) convert -i $< -f json -o $@
.PRECIOUS: $(TMPDIR)/component-%.json

MONDO_SSSOM_CONFIG_URL=https://raw.githubusercontent.com/monarch-initiative/mondo/master/src/ontology/metadata/mondo.sssom.config.yml

metadata/mondo.sssom.config.yml:
	wget $(MONDO_SSSOM_CONFIG_URL) -O $@

../mappings/%.sssom.tsv: $(TMPDIR)/component-%.json metadata/mondo.sssom.config.yml
	sssom parse $< -I obographs-json --prefix-map-mode merged -m metadata/mondo.sssom.config.yml -o $@

../mappings/ordo.sssom.tsv: $(TMPDIR)/component-ordo.json
	sssom parse $< -I obographs-json --prefix-map-mode merged -m metadata/ordo.metadata.sssom.yml -o $@

../mappings/doid.sssom.tsv: $(TMPDIR)/component-doid.json
	sssom parse $< -I obographs-json --prefix-map-mode merged -m metadata/doid.metadata.sssom.yml -o $@

../mappings/omim.sssom.tsv: $(TMPDIR)/component-omim.json
	sssom parse $< -I obographs-json --prefix-map-mode merged -m metadata/omim.metadata.sssom.yml -o $@

mappings: sssom $(ALL_MAPPINGS)

#################
# Utils #########
#################
# Documentation for this commands in this section is in: `docs/developer/ordo.md`

report-mapping-annotations:
	python3 $(SCRIPTSDIR)/ordo_mapping_annotations/report_mapping_annotations.py

update-jinja-sparql-queries:
	python3 $(SCRIPTSDIR)/ordo_mapping_annotations/create_sparql__ordo_replace_annotation_based_mappings.py
	python3 $(SCRIPTSDIR)/ordo_mapping_annotations/create_sparql__ordo_mapping_annotations_violation.py

#################
# Documentation #
#################
SOURCE_DOC_TEMPLATE=config/source_documentation.md.j2
SOURCE_METRICS_TEMPLATE=config/source_metrics.md.j2
ALL_SOURCE_DOCS=$(foreach n,$(ALL_COMPONENT_IDS), ../../docs/sources/$(n).md)
ALL_METRICS_DOCS=$(foreach n,$(ALL_COMPONENT_IDS), ../../docs/metrics/$(n).md)
ALL_DOCS=$(ALL_SOURCE_DOCS) $(ALL_METRICS_DOCS)

../../docs/sources/ ../../docs/metrics/ ../mappings/:
	mkdir -p $@

../../docs/sources/%.md: metadata/%.yml | ../../docs/sources/
	j2 "$(SOURCE_DOC_TEMPLATE)" $< > $@

PREFIXES_METRICS=--prefix 'OMIM: http://omim.org/entry/' \
	--prefix 'CHR: http://purl.obolibrary.org/obo/CHR_' \
	--prefix 'UMLS: http://linkedlifedata.com/resource/umls/id/' \
	--prefix 'HGNC: https://www.genenames.org/data/gene-symbol-report/\#!/hgnc_id/' \
	--prefix 'biolink: https://w3id.org/biolink/vocab/'

metadata/%-metrics.json: components/%.owl
	$(ROBOT) measure $(PREFIXES_METRICS) -i components/$*.owl --format json --metrics extended --output $@
.PRECIOUS: metadata/%-metrics.json

../../docs/metrics/%.md: metadata/%-metrics.json | ../../docs/metrics/
	j2 "$(SOURCE_METRICS_TEMPLATE)" metadata/$*-metrics.json > $@

j2:
	pip install j2cli j2cli[yaml]

documentation: j2 $(ALL_DOCS)

build-mondo-ingest:
	$(MAKE) refresh-imports
	$(MAKE) documentation
	$(MAKE) mappings
	$(MAKE) prepare_release

DEPLOY_ASSETS_MONDO_INGEST=$(OTHER_SRC) $(ALL_MAPPINGS) ../../mondo-ingest.owl ../../mondo-ingest.obo

deploy-mondo-ingest:
	@test $(GHVERSION)
	ls -alt $(DEPLOY_ASSETS_MONDO_INGEST)
	gh release create $(GHVERSION) --notes "TBD." --title "$(GHVERSION)" --draft $(DEPLOY_ASSETS_MONDO_INGEST)

tmp/mondo-ingest.owl:
	wget https://github.com/monarch-initiative/mondo-ingest/releases/latest/download/mondo-ingest.owl -O $@

tmp/mondo.owl:
	wget http://purl.obolibrary.org/obo/mondo.owl -O $@

tmp/mondo.sssom.tsv:
	wget http://purl.obolibrary.org/obo/mondo/mappings/mondo.sssom.tsv -O $@

tmp/mondo.sssom.ttl: tmp/mondo.sssom.tsv
	sssom convert $< -O rdf -o $@

# Merge Mondo, precise mappings and mondo-ingest into one coherent whole for the purpose of querying.

tmp/merged.owl: tmp/mondo.owl tmp/mondo-ingest.owl tmp/mondo.sssom.ttl
	$(ROBOT) merge -i tmp/mondo.owl -i tmp/mondo-ingest.owl -i tmp/mondo.sssom.ttl -o $@

$(REPORTDIR)/mondo_ordo_unsupported_subclass.tsv: ../sparql/mondo-ordo-unsupported-subclass.sparql
	$(ROBOT) query -i tmp/merged.owl --query $< $@

.PHONY: mondo-ordo-subclass
mondo-ordo-subclass: $(REPORTDIR)/mondo_ordo_unsupported_subclass.tsv

reports/mirror_signature-%.tsv: component-download-%.owl
	$(ROBOT) query -i $(TMPDIR)/$<.owl --query ../sparql/classes.sparql $@

reports/component_signature-%.tsv: components/%.owl
	$(ROBOT) query -i $< --query ../sparql/classes.sparql $@

ALL_MIRROR_SIGNTAURE_REPORTS=$(foreach n,$(ALL_COMPONENT_IDS), reports/component_signature-$(n).tsv)
ALL_COMPONENT_SIGNTAURE_REPORTS=$(foreach n,$(ALL_COMPONENT_IDS), reports/mirror_signature-$(n).tsv)

.PHONY: signature_reports
signature_reports: $(ALL_MIRROR_SIGNTAURE_REPORTS) $(ALL_COMPONENT_SIGNTAURE_REPORTS)
	echo "Finished running signature reports.."

#############################
#### Lexical matching #######
#############################

tmp/merged.db: tmp/merged.owl
	semsql make $@

mappings/mondo-sources-all-lexical.sssom.tsv: $(SCRIPTSDIR)/match-mondo-sources-all-lexical.py 
	python $^ run tmp/merged.db -c metadata/mondo.sssom.config.yml  -o $@
	# The $^ includes the python script, basically all paramters after the colon :

lexical_matches: mappings/mondo-sources-all-lexical.sssom.tsv
