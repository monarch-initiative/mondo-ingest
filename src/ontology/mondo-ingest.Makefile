## Customize Makefile settings for mondo-ingest
## 
## If you need to customize your Makefile, make changes here rather than in the main Makefile
.PHONY: build-mondo-ingest deploy-mondo-ingest documentation excluded-xrefs-in-mondo mappings \
report-mapping-annotations slurp-% slurp-all update-jinja-sparql-queries exclusions-%

####################################
### Standard constants #############
####################################

MAPPINGSDIR=../mappings
SKIP_HUGE=false

####################################
### Relevant signature #############
####################################
# This section is concerned with identifiying the entities of interest that should be imported from the source.
# Obtains the entities of interest from an ontology, as specified in a bespoke sparql query (bespoke for that ontology).
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
# Illegal punning on some properties #60: https://github.com/monarch-initiative/omim/issues/60
# todo: what does this have to do with #60 exactly? Does it address it? can that issue be closed?
$(COMPONENTSDIR)/omim.owl: $(TMPDIR)/omim_relevant_signature.txt | component-download-omim.owl
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-omim.owl.owl --select imports \
		rename --mappings config/property-map-1.sssom.tsv --allow-missing-entities true \
		rename --mappings config/property-map-2.sssom.tsv --allow-missing-entities true \
		remove -T $(TMPDIR)/omim_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T config/remove.txt --axioms equivalent \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/fix_hgnc_mappings.ru \
			--update ../sparql/fix_complex_reification.ru \
			--update ../sparql/fix_illegal_punning_omim.ru \
		annotate --ontology-iri $(URIBASE)/mondo/sources/omim.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/omim.owl -o $@; fi

$(COMPONENTSDIR)/ordo.owl: $(TMPDIR)/ordo_relevant_signature.txt config/properties.txt | component-download-ordo.owl
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-ordo.owl.owl --select imports \
		merge \
		rename --mappings config/property-map-1.sssom.tsv --allow-missing-entities true \
		rename --mappings config/property-map-2.sssom.tsv --allow-missing-entities true \
		query \
			--update ../sparql/fix_partof.ru \
			--update ../sparql/fix_deprecated.ru \
			--update ../sparql/fix_complex_reification.ru \
			--update ../sparql/fix_xref_prefixes.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/ordo-construct-subclass-from-part-of.ru \
			--update ../sparql/ordo-construct-subsets.ru \
			--update ../sparql/ordo-construct-d2g.ru \
			--update ../sparql/ordo-replace-annotation-based-mappings.ru \
		filter -T $(TMPDIR)/ordo_relevant_signature.txt --trim false \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/ordo.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/ordo.owl -o $@; fi

$(COMPONENTSDIR)/ncit.owl: $(TMPDIR)/ncit_relevant_signature.txt | component-download-ncit.owl
	if [ $(SKIP_HUGE) = false ] && [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-ncit.owl.owl --select imports \
		rename --mappings config/property-map-1.sssom.tsv --allow-missing-entities true \
		rename --mappings config/property-map-2.sssom.tsv --allow-missing-entities true \
		query --update ../sparql/rm_xref_by_prefix.ru \
		remove -T $(TMPDIR)/ncit_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T config/properties.txt --select complement --select properties --trim true \
		remove --term "http://purl.obolibrary.org/obo/NCIT_C179199" --axioms "equivalent" \
		annotate --ontology-iri $(URIBASE)/mondo/sources/ncit.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/ncit.owl -o $@; fi

$(COMPONENTSDIR)/doid.owl: $(TMPDIR)/doid_relevant_signature.txt | component-download-doid.owl
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-doid.owl.owl --select imports \
		rename --mappings config/property-map-1.sssom.tsv --allow-missing-entities true \
		rename --mappings config/property-map-2.sssom.tsv --allow-missing-entities true \
		remove -T $(TMPDIR)/doid_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix_hgnc_mappings.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/fix_complex_reification.ru \
			--update ../sparql/rm_xref_by_prefix.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/doid.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/doid.owl -o $@; fi

ICD10CM_URL="https://data.bioontology.org/ontologies/ICD10CM/submissions/22/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb"

# This preprocessing is necessary, because the bioportal version of ncit accidentally 
# puns ICD10 terms to be individuals and classes at the same time
# the remove step needs to run _before_ the first time the OWL API serialises the file, as 
# The injected declaration axioms makes it very hard to remove the
# Axioms that cause the codes to be individuals as well
component-download-icd10cm.owl: | $(TMPDIR)
	if [ $(MIR) = true ]; then wget $(ICD10CM_URL) -O $(TMPDIR)/icd10cm.tmp.owl && $(ROBOT) remove -i $(TMPDIR)/icd10cm.tmp.owl --select imports \
		remove -T config/remove_properties.txt \
		annotate --ontology-iri $(ONTBASE)/$@ $(ANNOTATE_ONTOLOGY_VERSION) -o $(TMPDIR)/$@.owl; fi

$(COMPONENTSDIR)/icd10cm.owl: $(TMPDIR)/icd10cm_relevant_signature.txt | component-download-icd10cm.owl
	if [ $(COMP) = true ]; then $(ROBOT) merge -i $(TMPDIR)/component-download-icd10cm.owl.owl \
		rename --mappings config/property-map-1.sssom.tsv --allow-missing-entities true \
		rename --mappings config/property-map-2.sssom.tsv --allow-missing-entities true \
		remove -T $(TMPDIR)/icd10cm_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T $(TMPDIR)/icd10cm_relevant_signature.txt --select individuals \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/fix_hgnc_mappings.ru \
			--update ../sparql/fix_complex_reification.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/icd10cm.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/icd10cm.owl -o $@; fi

$(COMPONENTSDIR)/icd10who.owl: $(TMPDIR)/icd10who_relevant_signature.txt | component-download-icd10who.owl
	if [ $(COMP) = true ] ; then $(ROBOT) remove -i $(TMPDIR)/component-download-icd10who.owl.owl --select imports \
		rename --mappings config/property-map-1.sssom.tsv --allow-missing-entities true \
		rename --mappings config/property-map-2.sssom.tsv --allow-missing-entities true \
		remove -T $(TMPDIR)/icd10who_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T $(TMPDIR)/icd10who_relevant_signature.txt --select individuals \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/fix_hgnc_mappings.ru \
			--update ../sparql/fix_complex_reification.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/icd10who.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/icd10who.owl -o $@; fi

$(ONT)-full.owl: $(SRC) $(OTHER_SRC) $(IMPORT_FILES)
	$(ROBOT) merge $(patsubst %, -i %, $^) \
		reason --reasoner ELK --equivalent-classes-allowed asserted-only --exclude-tautologies structural \
		relax \
		reduce -r ELK \
		$(SHARED_ROBOT_COMMANDS) annotate --ontology-iri $(ONTBASE)/$@ $(ANNOTATE_ONTOLOGY_VERSION) --output $@.tmp.owl && mv $@.tmp.owl $@

ALL_COMPONENT_IDS=$(strip $(patsubst $(COMPONENTSDIR)/%.owl,%, $(OTHER_SRC)))

#################
### Mappings ####
#################
#.PHONY: sssom
#sssom:
#	python3 -m pip install --upgrade pip setuptools && python3 -m pip install --upgrade --force-reinstall git+https://github.com/mapping-commons/sssom-py.git@master

.PHONY: dependencies
dependencies:
	python3 -m pip install --upgrade pip setuptools && python3 -m pip install --upgrade semsql==0.3.2 oaklib

ALL_MAPPINGS=$(foreach n,$(ALL_COMPONENT_IDS), ../mappings/$(n).sssom.tsv)

$(TMPDIR)/component-%.json: $(COMPONENTSDIR)/%.owl
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

mappings: $(ALL_MAPPINGS)

####################################
##### Mapping progress monitor #####
####################################

.PHONY: mapping-progress-report
mapping-progress-report: unmapped-terms-tables unmapped-terms-docs

.PHONY: unmapped-terms-docs
unmapped-terms-docs: $(foreach n,$(ALL_COMPONENT_IDS), reports/$(n)_unmapped_terms.tsv)
	python3 $(SCRIPTSDIR)/unmapped_docs.py

.PHONY: unmapped-terms-tables
unmapped-terms-tables: $(foreach n,$(ALL_COMPONENT_IDS), reports/$(n)_mapping_status.tsv)

$(REPORTDIR)/%_mapping_status.tsv $(REPORTDIR)/%_unmapped_terms.tsv: $(REPORTDIR)/%_term_exclusions.txt $(TMPDIR)/mondo.sssom.tsv metadata/%.yml $(COMPONENTSDIR)/%.db
	python3 $(SCRIPTSDIR)/unmapped_tables.py \
	--exclusions-path $(REPORTDIR)/$*_term_exclusions.txt \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--onto-config-path metadata/$*.yml \
	--db-path $(COMPONENTSDIR)/$*.db \
	--outpath-simple $(REPORTDIR)/$*_unmapped_terms.tsv \
	--outpath-full $(REPORTDIR)/$*_mapping_status.tsv

#################
##### Utils #####
#################
# Deprecated goal. Here for future reference.
report-mapping-annotations:
	python3 $(SCRIPTSDIR)/ordo_mapping_annotations/report_mapping_annotations.py

update-jinja-sparql-queries:
	python3 $(SCRIPTSDIR)/ordo_mapping_annotations/create_sparql__ordo_replace_annotation_based_mappings.py
	python3 $(SCRIPTSDIR)/ordo_mapping_annotations/create_sparql__ordo_mapping_annotations_violation.py

#################
### Exclusions ##
#################
# Exclusions: by ontology
$(REPORTDIR)/%_term_exclusions.txt $(REPORTDIR)/%_exclusion_reasons.robot.template.tsv: config/%_exclusions.tsv component-download-%.owl $(REPORTDIR)/mirror_signature-%.tsv $(REPORTDIR)/component_signature-%.tsv metadata/%.yml
	python3 $(SCRIPTSDIR)/exclusion_table_creation.py \
	--select-intensional-exclusions-path config/$*_exclusions.tsv \
	--onto-path $(TMPDIR)/component-download-$*.owl.owl \
	--mirror-signature-path $(REPORTDIR)/mirror_signature-$*.tsv \
	--component-signature-path $(REPORTDIR)/component_signature-$*.tsv \
	--config-path metadata/$*.yml \
	--outpath-txt $(REPORTDIR)/$*_term_exclusions.txt \
	--outpath-robot-template-tsv $(REPORTDIR)/$*_exclusion_reasons.robot.template.tsv

$(REPORTDIR)/%_exclusion_reasons.ttl: component-download-%.owl $(REPORTDIR)/%_exclusion_reasons.robot.template.tsv
	$(ROBOT) template --input $(TMPDIR)/component-download-$*.owl.owl --add-prefixes config/context.json --template $(REPORTDIR)/$*_exclusion_reasons.robot.template.tsv --output $(REPORTDIR)/$*_exclusion_reasons.ttl

$(REPORTDIR)/%_excluded_terms_in_mondo_xrefs.tsv $(REPORTDIR)/%_excluded_terms_in_mondo_xrefs_summary.tsv: $(TMPDIR)/mondo.sssom.tsv tmp/mondo.owl metadata/%.yml $(REPORTDIR)/component_signature-%.tsv $(REPORTDIR)/mirror_signature-%.tsv
	python3 $(RELEASEDIR)/src/analysis/problematic_exclusions.py \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--onto-path $(TMPDIR)/component-download-$*.owl.owl \
	--onto-config-path metadata/$*.yml \
	--mirror-signature-path $(REPORTDIR)/mirror_signature-$*.tsv \
	--component-signature-path $(REPORTDIR)/component_signature-$*.tsv \
	--outpath $@

# Exclusions: all artefacts for single ontology
exclusions-%:
	$(MAKE) $(REPORTDIR)/$*_term_exclusions.txt
	$(MAKE) $(REPORTDIR)/$*_exclusion_reasons.ttl
	$(MAKE) $(REPORTDIR)/$*_excluded_terms_in_mondo_xrefs.tsv

exclusions-all:
	$(MAKE) $(foreach n,$(ALL_COMPONENT_IDS), exclusions-$(n))

# Exclusions: running for all ontologies
$(REPORTDIR)/excluded_terms.txt $(REPORTDIR)/exclusion_reasons.robot.template.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n)_term_exclusions.txt)
	cat $(REPORTDIR)/*_term_exclusions.txt > $(REPORTDIR)/excluded_terms.txt; \
	awk '(NR == 1) || (NR == 2) || (FNR > 2)' $(REPORTDIR)/*_exclusion_reasons.robot.template.tsv > $(REPORTDIR)/exclusion_reasons.robot.template.tsv

$(REPORTDIR)/excluded_terms.ttl: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n)_exclusion_reasons.ttl)
	$(ROBOT) merge $(patsubst %, -i %, $^) -o $@

# todo: the merged _summary.tsv has a column `filename` on the right. would be better if it was named `ontology` and was on the left, and was sorted by most->least terms.
$(REPORTDIR)/excluded_terms_in_mondo_xrefs.tsv $(REPORTDIR)/excluded_terms_in_mondo_xrefs_summary.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n)_excluded_terms_in_mondo_xrefs.tsv)
	awk '(NR == 1) || (FNR > 1)' $(REPORTDIR)/*_excluded_terms_in_mondo_xrefs.tsv > $@
	@awk -v OFS='\t' 'NR == 1 { print $$0, "filename" } FNR > 1 { print $$0, FILENAME }' \
	reports/*_excluded_terms_in_mondo_xrefs_summary.tsv \
	> $(REPORTDIR)/excluded_terms_in_mondo_xrefs_summary.tsv

excluded-xrefs-in-mondo: $(REPORTDIR)/excluded_terms_in_mondo_xrefs.tsv

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

metadata/%-metrics.json: $(COMPONENTSDIR)/%.owl
	$(ROBOT) measure $(PREFIXES_METRICS) -i $(COMPONENTSDIR)/$*.owl --format json --metrics extended --output $@
.PRECIOUS: metadata/%-metrics.json

../../docs/metrics/%.md: metadata/%-metrics.json | ../../docs/metrics/
	j2 "$(SOURCE_METRICS_TEMPLATE)" metadata/$*-metrics.json > $@

j2:
	pip install j2cli j2cli[yaml]

documentation: j2 $(ALL_DOCS) mapping-progress-report

build-mondo-ingest:
	$(MAKE) refresh-imports
	$(MAKE) exclusions-all
	$(MAKE) slurp-all
	$(MAKE) mappings
	$(MAKE) matches
	$(MAKE) mapped-deprecated-terms
	$(MAKE) mapping-progress-report
	$(MAKE) documentation
	$(MAKE) prepare_release

DEPLOY_ASSETS_MONDO_INGEST=$(OTHER_SRC) $(ALL_MAPPINGS) ../../mondo-ingest.owl ../../mondo-ingest.obo

deploy-mondo-ingest:
	@test $(GHVERSION)
	ls -alt $(DEPLOY_ASSETS_MONDO_INGEST)
	gh release create $(GHVERSION) --notes "TBD." --title "$(GHVERSION)" --draft $(DEPLOY_ASSETS_MONDO_INGEST)

USE_MONDO_RELEASE=false

tmp/mondo.owl:
	if [ $(USE_MONDO_RELEASE) = true ]; then wget http://purl.obolibrary.org/obo/mondo.owl -O $@; else cd $(TMPDIR) &&\
		rm -rf ./mondo/ &&\
		git clone --depth 1 https://github.com/monarch-initiative/mondo &&\
		cd mondo/src/ontology &&\
		make mondo.owl IMP=false MIR=false &&\
		cd ../../../../ &&\
		cp $(TMPDIR)/mondo/src/ontology/mondo.owl $@ &&\
		cp $(TMPDIR)/mondo/src/ontology/mappings/mondo.sssom.tsv $(TMPDIR)/mondo.sssom.tsv &&\
		rm -rf $(TMPDIR)/mondo/; fi

$(REPORTDIR)/mondo_ordo_unsupported_subclass.tsv: ../sparql/mondo-ordo-unsupported-subclass.sparql
	$(ROBOT) query -i tmp/merged.owl --query $< $@

.PHONY: mondo-ordo-subclass
mondo-ordo-subclass: $(REPORTDIR)/mondo_ordo_unsupported_subclass.tsv

reports/mirror_signature-mondo.tsv: tmp/mondo.owl
	$(ROBOT) query -i $< --query ../sparql/classes.sparql $@
	(head -n 1 $@ && tail -n +2 $@ | sort) > $@-temp
	mv $@-temp $@

reports/mirror_signature-ncit.tsv: $(COMPONENTSDIR)/ncit.db metadata/ncit.yml
	python3 $(SCRIPTSDIR)/mirror_signature_via_oak.py --db-path $(COMPONENTSDIR)/ncit.db --onto-config-path metadata/ncit.yml --outpath $@;\

reports/mirror_signature-%.tsv: component-download-%.owl
	$(ROBOT) query -i $(TMPDIR)/$<.owl --query ../sparql/classes.sparql $@
	(head -n 1 $@ && tail -n +2 $@ | sort) > $@-temp
	mv $@-temp $@

reports/component_signature-%.tsv: $(COMPONENTSDIR)/%.owl
	$(ROBOT) query -i $< --query ../sparql/classes.sparql $@
	(head -n 1 $@ && tail -n +2 $@ | sort) > $@-temp
	mv $@-temp $@

ALL_MIRROR_SIGNTAURE_REPORTS=$(foreach n,$(ALL_COMPONENT_IDS), reports/component_signature-$(n).tsv)
ALL_COMPONENT_SIGNTAURE_REPORTS=$(foreach n,$(ALL_COMPONENT_IDS), reports/mirror_signature-$(n).tsv)

.PHONY: signature_reports
signature_reports: $(ALL_MIRROR_SIGNTAURE_REPORTS) $(ALL_COMPONENT_SIGNTAURE_REPORTS)
	echo "Finished running signature reports.."

#############################
#### Lexical matching #######
#############################
# Official Mondo SSSOM Mappings
# - Doeesn't include: broad mappings
# - Comes from make tmp/mondo.owl

tmp/mondo.sssom.ttl: tmp/mondo.sssom.tsv
	sssom convert $< -O rdf -o $@

# Merge Mondo, precise mappings and mondo-ingest into one coherent whole for the purpose of querying.
tmp/merged.owl: tmp/mondo.owl mondo-ingest.owl tmp/mondo.sssom.ttl
	$(ROBOT) merge -i tmp/mondo.owl -i mondo-ingest.owl -i tmp/mondo.sssom.ttl  --add-prefixes config/context.json -o $@

tmp/merged.db: tmp/merged.owl
	@rm -f .template.db
	@rm -f .template.db.tmp
	RUST_BACKTRACE=full semsql make $@ -P config/prefixes.csv
	@rm -f .template.db
	@rm -f .template.db.tmp

../mappings/mondo-sources-all-lexical.sssom.tsv: $(SCRIPTSDIR)/match-mondo-sources-all-lexical.py tmp/merged.db
	python $< run tmp/merged.db -c metadata/mondo.sssom.config.yml -r config/mondo-match-rules.yaml -o $@

lexical-matches: ../mappings/mondo-sources-all-lexical.sssom.tsv

###################################
#### Lexmatch-SSSOM-compare #######
###################################
lexmatch/README.md: $(SCRIPTSDIR)/lexmatch-sssom-compare.py ../mappings/mondo-sources-all-lexical.sssom.tsv
	python $< extract_unmapped_matches --matches ../mappings/mondo-sources-all-lexical.sssom.tsv --output-dir lexmatch --summary $@

extract-unmapped-matches: lexmatch/README.md

.PHONY: matches
matches: lexical-matches extract-unmapped-matches

#############################
######### Analysis ##########
#############################
.PHONY: mapped-deprecated-terms
mapped-deprecated-terms: mapped-deprecated-terms-artefacts mapped-deprecated-terms-docs

.PHONY: mapped-deprecated-terms-docs
mapped-deprecated-terms-docs:
	python3 $(SCRIPTSDIR)/deprecated_in_mondo.py --docs

.PHONY: mapped-deprecated-terms-artefacts
mapped-deprecated-terms-artefacts: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n)_mapped_deprecated_terms.robot.template.tsv)

$(REPORTDIR)/%_mapped_deprecated_terms.robot.template.tsv: $(REPORTDIR)/%_mapping_status.tsv tmp/mondo.sssom.tsv
	python3 $(SCRIPTSDIR)/deprecated_in_mondo.py \
	--mondo-mappings-path tmp/mondo.sssom.tsv \
	--mapping-status-path $(REPORTDIR)/$*_mapping_status.tsv \
	--outpath $@

#############################
###### Slurp pipeline #######
#############################
# todo: What if the mirror was out of date, but there's already a .db file there, but it's not up to date?
# Related issues:
#  - icd10cm/icd10who ttl -> owl: https://github.com/monarch-initiative/mondo-ingest/issues/138
#  - No rule to make target 'mirror/ONTOLOGY.owl': https://github.com/monarch-initiative/mondo-ingest/issues/137
# Maybe solved now by using $(COMPONENTSDIR)/
$(COMPONENTSDIR)/%.db: $(COMPONENTSDIR)/%.owl
	@rm -f .template.db
	@rm -f .template.db.tmp
	RUST_BACKTRACE=full semsql make $@ -P config/prefixes.csv
	@rm -f .template.db
	@rm -f .template.db.tmp

slurp/:
	mkdir -p $@

# min-id: the next available Mondo ID
# todo: `pip install` stuff is temporarily here until we come up with a fix. otherwise docker won't work
slurp/%.tsv: $(COMPONENTSDIR)/%.owl $(TMPDIR)/mondo.sssom.tsv $(REPORTDIR)/%_term_exclusions.txt $(REPORTDIR)/mirror_signature-mondo.tsv | slurp/
#	pip install --upgrade -r $(RELEASEDIR)/requirements-unlocked.txt
	python3 $(SCRIPTSDIR)/migrate.py \
	--ontology-path $(COMPONENTSDIR)/$*.owl \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--onto-config-path metadata/$*.yml \
	--onto-exclusions-path reports/$*_term_exclusions.txt \
	--min-id 850056 \
	--max-id 999999 \
	--mondo-terms-path $(REPORTDIR)/mirror_signature-mondo.tsv \
	--slurp-dir-path slurp/ \
	--outpath $@

slurp-%:
	$(MAKE) slurp/$*.tsv -B

slurp-no-updates-%:
	$(MAKE) slurp/$*.tsv

# todo: re-use for loop for ids?: ALL_MIRROR_SIGNTAURE_REPORTS=$(foreach n,$(ALL_COMPONENT_IDS), reports/component_signature-$(n).tsv)
slurp-all-no-updates: slurp-no-updates-omim slurp-no-updates-doid slurp-no-updates-ordo slurp-no-updates-icd10cm slurp-no-updates-icd10who slurp-no-updates-ncit

# todo: re-use for loop for ids?: ALL_MIRROR_SIGNTAURE_REPORTS=$(foreach n,$(ALL_COMPONENT_IDS), reports/component_signature-$(n).tsv)
slurp-all: slurp-omim slurp-doid slurp-ordo slurp-icd10cm slurp-icd10who slurp-ncit

##################################
##### Utilities ###################
##################################

# $$data: This prints the help message from imported makefiles.
.PHONY: help
help:
	@echo "$$data"
	@echo "----------------------------------------"
	@echo "	Command reference: mondo-ingest"
	@echo "----------------------------------------"
	@echo "slurp/%.tsv and slurp-%"
	@echo "For a given ontology, determine all slurpable / migratable terms. That is, terms that are candidates for integration into Mondo.\n"
	@echo "slurp-all"
	@echo "Runs slurp / migrate for all ontologies.\n"
	@echo "extract-unmapped-matches"
	@echo "Determine all new matches across external ontologies.\n"
	# Lexical matches
	@echo "lexical-matches"
	@echo "Determine lexical matches across external ontologies.\n"
	# Mapping status
	@echo "reports/%_mapping_status.tsv"
	@echo "A table of all terms for ontology %, along with labels, and other columns is_excluded, is_mapped, is_deprecated.\n"
	@echo "reports/%_unmapped_terms.tsv"
	@echo "A table of unmapped terms for ontology % and their labels.\n"
	@echo "unmapped-terms-docs"
	@echo "Creates mapping progress report (docs/reports/unmapped.md) and pages for each ontology which list their umapped terms."
	@echo "mapping-progress-report"
	@echo "Creates mapping progress report (docs/reports/unmapped.md) and pages for each ontology which list their umapped terms. Also generates reports/%_mapping_status.tsv and reports/%_unmapped_terms.tsv for all ontologies.\n"
	@echo "reports/mirror_signature-%.tsv"
	@echo "A table with a single column '?term' which includes all of the class IRIs in an ontology.\n"
	@echo "reports/%_mapped_deprecated_terms.robot.template.tsv"
	@echo "A table of all of the deprecated terms from a given ontology that have existing mappings in Mondo.\n"
	@echo "mapped-deprecated-terms-artefacts"
	@echo "Creates a reports/%_mapped_deprecated_terms.robot.template.tsv for all ontologies.\n"
	@echo "mapped-deprecated-terms-docs"
	@echo "Creates a report of statistics for mapped deprecated terms (docs/reports/mapped_deprecated.md) and pages for each ontology which list their deprecated terms with existing xrefs in Mondo.\n"
	@echo "mapped-deprecated-terms"
	@echo "Creates a report of statistics for mapped deprecated terms (docs/reports/mapped_deprecated.md) and pages for each ontology which list their deprecated terms with existing xrefs in Mondo. Also creates a reports/%_mapped_deprecated_terms.robot.template.tsv for all ontologies.\n"
	@echo "reports/%_term_exclusions.txt"
	@echo "A simple list of terms to exclude from integration into Mondo from the given ontology.\n"
	@echo "reports/%_exclusion_reasons.robot.template.tsv"
	@echo "A robot template of terms to exclude from integration into Mondo from the given ontology.\n"
	@echo "reports/%_exclusion_reasons.ttl"
	@echo "A list of terms to exclude from integration into Mondo from the given ontology, in TTL format.\n"
	@echo "reports/%_excluded_terms_in_mondo_xrefs.tsv"
	@echo "A list of terms excluded from integration in Mondo that still have xrefs in Mondo.\n"
	@echo "excluded-xrefs-in-mondo and reports/excluded_terms_in_mondo_xrefs.tsv"
	@echo "Runs reports/%_excluded_terms_in_mondo_xrefs.tsv for all ontologies.\n"
	@echo "exclusions-%"
	@echo "Runs reports/%_term_exclusions.txt, reports/%_exclusion_reasons.ttl, and reports/%_excluded_terms_in_mondo_xrefs.tsv for a given ontology.\n"
	@echo "reports/excluded_terms.ttl"
	@echo "Runs reports/%_exclusion_reasons.ttl for all ontologies. and combines into a single file.\n"
	@echo "reports/excluded_terms.txt"
	@echo "Runs reports/%_term_exclusions.txt for all ontologies and combines into a single file.\n"
	@echo "reports/exclusion_reasons.robot.template.tsv"
	@echo "Runs reports/%_exclusion_reasons.robot.template.tsv for all ontologies and combines into a single file.\n"
	@echo "exclusions-all"
	@echo "Runs all exclusion artefacts for all ontologies.\n"
