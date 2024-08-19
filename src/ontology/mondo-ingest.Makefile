## Customize Makefile settings for mondo-ingest
## 
## If you need to customize your Makefile, make changes here rather than in the main Makefile
#
# todo's
#  todo #1. Several $(COMPONENTSDIR/*.owl goals have unnecessary operations: https://github.com/monarch-initiative/mondo-ingest/pull/299#discussion_r1187182707
#   - The line that references config/remove.txt looks like it only needs to be for OMIM
#   - omimps and hgnc_id SPARQL updates are probably just for OMIM as well
#  todo #2: $(COMPONENTSDIR)/%.db's vs mondo-ingest.db. We're using both, but it may be possible we only need to use one. I feel inclined towards the former, but the latter should result in faster builds.

####################################
### Standard constants #############
####################################
MAPPINGSDIR=../mappings
SKIP_HUGE=false

####################################
### Package management #############
####################################
.PHONY: pip-%
pip-%:
	 python3 -m pip install --upgrade $*

.PHONY: dependencies
dependencies: pip-pip pip-setuptools pip-oaklib pip-sssom pip-semsql

####################################
### General ########################
####################################
%.db: %.owl
	@rm -f $*.db
	@rm -f .template.db
	@rm -f .template.db.tmp
	@rm -f $*-relation-graph.tsv.gz
	RUST_BACKTRACE=full semsql make $*.db -P config/prefixes.csv
	@rm -f .template.db
	@rm -f .template.db.tmp
	@rm -f $*-relation-graph.tsv.gz
	@test -f $*.db || (echo "Error: File not found!" && exit 1)

.PRECIOUS: %.db

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
# todo: Illegal punning on some properties #60: https://github.com/monarch-initiative/omim/issues/60
#  - #60 needs to be fixed at source, but a workaround can probably be implemented in this goal
$(COMPONENTSDIR)/omim.owl: $(TMPDIR)/omim_relevant_signature.txt | component-download-omim.owl
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-omim.owl.owl --select imports \
		rename --mappings config/property-map.sssom.tsv --allow-missing-entities true --allow-duplicates true \
		remove -T $(TMPDIR)/omim_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T config/remove.txt --axioms equivalent \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/fix_illegal_punning_omim.ru \
			--update ../sparql/exact_syn_from_label.ru \
		annotate --ontology-iri $(URIBASE)/mondo/sources/omim.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/omim.owl -o $@; fi

# todo: See #1 at top of file
$(COMPONENTSDIR)/ordo.owl: $(TMPDIR)/ordo_relevant_signature.txt config/properties.txt | component-download-ordo.owl
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-ordo.owl.owl --select imports \
		merge \
		rename --mappings config/property-map.sssom.tsv --allow-missing-entities true --allow-duplicates true \
		query \
			--update ../sparql/fix_partof.ru \
			--update ../sparql/fix_deprecated.ru \
			--update ../sparql/fix_complex_reification_ordo.ru \
			--update ../sparql/fix_xref_prefixes.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/exact_syn_from_label.ru \
			--update ../sparql/ordo-construct-subclass-from-part-of.ru \
			--update ../sparql/ordo-construct-subsets.ru \
			--update ../sparql/ordo-construct-d2g.ru \
			--update ../sparql/ordo-replace-annotation-based-mappings.ru \
		remove -T $(TMPDIR)/ordo_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/ordo.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/ordo.owl -o $@; fi

$(COMPONENTSDIR)/ncit.owl: $(TMPDIR)/ncit_relevant_signature.txt | component-download-ncit.owl
	if [ $(SKIP_HUGE) = false ] && [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-ncit.owl.owl --select imports \
		rename --mappings config/property-map.sssom.tsv --allow-missing-entities true --allow-duplicates true \
		query \
			--update ../sparql/rm_xref_by_prefix.ru \
			--update ../sparql/exact_syn_from_label.ru \
		remove -T $(TMPDIR)/ncit_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T config/properties.txt --select complement --select properties --trim true \
		remove --term "http://purl.obolibrary.org/obo/NCIT_C179199" --axioms "equivalent" \
		annotate --ontology-iri $(URIBASE)/mondo/sources/ncit.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/ncit.owl -o $@; fi

# todo: See #1 at top of file
$(COMPONENTSDIR)/doid.owl: $(TMPDIR)/doid_relevant_signature.txt | component-download-doid.owl
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-doid.owl.owl --select imports \
		rename --mappings config/property-map.sssom.tsv --allow-missing-entities true --allow-duplicates true \
		remove -T $(TMPDIR)/doid_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix_mim.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/rm_xref_by_prefix.ru \
			--update ../sparql/fix_make_omim_exact.ru \
			--update ../sparql/exact_syn_from_label.ru \
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

# todo: See #1 at top of file
$(COMPONENTSDIR)/icd10cm.owl: $(TMPDIR)/icd10cm_relevant_signature.txt | component-download-icd10cm.owl
	if [ $(COMP) = true ]; then $(ROBOT) merge -i $(TMPDIR)/component-download-icd10cm.owl.owl \
		rename --mappings config/property-map.sssom.tsv --allow-missing-entities true --allow-duplicates true \
		remove -T $(TMPDIR)/icd10cm_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T $(TMPDIR)/icd10cm_relevant_signature.txt --select individuals \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/exact_syn_from_label.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/icd10cm.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/icd10cm.owl -o $@; fi

# todo: See #1 at top of file
$(COMPONENTSDIR)/icd10who.owl: $(TMPDIR)/icd10who_relevant_signature.txt | component-download-icd10who.owl
	if [ $(COMP) = true ] ; then $(ROBOT) remove -i $(TMPDIR)/component-download-icd10who.owl.owl --select imports \
		rename --mappings config/property-map.sssom.tsv --allow-missing-entities true --allow-duplicates true \
		remove -T $(TMPDIR)/icd10who_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T $(TMPDIR)/icd10who_relevant_signature.txt --select individuals \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/exact_syn_from_label.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/icd10who.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/icd10who.owl -o $@; fi

$(COMPONENTSDIR)/icd11foundation.owl: $(TMPDIR)/icd11foundation_relevant_signature.txt | component-download-icd11foundation.owl
	if [ $(COMP) = true ] ; then $(ROBOT) remove -i $(TMPDIR)/component-download-icd11foundation.owl.owl --select imports \
		rename --mappings config/property-map.sssom.tsv --allow-missing-entities true --allow-duplicates true \
		rename --mappings config/icd11foundation-property-map.sssom.tsv \
		remove -T $(TMPDIR)/icd11foundation_relevant_signature.txt --select complement --select "classes individuals" \
		remove -T $(TMPDIR)/icd11foundation_relevant_signature.txt --select individuals \
		query \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/exact_syn_from_label.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/icd11foundation.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/icd11foundation.owl -o $@; fi

$(COMPONENTSDIR)/gard.owl: $(TMPDIR)/gard_relevant_signature.txt | component-download-gard.owl
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/component-download-gard.owl.owl --select imports \
		remove -T $(TMPDIR)/gard_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		annotate --ontology-iri $(URIBASE)/mondo/sources/gard.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/gard.owl -o $@; fi

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
ALL_MAPPINGS=$(foreach n,$(ALL_COMPONENT_IDS), $(MAPPINGSDIR)/$(n).sssom.tsv)

$(TMPDIR)/component-%.json: $(COMPONENTSDIR)/%.owl
	$(ROBOT) convert -i $< -f json -o $@
.PRECIOUS: $(TMPDIR)/component-%.json

$(MAPPINGSDIR)/%.sssom.tsv:
	$(MAKE) $(TMPDIR)/component-$*.json metadata/mondo.sssom.config.yml
	sssom parse $(TMPDIR)/component-$*.json -I obographs-json --prefix-map-mode merged -m metadata/mondo.sssom.config.yml -o $@
	sssom sort $@ -o $@

$(MAPPINGSDIR)/ordo.sssom.tsv: $(TMPDIR)/component-ordo.json
	sssom parse $< -I obographs-json --prefix-map-mode merged -m metadata/ordo.metadata.sssom.yml -o $@
	sssom sort $@ -o $@

$(MAPPINGSDIR)/doid.sssom.tsv: $(TMPDIR)/component-doid.json
	sssom parse $< -I obographs-json --prefix-map-mode merged -m metadata/doid.metadata.sssom.yml -o $@
	sssom sort $@ -o $@

$(MAPPINGSDIR)/omim.sssom.tsv: $(TMPDIR)/component-omim.json
	sssom parse $< -I obographs-json --prefix-map-mode merged -m metadata/omim.metadata.sssom.yml -o $@
	sssom sort $@ -o $@

$(MAPPINGSDIR)/nando-mondo.sssom.tsv:
	@echo "$@ is manually curated"

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

$(REPORTDIR)/%_mapping_status.tsv $(REPORTDIR)/%_unmapped_terms.tsv: $(REPORTDIR)/%_term_exclusions.txt metadata/%.yml $(COMPONENTSDIR)/%.db
	$(MAKE) up-to-date-mondo.sssom.tsv
	python3 $(SCRIPTSDIR)/unmapped_tables.py \
	--exclusions-path $(REPORTDIR)/$*_term_exclusions.txt \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--onto-config-path metadata/$*.yml \
	--db-path $(COMPONENTSDIR)/$*.db \
	--outpath-simple $(REPORTDIR)/$*_unmapped_terms.tsv \
	--outpath-full $(REPORTDIR)/$*_mapping_status.tsv

unmapped/:
	mkdir -p $@

unmapped/%-unmapped.owl: $(COMPONENTSDIR)/%.owl reports/%_unmapped_terms.tsv | unmapped/
	cut -f 1 reports/$*_unmapped_terms.tsv | tail -n +2 > reports/$*_unmapped_terms.txt
	$(ROBOT) filter -i components/$*.owl -T reports/$*_unmapped_terms.txt -o $@
	rm reports/$*_unmapped_terms.txt

.PHONY: recreate-unmapped-components
recreate-unmapped-components: $(patsubst %, unmapped/%-unmapped.owl, $(ALL_COMPONENT_IDS))

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
.PRECIOUS: $(REPORTDIR)/%_exclusion_reasons.robot.template.tsv

$(REPORTDIR)/%_exclusion_reasons.ttl: component-download-%.owl $(REPORTDIR)/%_exclusion_reasons.robot.template.tsv
	$(ROBOT) template --input $(TMPDIR)/component-download-$*.owl.owl --add-prefixes config/context.json --template $(REPORTDIR)/$*_exclusion_reasons.robot.template.tsv --output $(REPORTDIR)/$*_exclusion_reasons.ttl

# todo: Should this also be a prereq $(TMPDIR)/component-download-$*.owl.owl? Perhaps worried about refreshing when not need to? But then we'd just use COMP=false if so?
$(REPORTDIR)/%_excluded_terms_in_mondo_xrefs.tsv $(REPORTDIR)/%_excluded_terms_in_mondo_xrefs_summary.tsv: metadata/%.yml $(REPORTDIR)/component_signature-%.tsv $(REPORTDIR)/mirror_signature-%.tsv
	$(MAKE) up-to-date-mondo.sssom.tsv
	python3 $(RELEASEDIR)/src/analysis/problematic_exclusions.py \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--onto-path $(TMPDIR)/component-download-$*.owl.owl \
	--onto-config-path metadata/$*.yml \
	--mirror-signature-path $(REPORTDIR)/mirror_signature-$*.tsv \
	--component-signature-path $(REPORTDIR)/component_signature-$*.tsv \
	--outpath $@

# Exclusions: all artefacts for single ontology
.PHONY: exclusions-%
exclusions-%: reports/%_exclusion_reasons.ttl reports/%_excluded_terms_in_mondo_xrefs.tsv  $(REPORTDIR)/%_term_exclusions.txt 
	@echo "$@ completed"

exclusions-all: $(foreach n,$(ALL_COMPONENT_IDS), exclusions-$(n))
	@echo "$@ completed"

# Exclusions: running for all ontologies
# todo: change '> $(REPORTDIR)/excluded_terms.txt' to '> $@' like in goal '$(REPORTDIR)/excluded_terms_in_mondo_xrefs.tsv'?
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

###################
## Documentation ##
###################
SOURCE_DOC_TEMPLATE=config/source_documentation.md.j2
SOURCE_METRICS_TEMPLATE=config/source_metrics.md.j2
ALL_SOURCE_DOCS=$(foreach n,$(ALL_COMPONENT_IDS), ../../docs/sources/$(n).md)
ALL_METRICS_DOCS=$(foreach n,$(ALL_COMPONENT_IDS), ../../docs/metrics/$(n).md)
ALL_DOCS=$(ALL_SOURCE_DOCS) $(ALL_METRICS_DOCS)

../../docs/sources/ ../../docs/metrics/ $(MAPPINGSDIR)/:
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

.PHONY: j2
j2:
	pip install j2cli j2cli[yaml]

.PHONY: documentation
documentation: j2 $(ALL_DOCS) unmapped-terms-docs mapped-deprecated-terms-docs slurp-docs


.PHONY: build-mondo-ingest
build-mondo-ingest:
	$(MAKE) refresh-imports exclusions-all slurp-all mappings matches \
		mapped-deprecated-terms mapping-progress-report \
		recreate-unmapped-components sync documentation \
		update-externally-managed-content \
		prepare_release
	@echo "Mondo Ingest has been fully completed"

.PHONY: build-mondo-ingest-no-imports
build-mondo-ingest-no-imports:
	$(MAKE_FAST) exclusions-all slurp-all mappings matches \
		mapped-deprecated-terms mapping-progress-report \
		recreate-unmapped-components sync documentation \
		update-externally-managed-content \
		prepare_release
	@echo "Mondo Ingest (fast) has been fully completed"

DEPLOY_ASSETS_MONDO_INGEST=$(OTHER_SRC) $(ALL_MAPPINGS) ../../mondo-ingest.owl ../../mondo-ingest.obo

.PHONY: deploy-mondo-ingest
deploy-mondo-ingest:
	@test $(GHVERSION)
	ls -alt $(DEPLOY_ASSETS_MONDO_INGEST)
	gh release create $(GHVERSION) --notes "TBD." --title "$(GHVERSION)" --draft $(DEPLOY_ASSETS_MONDO_INGEST)

USE_MONDO_RELEASE=false

# Builds tmp/mondo/ and rebuilds mondo.owl and mondo.sssom.tsv, and stores hash of latest commit of mondo repo main branch in tmp/mondo_repo_built
tmp/mondo_repo_built:
	if [ $(USE_MONDO_RELEASE) = true ]; then wget http://purl.obolibrary.org/obo/mondo.owl -O $@; else cd $(TMPDIR) &&\
		rm -rf ./mondo/ &&\
		git clone --depth 1 https://github.com/monarch-initiative/mondo &&\
		cd mondo/src/ontology &&\
		make mondo.owl mappings -B MIR=false IMP=false MIR=false &&\
		latest_hash=$$(git rev-parse origin/master) &&\
		echo "$$latest_hash" > $@ &&\
		cp $@ mappings/mondo.sssom.tsv mondo.owl ../../../; fi

# Triggers a refresh of tmp/mondo/ and a rebuild of mondo.owl and mondo.sssom.tsv, only if mondo repo main branch has new commits
.PHONY: refresh-mondo-clone
refresh-mondo-clone:
	@if [ ! -d tmp/mondo ]; then \
		$(MAKE) tmp/mondo_repo_built -B; \
	else \
		current_hash=$$(cat tmp/mondo_repo_built); \
		cd tmp/mondo; \
		git fetch origin; \
		latest_hash=$$(git rev-parse origin/master); \
		if [ ! "$$current_hash" = "$$latest_hash" ]; then \
			cd .. && mv mondo mondo-bak && mv mondo_repo_built mondo_repo_built-bak; \
			cd .. && $(MAKE) tmp/mondo_repo_built -B; \
			rm -rf tmp/mondo-bak tmp/mondo_repo_built-bak; \
		fi; \
	fi

.PHONY: up-to-date-mondo.sssom.tsv
up-to-date-mondo.sssom.tsv: refresh-mondo-clone

.PHONY: up-to-date-mondo.owl
up-to-date-mondo.owl: refresh-mondo-clone

reports/mirror_signature-mondo.tsv:
	$(MAKE) up-to-date-mondo.owl
	$(ROBOT) query -i tmp/mondo.owl --query ../sparql/classes.sparql $@
	(head -n 1 $@ && tail -n +2 $@ | sort) > $@-temp
	mv $@-temp $@

reports/mirror_signature-ncit.tsv: $(COMPONENTSDIR)/ncit.db metadata/ncit.yml
	python3 $(SCRIPTSDIR)/mirror_signature_via_oak.py --db-path $(COMPONENTSDIR)/ncit.db --onto-config-path metadata/ncit.yml --outpath $@

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
	@echo "Finished running signature reports."

#############################
#### Lexical matching #######
#############################
# Official Mondo SSSOM Mappings
# - Doeesn't include: broad mappings
# - Comes from make tmp/mondo.owl

tmp/mondo.sssom.ttl:
	$(MAKE) up-to-date-mondo.sssom.tsv
	sssom convert $(TMPDIR)/mondo.sssom.tsv -O rdf -o $@

ALL_EXCLUSION_FILES= $(patsubst %, $(REPORTDIR)/%_term_exclusions.txt, $(ALL_COMPONENT_IDS))
ALL_EXCLUSION_FILES_AS_PARAM= $(patsubst %, --exclusion $(REPORTDIR)/%_term_exclusions.txt, $(ALL_COMPONENT_IDS))


MONDO_REJECT_SHEET = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR_pk7yVg6caeLOiHk0EME2mylCtwNrORCgE0OV80YgoIRYztBYmRTooV8veJiPyYW1ExWBKriU17Kt/pub?gid=0&single=true&output=tsv"
$(MAPPINGSDIR)/rejected-mappings.tsv:
	wget $(MONDO_REJECT_SHEET) -O $@

$(MAPPINGSDIR)/rejected-mappings-sssom.tsv: $(MAPPINGSDIR)/rejected-mappings.tsv
	sssom parse $< -m metadata/mondo.sssom.config.yml --no-strict-clean-prefixes -o $@

tmp/mondo-ingest.owl: mondo-ingest.owl
	cp $< $@

# Merge Mondo, precise mappings and mondo-ingest into one coherent whole for the purpose of querying.
tmp/merged.owl: mondo-ingest.owl tmp/mondo.sssom.ttl
	$(MAKE) up-to-date-mondo.owl
	$(ROBOT) merge -i tmp/mondo.owl -i mondo-ingest.owl -i tmp/mondo.sssom.ttl --add-prefixes config/context.json \
			 remove --term "http://purl.obolibrary.org/obo/mondo#ABBREVIATION" --preserve-structure false -o $@

# todo: should probably be a multi-target goal, including: $(MAPPINGSDIR)/mondo-sources-all-lexical-2.sssom.tsv
$(MAPPINGSDIR)/mondo-sources-all-lexical.sssom.tsv: $(SCRIPTSDIR)/match-mondo-sources-all-lexical.py tmp/merged.db $(MAPPINGSDIR)/rejected-mappings.tsv
	rm -f $(MAPPINGSDIR)/mondo-sources-all-lexical.sssom.tsv
	rm -f $(MAPPINGSDIR)/mondo-sources-all-lexical-2.sssom.tsv
	$(MAKE) pip-bioregistry
	python $(SCRIPTSDIR)/match-mondo-sources-all-lexical.py run tmp/merged.db \
		-c metadata/mondo.sssom.config.yml \
		-r config/mondo-match-rules.yaml \
		--rejects $(MAPPINGSDIR)/rejected-mappings.tsv \
		-o $@

.PHONY: lexical-matches
lexical-matches: $(MAPPINGSDIR)/mondo-sources-all-lexical.sssom.tsv

###################################
#### Lexmatch-SSSOM-compare #######
###################################
# This goal also creates, for all sources: lexmatch/unmapped_%_lex.tsv, lexmatch/unmapped_%_lex_exact.tsv
lexmatch/README.md: $(SCRIPTSDIR)/lexmatch-sssom-compare.py $(MAPPINGSDIR)/mondo-sources-all-lexical.sssom.tsv $(ALL_EXCLUSION_FILES)
	find lexmatch/ -name "*.tsv" -type f -delete
	python $(SCRIPTSDIR)/lexmatch-sssom-compare.py extract_unmapped_matches $(ALL_COMPONENT_IDS) \
		--matches $(MAPPINGSDIR)/mondo-sources-all-lexical.sssom.tsv \
		--output-dir lexmatch \
		--summary $@ \
		$(ALL_EXCLUSION_FILES_AS_PARAM)

extract-unmapped-matches: lexmatch/README.md

###################################
#### Lexmatch-combine #######
###################################
lexmatch/all_exact.robot.tsv: $(SCRIPTSDIR)/lexmatch-sssom-compare.py lexmatch/README.md
	python $< combine_unmapped_lex_exacts

combine-unmapped-exact-lexmatches: lexmatch/all_exact.robot.tsv

.PHONY: matches
matches: lexical-matches extract-unmapped-matches combine-unmapped-exact-lexmatches

#############################
###### Slurp pipeline #######
#############################
slurp/:
	mkdir -p $@

# min-id: the next available Mondo ID
slurp/%.tsv: $(COMPONENTSDIR)/%.owl $(REPORTDIR)/%_mapping_status.tsv $(REPORTDIR)/%_term_exclusions.txt $(REPORTDIR)/mirror_signature-mondo.tsv | slurp/
	$(MAKE) up-to-date-mondo.sssom.tsv
	python3 $(SCRIPTSDIR)/migrate.py \
	--ontology-path $(COMPONENTSDIR)/$*.owl \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--onto-config-path metadata/$*.yml \
	--mapping-status-path reports/$*_mapping_status.tsv \
	--min-id 850056 \
	--max-id 999999 \
	--mondo-terms-path $(REPORTDIR)/mirror_signature-mondo.tsv \
	--slurp-dir-path slurp/ \
	--outpath $@
.PRECIOUS: slurp/%.tsv

.PHONY: slurp-%
slurp-%: slurp/%.tsv
	@echo "$@ completed".

.PHONY: slurp-ordo
slurp-ordo: slurp/ordo.tsv
	$(MAKE) slurp-modifications-ordo

.PHONY: slurp-no-updates-%
slurp-no-updates-%: slurp/%.tsv
	@echo "$@ completed".

.PHONY: slurp-docs
slurp-docs:
	python3 $(SCRIPTSDIR)/migrate.py --docs

.PHONY: slurp-all-no-updates
slurp-all-no-updates: $(foreach n,$(ALL_COMPONENT_IDS), slurp-no-updates-$(n))
	$(MAKE) slurp-modifications
	@echo "$@ ($^) completed".

.PHONY: slurp-all
slurp-all: $(foreach n,$(ALL_COMPONENT_IDS), slurp-$(n))
	$(MAKE) slurp-modifications
	@echo "$@ ($^) completed".

.PHONY: slurp-modifications
slurp-modifications: slurp-modifications-ordo

.PHONY: slurp-modifications-ordo
slurp-modifications-ordo: slurp/ordo.tsv tmp/ordo-subsets.tsv
	python3 $(SCRIPTSDIR)/migrate.py --ordo-mods

#############################
###### Synchronization ######
#############################
.PHONY: sync
sync: sync-subclassof

.PHONY: sync-subclassof
sync-subclassof: $(REPORTDIR)/sync-subClassOf.confirmed.tsv $(REPORTDIR)/sync-subClassOf.direct-in-mondo-only.tsv $(TMPDIR)/sync-subClassOf.added.self-parentage.tsv

# todo: drop this? This is really just an alias here for quality of life, but not used by anything.
.PHONY: sync-subclassof-%
sync-subclassof-%: $(REPORTDIR)/%.subclass.confirmed.robot.tsv

$(TMPDIR)/sync-subClassOf.added.self-parentage.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(TMPDIR)/$(n).subclass.self-parentage.tsv)
	$(MAKE) up-to-date-mondo.sssom.tsv
	python3 $(SCRIPTSDIR)/sync_subclassof_collate_self_parentage.py \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \

# Side effects: Deletes SOURCE.subclass.direct-in-mondo-only.tsv's from which the combination is made.
$(REPORTDIR)/sync-subClassOf.direct-in-mondo-only.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n).subclass.direct-in-mondo-only.tsv) tmp/mondo.db
	python3 $(SCRIPTSDIR)/sync_subclassof_collate_direct_in_mondo_only.py --outpath $@

$(REPORTDIR)/sync-subClassOf.confirmed.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n).subclass.confirmed.robot.tsv)
	awk '(NR == 1) || (NR == 2) || (FNR > 2)' $(REPORTDIR)/*.subclass.confirmed.robot.tsv > $@

$(REPORTDIR)/%.subclass.confirmed.robot.tsv $(REPORTDIR)/%.subclass.added.robot.tsv $(REPORTDIR)/%.subclass.added-obsolete.robot.tsv $(REPORTDIR)/%.subclass.direct-in-mondo-only.tsv $(TMPDIR)/%.subclass.self-parentage.tsv: tmp/mondo-ingest.db tmp/mondo.db
	$(MAKE) up-to-date-mondo.sssom.tsv
	python3 $(SCRIPTSDIR)/sync_subclassof.py \
	--outpath-added $(REPORTDIR)/$*.subclass.added.robot.tsv \
	--outpath-added-obsolete $(REPORTDIR)/$*.subclass.added-obsolete.robot.tsv \
	--outpath-confirmed $(REPORTDIR)/$*.subclass.confirmed.robot.tsv \
	--outpath-direct-in-mondo-only $(REPORTDIR)/$*.subclass.direct-in-mondo-only.tsv \
	--outpath-self-parentage $(TMPDIR)/$*.subclass.self-parentage.tsv \
	--mondo-db-path $(TMPDIR)/mondo.db \
	--mondo-ingest-db-path $(TMPDIR)/mondo-ingest.db \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--onto-config-path metadata/$*.yml

##################################
## Externally managed content ####
##################################

EXTERNAL_CONTENT_DIR=external

EXTERNAL_FILES = efo-proxy-merges \
		mondo-clingen \
		mondo-efo \
		mondo-medgen \
		mondo-omim-genes \
		mondo-otar-subset \
		nando-mappings \
		nord \
		ordo-subsets

tmp/mondo-incl-external.owl: mondo.owl $(foreach n,$(EXTERNAL_FILES), external/$(n).robot.owl)
	$(ROBOT) merge -i mondo.owl $(foreach n,$(EXTERNAL_FILES), -i external/$(n).robot.owl) \
		filter --term MONDO:0000001 --term MONDO:0021125 --term MONDO:0042489 --term MONDO:0021178 --select "annotations self descendants" --signature true -o $@

tmp/mondo-incl-robot-report.tsv: tmp/mondo-incl-external.owl config/robot_report_external_content.txt
	$(ROBOT) report -i $< --profile config/robot_report_external_content.txt -o $@

.PHONY: update-externally-managed-content
update-externally-managed-content: tmp/mondo-incl-robot-report.tsv $(foreach n,$(EXTERNAL_FILES), $(EXTERNAL_CONTENT_DIR)/$(n).robot.owl)
	python $(SCRIPTSDIR)/post_process_externally_managed_content.py $(foreach n,$(EXTERNAL_FILES), --emc-id $(n)) --emc-dir $(EXTERNAL_CONTENT_DIR) --robot-report $<
	@echo "Externally managed content updated."

$(EXTERNAL_CONTENT_DIR)/%.robot.owl: $(EXTERNAL_CONTENT_DIR)/%.robot.tsv
	$(ROBOT) template \
		--template $< \
		--prefix "orcid: https://orcid.org/" \
		--input $(IMPORTDIR)/ro_import.owl \
	 	annotate \
				--ontology-iri $(URIBASE)/mondo/external/nord.robot.owl \
				--version-iri $(URIBASE)/mondo/external/$(TODAY)/nord.robot.owl \
				-o $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/%.robot.owl

###### NORD #########

$(TMPDIR)/nord.tsv:
	wget "https://rdbdev.wpengine.com/wp-content/uploads/mondo-export/rare_export.tsv" -O $@

$(EXTERNAL_CONTENT_DIR)/nord.robot.tsv: $(TMPDIR)/nord.tsv config/external-content-robot-headers.json
	mkdir -p $(EXTERNAL_CONTENT_DIR)
	python ../scripts/add-robot-template-header.py $^ > $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/nord.robot.tsv

###### ORDO #########

tmp/ordo-subsets.tsv:
	$(MAKE) component-download-ordo.owl
	$(ROBOT) query -i $(TMPDIR)/component-download-ordo.owl.owl --query ../sparql/select-ordo-subsets.sparql $@

$(EXTERNAL_CONTENT_DIR)/ordo-subsets.robot.tsv: tmp/ordo-subsets.tsv
	mkdir -p $(EXTERNAL_CONTENT_DIR)
	$(MAKE) up-to-date-mondo.sssom.tsv
	python3 $(SCRIPTSDIR)/ordo_subsets.py \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--class-subsets-tsv-path tmp/ordo-subsets.tsv \
	--onto-config-path metadata/ordo.yml \
	--outpath $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/ordo-subsets.robot.tsv

###### OMIM #########

$(EXTERNAL_CONTENT_DIR)/mondo-omim-genes.robot.tsv:
	mkdir -p $(EXTERNAL_CONTENT_DIR)
	wget "https://github.com/monarch-initiative/omim/releases/latest/download/mondo-omim-genes.robot.tsv" -O $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/mondo-omim-genes.robot.tsv

###### NanDO #########

$(MAPPINGSDIR)/mondo-nando.sssom.tsv: $(MAPPINGSDIR)/nando-mondo.sssom.tsv
	sssom invert $(MAPPINGSDIR)/nando-mondo.sssom.tsv --no-merge-inverted -o $@
	sssom annotate $@ --mapping_provider "MONDO:NANDO" -o $@

$(EXTERNAL_CONTENT_DIR)/nando-mappings.robot.tsv: $(MAPPINGSDIR)/mondo-nando.sssom.tsv
	mkdir -p $(EXTERNAL_CONTENT_DIR)
	python ../scripts/sssom_to_robot_template.py --inpath $< --outpath $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/nando-mappings.robot.tsv

###### OTAR / EFO #########

$(EXTERNAL_CONTENT_DIR)/mondo-efo.robot.tsv:
	wget "https://raw.githubusercontent.com/EBISPOT/efo/master/src/ontology/reports/mondo-efo.robot.tsv" -O $@

$(EXTERNAL_CONTENT_DIR)/mondo-otar-subset.robot.tsv:
	wget "https://raw.githubusercontent.com/EBISPOT/efo/master/src/ontology/reports/mondo-otar-subset.robot.tsv" -O $@

# Unfortunately, @matentzn cant find the orginal TSV file, but it is highly unlikely this file will ever change.

$(EXTERNAL_CONTENT_DIR)/efo-proxy-merges.robot.owl:
	echo "WARNING: $@" is currently manually curated!"

###### MedGen #########

$(EXTERNAL_CONTENT_DIR)/mondo-medgen.robot.tsv:
	wget "https://github.com/monarch-initiative/medgen/releases/latest/download/medgen-xrefs.robot.template.tsv" -O $@

###### ClinGen #########

# Managed in Google Sheets:
# https://docs.google.com/spreadsheets/d/1JAgySABpRkmXl-8lu5Yrxd9yjTGNbH8aoDcMlHqpssQ/edit?gid=637121472#gid=637121472

$(EXTERNAL_CONTENT_DIR)/mondo-clingen.robot.tsv:
	wget "https://docs.google.com/spreadsheets/d/e/2PACX-1vRiYDV1n1nDuJOgnlFx6DsYGyIGlbgI1HeDzI740OgmOKYy2RCCyBqLHiBh-IMadYXjVglsxDPypArh/pub?gid=637121472&single=true&output=tsv" -O $@


#############################
######### Analysis ##########
#############################
.PHONY: mapped-deprecated-terms
mapped-deprecated-terms: mapped-deprecated-terms-docs

.PHONY: mapped-deprecated-terms-docs
mapped-deprecated-terms-docs: ../../docs/reports/mapped_deprecated.md

../../docs/reports/mapped_deprecated.md: mapped-deprecated-terms-artefacts
	python3 $(SCRIPTSDIR)/deprecated_in_mondo.py --docs

.PHONY: mapped-deprecated-terms-artefacts
mapped-deprecated-terms-artefacts: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n)_mapped_deprecated_terms.robot.template.tsv)

$(REPORTDIR)/%_mapped_deprecated_terms.robot.template.tsv: $(REPORTDIR)/%_mapping_status.tsv
	$(MAKE) up-to-date-mondo.sssom.tsv
	python3 $(SCRIPTSDIR)/deprecated_in_mondo.py \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--mapping-status-path $(REPORTDIR)/$*_mapping_status.tsv \
	--outpath $@

#################
##### Utils #####
#################
# Deprecated goal. Here for future reference.
.PHONY: report-mapping-annotations
report-mapping-annotations:
	python3 $(SCRIPTSDIR)/ordo_mapping_annotations/report_mapping_annotations.py

.PHONY: update-jinja-sparql-queries
update-jinja-sparql-queries:
	python3 $(SCRIPTSDIR)/ordo_mapping_annotations/create_sparql__ordo_replace_annotation_based_mappings.py
	python3 $(SCRIPTSDIR)/ordo_mapping_annotations/create_sparql__ordo_mapping_annotations_violation.py

#############################
########### Ad hoc ##########
#############################
$(REPORTDIR)/mondo_ordo_unsupported_subclass.tsv: ../sparql/mondo-ordo-unsupported-subclass.sparql
	$(ROBOT) query -i tmp/merged.owl --query $< $@

.PHONY: mondo-ordo-subclass
mondo-ordo-subclass: $(REPORTDIR)/mondo_ordo_unsupported_subclass.tsv

#############################
########### Help ############
#############################
# $$data: This prints the help message from imported makefiles.
.PHONY: help
help:
	@echo "$$data"
	@echo "----------------------------------------"
	@echo "	Command reference: mondo-ingest"
	@echo "----------------------------------------"
	# Common dependencies
	@echo "refresh-mondo-clone"
	@echo "Triggers a refresh of tmp/mondo/ and a rebuild of mondo.owl and mondo.sssom.tsv, only if mondo repo main branch has new commits\n"
	@echo "up-to-date-mondo.sssom.tsv"
	@echo "Triggers a refresh mondo.sssom.tsv (via refresh-mondo-clone), only if mondo repo main branch has new commits\n"
	@echo "up-to-date-mondo.owl"
	@echo "Triggers a refresh mondo.owl (via refresh-mondo-clone), only if mondo repo main branch has new commits\n"
	# Slurp / migrate
	@echo "slurp/%.tsv and slurp-%"
	@echo "For a given ontology, determine all slurpable / migratable terms. That is, terms that are candidates for integration into Mondo.\n"
	@echo "slurp-all"
	@echo "Runs slurp / migrate for all ontologies.\n"
	# Docs
	@echo "slurp-docs"
	@echo "Creates a page (docs/reports/migrate.md) listing 'n' migratable terms by ontology as well as and pages for each ontology with more detailed information."
	# Unmapped matches
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
	@echo "Creates a report of statistics for mapped deprecated terms (docs/reports/mapped_deprecated.md) and pages for each ontology which list their deprecated terms with existing xrefs in Mondo, where these terms have not yet been marked as deprecated in Mondo..\n"
	@echo "mapped-deprecated-terms"
	# Exclusions
	@echo "Creates a report of statistics for mapped deprecated terms (docs/reports/mapped_deprecated.md) and pages for each ontology which list their deprecated terms with existing xrefs in Mondo. Also creates a reports/%_mapped_deprecated_terms.robot.template.tsv for all ontologies.\n"
	@echo "unmapped/%-unmapped.owl"
	@echo "Creates an OWL component of the ontology which consists only of the subset of terms which are current mapping candidates.\n"
	@echo "recreate-unmapped-components"
	@echo "Runs unmapped/%-unmapped.owl for all ontologies.\n"
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
	# Synchronization
	@echo "sync"
	@echo "Runs synchronization pipeline.\n"
	# - Synchronization: subClassOf
	@echo "sync-subclassof"
	@echo "Runs 'sync-subclassof' part of synchronization pipeline, generating set of outputs for all ontologies.\n"
	@echo "sync-subclassof-%"
	@echo "Generates subClassOf synchronization outputs for given ontology. Alias for 'reports/%.subclass.added.robot.tsv', 'reports/%.subclass.confirmed.robot.tsv', and 'reports/%.subclass.direct-in-mondo-only.tsv'.\n"
	@echo "reports/%.subclass.added.robot.tsv"
	@echo "Creates robot template containing new subclass relationships from given ontology to be imported into Mondo. Running this also runs / generates 'reports/%.subclass.confirmed.robot.tsv' and 'reports/%.subclass.direct-in-mondo-only.tsv'.\n"
	@echo "reports/%.subclass.added-obsolete.robot.tsv": 
	@echo "Creates robot template containing new subclass relationships from given ontology that would be imported into Mondo, except for that these terms are obsolete in Mondo. Running this also runs / generates 'reports/%.subclass.added.robot.tsv', 'reports/%.subclass.confirmed.robot.tsv', and 'reports/%.subclass.direct-in-mondo-only.tsv'.\n"
	@echo "reports/%.subclass.confirmed.robot.tsv"
	@echo "Creates robot template containing subclass relations for given ontology that exist in Mondo and are confirmed to also exist in the source. Running this also runs / generates 'reports/%.subclass.added.robot.tsv' and 'reports/%.subclass.direct-in-mondo-only.tsv'.\n"
	@echo "reports/%.subclass.direct-in-mondo-only.tsv"
	@echo "Path to create file for relations for given ontology where direct subclass relation exists only in Mondo and not in the source. Running this also runs / generates 'reports/%.subclass.added.robot.tsv' and 'reports/%.subclass.confirmed.robot.tsv'.\n"
	@echo "reports/sync-subClassOf.direct-in-mondo-only.tsv"
	@echo "For all subclass relationships in Mondo, shows which sources do not have it and whether no source has it. Combination of all --outpath-direct-in-mondo-only outputs for all sources, using those as inputs, and then deletes them after.\n"
	@echo "reports/sync-subClassOf.confirmed.tsv"
	@echo "For all subclass relationships in Mondo, by source, a robot template containing showing what is in Mondo and are confirmed to also exist in the source. Combination of all --outpath-confirmed outputs for all sources.\n"
	# - Refresh externally managed content
	@echo "update-externally-managed-content"
	@echo "Downloads and processes all externally managed content like cross references, subsets and labels, including NORD and GARD.\n"
