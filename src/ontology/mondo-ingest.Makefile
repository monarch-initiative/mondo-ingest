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
### COMPONENT VERSIONS #############
####################################

# Since ODK 1.6, the download sources of the components are managed in the Makefile
# Rather than the config file. For the Open Data Archeologist, check for context
# https://github.com/INCATools/ontology-development-kit/issues/1272#issuecomment-2914089788
DOID=				http://purl.obolibrary.org/obo/doid.owl
ICD10_BP_CODE=		27
ICD10CM=			https://data.bioontology.org/ontologies/ICD10CM/submissions/$(ICD10_BP_CODE)/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb
ICD10WHO=			https://github.com/monarch-initiative/icd10who/releases/latest/download/icd10who.ttl
ICD11FOUNDATION=	https://github.com/monarch-initiative/icd11/releases/latest/download/icd11foundation.owl
NCIT=				http://purl.obolibrary.org/obo/ncit.owl
OMIM=				https://github.com/monarch-initiative/omim/releases/latest/download/omim.owl
ORDO=				http://www.orphadata.org/data/ORDO/ordo_orphanet.owl

####################################
#### MIRROR SOURCES ################
####################################

ifeq ($(MIR),true)
$(TMPDIR)/mirror-ordo.owl: | all_robot_plugins $(TMPDIR)
	$(ROBOT) merge -I $(ORDO) \
		 odk:normalize --add-source true --output $@
.PRECIOUS: $(TMPDIR)/mirror-ordo.owl

$(TMPDIR)/mirror-doid.owl: | all_robot_plugins $(TMPDIR)
	$(ROBOT) merge -I $(DOID) \
		 odk:normalize --add-source true --output $@
.PRECIOUS: $(TMPDIR)/mirror-doid.owl

$(TMPDIR)/mirror-icd10who.owl: | all_robot_plugins $(TMPDIR)
	$(ROBOT) merge -I $(ICD10WHO) \
		 odk:normalize --add-source true --output $@
.PRECIOUS: $(TMPDIR)/mirror-icd10who.owl

$(TMPDIR)/mirror-icd11foundation.owl: | all_robot_plugins $(TMPDIR)
	$(ROBOT) merge -I $(ICD11FOUNDATION) \
		 odk:normalize --add-source true --output $@
.PRECIOUS: $(TMPDIR)/mirror-icd11foundation.owl

$(TMPDIR)/mirror-ncit.owl: | all_robot_plugins $(TMPDIR)
	$(ROBOT) merge -I $(NCIT) \
		 odk:normalize --add-source true --output $@
.PRECIOUS: $(TMPDIR)/mirror-ncit.owl

$(TMPDIR)/mirror-omim.owl: | all_robot_plugins $(TMPDIR)
	$(ROBOT) merge -I $(OMIM) \
		 odk:normalize --add-source true --output $@
.PRECIOUS: $(TMPDIR)/mirror-omim.owl

# The following preprocessing is necessary, because the bioportal version of ncit accidentally 
# puns ICD10 terms to be individuals and classes at the same time
# the remove step needs to run _before_ the first time the OWL API serialises the file, as 
# The injected declaration axioms makes it very hard to remove the
# Axioms that cause the codes to be individuals as well
$(TMPDIR)/mirror-icd10cm.owl: | all_robot_plugins $(TMPDIR)
	wget $(ICD10CM) -O $(TMPDIR)/icd10cm.tmp.owl
	$(ROBOT) remove -i $(TMPDIR)/icd10cm.tmp.owl --select imports \
		remove -T config/remove_properties.txt \
		annotate \
			--ontology-iri https://bioportal.bioontology.org/ontologies/ICD10CM/$@ \
			--version-iri https://data.bioontology.org/ontologies/ICD10CM/submissions/$(ICD10_BP_CODE)/icd10cm.owl \
		odk:normalize --add-source true -o $@
.PRECIOUS: $(TMPDIR)/mirror-icd10cm.owl

endif

####################################
### Standard constants #############
####################################
MAPPINGSDIR=../mappings
DOCS_DIR=../../docs
SKIP_HUGE=false

####################################
### Package management #############
####################################
.PHONY: pip-%
pip-%:
	 python3 -m pip install --upgrade $* --break-system-packages

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
$(TMPDIR)/%_relevant_signature.txt: $(TMPDIR)/mirror-%.owl | $(TMPDIR)
	if [ $(COMP) = true ]; then $(ROBOT) query -i $< -q "../sparql/$*-relevant-signature.sparql" $@; fi
.PRECIOUS: $(TMPDIR)/%_relevant_signature.txt

### ORDO needs to be structurally changed before the query can be run..
$(TMPDIR)/ordo_relevant_signature.txt: $(TMPDIR)/mirror-ordo.owl | $(TMPDIR)
	if [ $(COMP) = true ]; then $(ROBOT) query -i $< --update ../sparql/ordo-construct-subclass-from-part-of.ru \
		query -q "../sparql/ordo-relevant-signature.sparql" $@; fi
.PRECIOUS: $(TMPDIR)/ordo_relevant_signature.txt

#######################################
### Ingest Components #################
#######################################
# This section is concerned with transforming the incoming sources into the
# Monarch Ingest schema.
# todo: Illegal punning on some properties #60: https://github.com/monarch-initiative/omim/issues/60
#  - #60 needs to be fixed at source, but a workaround can probably be implemented in this goal
$(COMPONENTSDIR)/omim.owl: $(TMPDIR)/omim_relevant_signature.txt $(TMPDIR)/mirror-omim.owl
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/mirror-omim.owl --select imports \
		rename --mappings config/property-map.sssom.tsv --allow-missing-entities true --allow-duplicates true \
		remove -T $(TMPDIR)/omim_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T config/remove.txt --axioms equivalent \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/fix_illegal_punning_omim.ru \
			--update ../sparql/exact_syn_from_label.ru \
			--update ../sparql/convert-OMO_0003000-to-MONDO_ABBREVIATION.ru \
		annotate --ontology-iri $(URIBASE)/mondo/sources/omim.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/omim.owl -o $@; fi

# todo: See #1 at top of file
$(COMPONENTSDIR)/ordo.owl: $(TMPDIR)/ordo_relevant_signature.txt config/properties.txt $(TMPDIR)/mirror-ordo.owl
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/mirror-ordo.owl --select imports \
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
		query --update ../sparql/ordo-replace-annotation-based-mappings.ru \
		remove --term oboInOwl:hasDbXref --axioms "annotation" \
		remove -T $(TMPDIR)/ordo_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/ordo.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/ordo.owl -o $@; fi

$(COMPONENTSDIR)/ncit.owl: $(TMPDIR)/ncit_relevant_signature.txt | $(TMPDIR)/mirror-ncit.owl
	if [ $(SKIP_HUGE) = false ] && [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/mirror-ncit.owl --select imports \
		rename --mappings config/property-map.sssom.tsv --allow-missing-entities true --allow-duplicates true \
		query \
			--update ../sparql/rm_xref_by_prefix.ru \
			--update ../sparql/exact_syn_from_label.ru \
		remove -T $(TMPDIR)/ncit_relevant_signature.txt --select complement --select "classes individuals" --trim false \
			--drop-axiom-annotations NCIT:P378 \
			--drop-axiom-annotations NCIT:P383 \
			--drop-axiom-annotations NCIT:P384 \
		remove -T config/properties.txt --select complement --select properties --trim true \
		remove --term "http://purl.obolibrary.org/obo/NCIT_C179199" --axioms "equivalent" \
		annotate --ontology-iri $(URIBASE)/mondo/sources/ncit.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/ncit.owl -o $@; fi

# todo: See #1 at top of file
$(COMPONENTSDIR)/doid.owl: $(TMPDIR)/doid_relevant_signature.txt | $(TMPDIR)/mirror-doid.owl
	if [ $(COMP) = true ]; then $(ROBOT) remove -i $(TMPDIR)/mirror-doid.owl --select imports \
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

# todo: See #1 at top of file
$(COMPONENTSDIR)/icd10cm.owl: $(TMPDIR)/icd10cm_relevant_signature.txt $(TMPDIR)/mirror-icd10cm.owl
	if [ $(COMP) = true ]; then $(ROBOT) merge -i $(TMPDIR)/mirror-icd10cm.owl \
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
$(COMPONENTSDIR)/icd10who.owl: $(TMPDIR)/icd10who_relevant_signature.txt | $(TMPDIR)/mirror-icd10who.owl
	if [ $(COMP) = true ] ; then $(ROBOT) remove -i $(TMPDIR)/mirror-icd10who.owl --select imports \
		rename --mappings config/property-map.sssom.tsv --allow-missing-entities true --allow-duplicates true \
		remove -T $(TMPDIR)/icd10who_relevant_signature.txt --select complement --select "classes individuals" --trim false \
		remove -T $(TMPDIR)/icd10who_relevant_signature.txt --select individuals \
		query \
			--update ../sparql/fix_omimps.ru \
			--update ../sparql/fix-labels-with-brackets.ru \
			--update ../sparql/exact_syn_from_label.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/icd10who.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/icd10who.owl -o $@; fi

$(COMPONENTSDIR)/icd11foundation.owl: $(TMPDIR)/icd11foundation_relevant_signature.txt $(TMPDIR)/mirror-icd11foundation.owl
	if [ $(COMP) = true ] ; then $(ROBOT) remove -i $(TMPDIR)/mirror-icd11foundation.owl --select imports \
		rename --mappings config/property-map.sssom.tsv --allow-missing-entities true --allow-duplicates true \
		rename --mappings config/icd11foundation-property-map.sssom.tsv \
		remove -T $(TMPDIR)/icd11foundation_relevant_signature.txt --select complement --select "classes individuals" \
		remove -T $(TMPDIR)/icd11foundation_relevant_signature.txt --select individuals \
		query \
			--update ../sparql/exact_syn_from_label.ru \
			--update ../sparql/fix_icd11_synonyms.ru \
		remove -T config/properties.txt --select complement --select properties --trim true \
		annotate --ontology-iri $(URIBASE)/mondo/sources/icd11foundation.owl --version-iri $(URIBASE)/mondo/sources/$(TODAY)/icd11foundation.owl -o $@; fi

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
unmapped-terms-docs: docs/reports/unmapped.md

# todo: ideally `unmapped_docs.py` would also take file path(s) as input args. Currently, running `unmapped_%.md` for any source will trigger this for all sources.
docs/reports/unmapped.md docs/reports/unmapped_%.md: $(foreach n,$(ALL_COMPONENT_IDS), reports/$(n)_unmapped_terms.tsv)
	python3 $(SCRIPTSDIR)/unmapped_docs.py

.PHONY: unmapped-terms-tables
unmapped-terms-tables: $(foreach n,$(ALL_COMPONENT_IDS), reports/$(n)_mapping_status.tsv)

$(REPORTDIR)/%_mapping_status.tsv $(REPORTDIR)/%_unmapped_terms.tsv: $(REPORTDIR)/%_term_exclusions.txt metadata/%.yml $(COMPONENTSDIR)/%.db $(TMPDIR)/mondo.sssom.tsv
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
$(REPORTDIR)/%_term_exclusions.txt $(REPORTDIR)/%_exclusion_reasons.robot.template.tsv: config/%_exclusions.tsv $(TMPDIR)/mirror-%.owl $(REPORTDIR)/mirror_signature-%.tsv $(REPORTDIR)/component_signature-%.tsv metadata/%.yml
	python3 $(SCRIPTSDIR)/exclusion_table_creation.py \
	--select-intensional-exclusions-path config/$*_exclusions.tsv \
	--onto-path $(TMPDIR)/mirror-$*.owl \
	--mirror-signature-path $(REPORTDIR)/mirror_signature-$*.tsv \
	--component-signature-path $(REPORTDIR)/component_signature-$*.tsv \
	--config-path metadata/$*.yml \
	--outpath-txt $(REPORTDIR)/$*_term_exclusions.txt \
	--outpath-robot-template-tsv $(REPORTDIR)/$*_exclusion_reasons.robot.template.tsv
.PRECIOUS: $(REPORTDIR)/%_exclusion_reasons.robot.template.tsv

$(REPORTDIR)/%_exclusion_reasons.ttl: $(REPORTDIR)/%_exclusion_reasons.robot.template.tsv $(TMPDIR)/mirror-%.owl
	$(ROBOT) template --input $(TMPDIR)/mirror-$*.owl --add-prefixes config/context.json --template $(REPORTDIR)/$*_exclusion_reasons.robot.template.tsv --output $(REPORTDIR)/$*_exclusion_reasons.ttl

$(REPORTDIR)/%_excluded_terms_in_mondo_xrefs.tsv $(REPORTDIR)/%_excluded_terms_in_mondo_xrefs_summary.tsv: metadata/%.yml $(REPORTDIR)/component_signature-%.tsv $(REPORTDIR)/mirror_signature-%.tsv $(TMPDIR)/mondo.sssom.tsv $(TMPDIR)/mirror-%.owl
	python3 $(RELEASEDIR)/src/analysis/problematic_exclusions.py \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--onto-path  $(TMPDIR)/mirror-$*.owl \
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
ALL_SOURCE_DOCS=$(foreach n,$(ALL_COMPONENT_IDS), $(DOCS_DIR)/sources/$(n).md)
ALL_METRICS_DOCS=$(foreach n,$(ALL_COMPONENT_IDS), $(DOCS_DIR)/metrics/$(n).md)
ALL_DOCS=$(ALL_SOURCE_DOCS) $(ALL_METRICS_DOCS)

$(DOCS_DIR)/sources/ $(DOCS_DIR)/metrics/ $(MAPPINGSDIR)/:
	mkdir -p $@

$(DOCS_DIR)/sources/%.md: metadata/%.yml | $(DOCS_DIR)/sources/
	jinjanate "$(SOURCE_DOC_TEMPLATE)" $< > $@

PREFIXES_METRICS=--prefix 'OMIM: http://omim.org/entry/' \
	--prefix 'CHR: http://purl.obolibrary.org/obo/CHR_' \
	--prefix 'UMLS: http://linkedlifedata.com/resource/umls/id/' \
	--prefix 'HGNC: https://www.genenames.org/data/gene-symbol-report/\#!/hgnc_id/' \
	--prefix 'biolink: https://w3id.org/biolink/vocab/'

metadata/%-metrics.json: $(COMPONENTSDIR)/%.owl
	$(ROBOT) measure $(PREFIXES_METRICS) -i $(COMPONENTSDIR)/$*.owl --format json --metrics extended --output $@
.PRECIOUS: metadata/%-metrics.json

$(DOCS_DIR)/metrics/%.md: metadata/%-metrics.json | $(DOCS_DIR)/metrics/
	jinjanate "$(SOURCE_METRICS_TEMPLATE)" metadata/$*-metrics.json > $@

.PHONY: documentation
documentation: $(ALL_DOCS) unmapped-terms-docs mapped-deprecated-terms-docs slurp-docs


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


# make function, not target!
# Builds tmp/mondo/ and rebuilds mondo.owl, mondo-edit.owl and mondo.sssom.tsv, and stores hash of latest commit of mondo repo main branch in tmp/mondo_repo_built
define build_mondo
	cd $(TMPDIR) && \
	rm -rf ./mondo/ && \
	git clone --depth 1 https://github.com/monarch-initiative/mondo && \
	cd mondo/src/ontology && \
	make mondo.owl mappings -B MIR=false IMP=false &&\
	latest_hash=$$(git rev-parse origin/master) && \
	echo "$$latest_hash" > $(1)
endef

SKIP_REFRESH=false

$(TMPDIR)/mondo_repo_built: .FORCE
	@if [ ! -f $@ ]; then \
		$(call build_mondo, $@); \
	elif [ "$(SKIP_REFRESH)" != "true" ]; then \
		current_hash=$$(cat $@); \
		cd $(TMPDIR)/mondo; \
		git fetch origin; \
		latest_hash=$$(git rev-parse origin/master); \
		if [ ! "$$current_hash" = "$$latest_hash" ]; then \
			cd .. && mv mondo mondo-bak && mv mondo_repo_built mondo_repo_built-bak; \
			cd .. && $(call build_mondo, $@); \
			rm -rf $(TMPDIR)/mondo-bak $(TMPDIR)/mondo_repo_built-bak; \
		fi; \
	fi


$(TMPDIR)/mondo.owl: $(TMPDIR)/mondo_repo_built
	cp $(TMPDIR)/mondo/src/ontology/mondo.owl $@

 $(TMPDIR)/mondo.sssom.tsv: $(TMPDIR)/mondo_repo_built
	cp $(TMPDIR)/mondo/src/ontology/mappings/mondo.sssom.tsv $@

reports/mirror_signature-mondo.tsv: $(TMPDIR)/mondo.owl
	$(ROBOT) query -i $(TMPDIR)/mondo.owl --query ../sparql/classes.sparql $@
	(head -n 1 $@ && tail -n +2 $@ | sort) > $@-temp
	mv $@-temp $@

reports/mirror_signature-ncit.tsv: $(COMPONENTSDIR)/ncit.db metadata/ncit.yml
	python3 $(SCRIPTSDIR)/mirror_signature_via_oak.py --db-path $(COMPONENTSDIR)/ncit.db --onto-config-path metadata/ncit.yml --outpath $@

reports/mirror_signature-%.tsv: $(TMPDIR)/mirror-%.owl
	$(ROBOT) query -i $< --query ../sparql/classes.sparql $@
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

$(TMPDIR)/mondo.sssom.ttl: $(TMPDIR)/mondo.sssom.tsv
	sssom convert $(TMPDIR)/mondo.sssom.tsv -O rdf -o $@

ALL_EXCLUSION_FILES= $(patsubst %, $(REPORTDIR)/%_term_exclusions.txt, $(ALL_COMPONENT_IDS))
ALL_EXCLUSION_FILES_AS_PARAM= $(patsubst %, --exclusion $(REPORTDIR)/%_term_exclusions.txt, $(ALL_COMPONENT_IDS))


MONDO_REJECT_SHEET = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR_pk7yVg6caeLOiHk0EME2mylCtwNrORCgE0OV80YgoIRYztBYmRTooV8veJiPyYW1ExWBKriU17Kt/pub?gid=0&single=true&output=tsv"
$(MAPPINGSDIR)/rejected-mappings.tsv:
	wget $(MONDO_REJECT_SHEET) -O $@

$(MAPPINGSDIR)/rejected-mappings-sssom.tsv: $(MAPPINGSDIR)/rejected-mappings.tsv
	sssom parse $< -m metadata/mondo.sssom.config.yml --no-strict-clean-prefixes -o $@

$(TMPDIR)/mondo-ingest.owl: mondo-ingest.owl
	cp $< $@

# Merge Mondo, precise mappings and mondo-ingest into one coherent whole for the purpose of querying.
$(TMPDIR)/merged.owl: mondo-ingest.owl $(TMPDIR)/mondo.sssom.ttl $(TMPDIR)/mondo.owl
	$(ROBOT) merge -i $(TMPDIR)/mondo.owl -i mondo-ingest.owl -i $(TMPDIR)/mondo.sssom.ttl --add-prefixes config/context.json \
			 remove --term "http://purl.obolibrary.org/obo/mondo#ABBREVIATION" --preserve-structure false -o $@

# todo: should probably be a multi-target goal, including: $(MAPPINGSDIR)/mondo-sources-all-lexical-2.sssom.tsv
$(MAPPINGSDIR)/mondo-sources-all-lexical.sssom.tsv: $(SCRIPTSDIR)/match-mondo-sources-all-lexical.py $(TMPDIR)/merged.db $(MAPPINGSDIR)/rejected-mappings.tsv
	rm -f $(MAPPINGSDIR)/mondo-sources-all-lexical.sssom.tsv
	rm -f $(MAPPINGSDIR)/mondo-sources-all-lexical-2.sssom.tsv
	python $(SCRIPTSDIR)/match-mondo-sources-all-lexical.py run $(TMPDIR)/merged.db \
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
slurp/%.tsv: $(COMPONENTSDIR)/%.owl $(REPORTDIR)/%_mapping_status.tsv $(REPORTDIR)/%_term_exclusions.txt $(REPORTDIR)/mirror_signature-mondo.tsv $(TMPDIR)/mondo.sssom.tsv | slurp/
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

.PHONY: slurp-docs
slurp-docs:
	python3 $(SCRIPTSDIR)/migrate.py --docs

.PHONY: slurp-all
slurp-all: $(foreach n,$(ALL_COMPONENT_IDS), slurp-$(n))
	$(MAKE) slurp-modifications
	@echo "$@ ($^) completed".

.PHONY: slurp-modifications
slurp-modifications: slurp-modifications-ordo

.PHONY: slurp-modifications-ordo
slurp-modifications-ordo: slurp/ordo.tsv $(TMPDIR)/ordo-subsets.tsv
	python3 $(SCRIPTSDIR)/migrate.py --ordo-mods

#############################
###### Synchronization ######
#############################
.PHONY: sync
sync: sync-subclassof sync-synonyms

# Synchronization: subClassOf
.PHONY: sync-subclassof
sync-subclassof: $(REPORTDIR)/sync-subClassOf.confirmed.tsv $(REPORTDIR)/sync-subClassOf.confirmed-direct-source-indirect-mondo.tsv $(REPORTDIR)/sync-subClassOf.direct-in-mondo-only.tsv $(TMPDIR)/sync-subClassOf.added.self-parentage.tsv

# todo: drop this? This is really just an alias here for quality of life, but not used by anything.
.PHONY: sync-subclassof-%
sync-subclassof-%: $(REPORTDIR)/%.subclass.confirmed.robot.tsv

$(TMPDIR)/sync-subClassOf.added.self-parentage.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(TMPDIR)/$(n).subclass.self-parentage.tsv) $(TMPDIR)/mondo.sssom.tsv
	python3 $(SCRIPTSDIR)/sync_subclassof_collate_self_parentage.py \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv

# Side effects: Deletes SOURCE.subclass.direct-in-mondo-only.tsv's from which the combination is made.
$(REPORTDIR)/sync-subClassOf.direct-in-mondo-only.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n).subclass.direct-in-mondo-only.tsv) $(TMPDIR)/mondo.db
	python3 $(SCRIPTSDIR)/sync_subclassof_collate_direct_in_mondo_only.py --outpath $@

$(REPORTDIR)/sync-subClassOf.confirmed.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n).subclass.confirmed.robot.tsv)
	awk '(NR == 1) || (NR == 2) || (FNR > 2)' $(REPORTDIR)/*.subclass.confirmed.robot.tsv > $@

$(REPORTDIR)/sync-subClassOf.confirmed-direct-source-indirect-mondo.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n).subclass.confirmed-direct-source-indirect-mondo.robot.tsv)
	awk '(NR == 1) || (NR == 2) || (FNR > 2)' $(REPORTDIR)/*.subclass.confirmed-direct-source-indirect-mondo.robot.tsv > $@

$(TMPDIR)/mondo-excluded-subclasses.tsv: $(TMPDIR)/mondo.owl
	$(ROBOT) query -i $< -q ../sparql/mondo-excluded-subclasses.sparql $@

$(TMPDIR)/mondo-susceptibility-terms.tsv: $(TMPDIR)/mondo.owl
	$(ROBOT) query -i $< -q ../sparql/mondo-susceptibility-terms.sparql $@

$(REPORTDIR)/%.subclass.confirmed.robot.tsv $(REPORTDIR)/%.subclass.confirmed-direct-source-indirect-mondo.robot.tsv $(REPORTDIR)/%.subclass.added.robot.tsv $(REPORTDIR)/%.subclass.added-obsolete.robot.tsv $(REPORTDIR)/%.subclass.direct-in-mondo-only.tsv $(TMPDIR)/%.subclass.self-parentage.tsv: $(TMPDIR)/mondo-excluded-subclasses.tsv $(TMPDIR)/mondo-susceptibility-terms.tsv $(TMPDIR)/mondo-ingest.db $(TMPDIR)/mondo.db $(TMPDIR)/mondo.sssom.tsv
	python3 $(SCRIPTSDIR)/sync_subclassof.py \
	--outpath-added $(REPORTDIR)/$*.subclass.added.robot.tsv \
	--outpath-added-obsolete $(REPORTDIR)/$*.subclass.added-obsolete.robot.tsv \
	--outpath-confirmed $(REPORTDIR)/$*.subclass.confirmed.robot.tsv \
	--outpath-confirmed-direct-source-indirect-mondo $(REPORTDIR)/$*.subclass.confirmed-direct-source-indirect-mondo.robot.tsv \
	--outpath-direct-in-mondo-only $(REPORTDIR)/$*.subclass.direct-in-mondo-only.tsv \
	--outpath-self-parentage $(TMPDIR)/$*.subclass.self-parentage.tsv \
	--mondo-db-path $(TMPDIR)/mondo.db \
	--mondo-ingest-db-path $(TMPDIR)/mondo-ingest.db \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--onto-config-path metadata/$*.yml \
	--mondo-excluded-subclasses-path $(TMPDIR)/mondo-excluded-subclasses.tsv \
	--mondo-susceptibility-terms-path $(TMPDIR)/mondo-susceptibility-terms.tsv

# Synchronization: Synonyms
SYN_SYNC_DIR=$(REPORTDIR)/sync-synonym
$(SYN_SYNC_DIR):
	mkdir -p $@

.PHONY: sync-synonyms
sync-synonyms: $(SYN_SYNC_DIR)/sync-synonyms.added.robot.tsv $(SYN_SYNC_DIR)/sync-synonyms.confirmed.robot.tsv $(SYN_SYNC_DIR)/sync-synonyms.updated.robot.tsv $(SYN_SYNC_DIR)/review-qc-duplicate-exact-synonym-no-abbrev.tsv

# Note: If wanting to consider -updated/-scope-mismatch collisions, then: (i) change --dont_filter_updated to False, (ii) add $(SYN_SYNC_DIR)/sync-synonyms.updated.robot.tsv to the list of outputs in the goal definition, (iii) remove the separate goal for $(SYN_SYNC_DIR)/sync-synonyms.updated.robot.tsv.
$(SYN_SYNC_DIR)/sync-synonyms.added.robot.tsv $(SYN_SYNC_DIR)/review-qc-duplicate-exact-synonym-no-abbrev.tsv: $(TMPDIR)/sync-synonyms.added.robot.tsv $(SYN_SYNC_DIR)/sync-synonyms.confirmed.robot.tsv $(TMPDIR)/sync-synonyms.updated.robot.tsv $(TMPDIR)/mondo-synonyms-scope-type-xref.tsv $(TMPDIR)/mondo.db
	python3 $(SCRIPTSDIR)/sync_synonym_curation_filtering.py \
	--added-inpath $(TMPDIR)/sync-synonyms.added.robot.tsv \
	--confirmed-inpath $(SYN_SYNC_DIR)/sync-synonyms.confirmed.robot.tsv \
	--updated-inpath $(TMPDIR)/sync-synonyms.updated.robot.tsv \
	--added-outpath $(SYN_SYNC_DIR)/sync-synonyms.added.robot.tsv \
	--updated-outpath $(SYN_SYNC_DIR)/sync-synonyms.updated.robot.tsv \
	--mondo-synonyms-inpath $(TMPDIR)/mondo-synonyms-scope-type-xref.tsv \
	--mondo-db-inpath $(TMPDIR)/mondo.db \
	--review-outpath $(SYN_SYNC_DIR)/review-qc-duplicate-exact-synonym-no-abbrev.tsv \
	--dont-filter-updated True

$(SYN_SYNC_DIR)/sync-synonyms.updated.robot.tsv: $(TMPDIR)/sync-synonyms.updated.robot.tsv
	cp $< $@

$(SYN_SYNC_DIR)/sync-synonyms.confirmed.robot.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(TMPDIR)/$(n)-synonyms.confirmed.robot.tsv)
	awk '(NR == 1) || (NR == 2) || (FNR > 2)' $(TMPDIR)/*.synonyms.confirmed.robot.tsv > $@

$(TMPDIR)/sync-synonyms.added.robot.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(TMPDIR)/$(n)-synonyms.added.robot.tsv)
	awk '(NR == 1) || (NR == 2) || (FNR > 2)' $(TMPDIR)/*.synonyms.added.robot.tsv > $@

$(TMPDIR)/sync-synonyms.updated.robot.tsv: $(foreach n,$(ALL_COMPONENT_IDS), $(TMPDIR)/$(n)-synonyms.updated.robot.tsv)
	awk '(NR == 1) || (NR == 2) || (FNR > 2)' $(TMPDIR)/*.synonyms.updated.robot.tsv > $@

$(TMPDIR)/mondo-synonyms-scope-type-xref.tsv: $(TMPDIR)/mondo.owl
	$(ROBOT) query -i tmp/mondo.owl --query ../sparql/synonyms-scope-type-xref.sparql $@

$(TMPDIR)/%-synonyms-scope-type-xref.tsv: $(COMPONENTSDIR)/%.owl
	$(ROBOT) query -i $(COMPONENTSDIR)/$*.owl --query ../sparql/synonyms-scope-type-xref.sparql $@

../../tests/input/sync_synonym/%-synonyms-scope-type-xref.tsv:
	$(ROBOT) query -i ../../tests/input/sync_synonym/test_$*.owl --query ../sparql/synonyms-scope-type-xref.sparql $@

$(TMPDIR)/%-synonyms.added.robot.tsv $(TMPDIR)/%-synonyms.updated.robot.tsv $(TMPDIR)/%-synonyms.confirmed.robot.tsv: $(TMPDIR)/mondo.sssom.tsv $(COMPONENTSDIR)/%.db metadata/%.yml $(TMPDIR)/mondo-synonyms-scope-type-xref.tsv $(TMPDIR)/%-synonyms-scope-type-xref.tsv | $(TMPDIR)
	python3 $(SCRIPTSDIR)/sync_synonym.py \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--ontology-db-path $(COMPONENTSDIR)/$*.db \
	--mondo-synonyms-path $(TMPDIR)/mondo-synonyms-scope-type-xref.tsv \
	--mondo-exclusion-configs config/mondo-exclusion-configs.yml \
	--onto-synonym-types-path $(TMPDIR)/$*-synonyms-scope-type-xref.tsv \
	--onto-config-path metadata/$*.yml \
	--outpath-added $(TMPDIR)/$*.synonyms.added.robot.tsv \
	--outpath-confirmed $(TMPDIR)/$*.synonyms.confirmed.robot.tsv \
	--outpath-updated $(TMPDIR)/$*.synonyms.updated.robot.tsv \
   	--doid-added-filtration

##################################
## Externally managed content ####
##################################

EXTERNAL_CONTENT_DIR=external

EXTERNAL_FILES = \
	mondo-clingen \
	mondo-efo \
	mondo-medgen \
	mondo-omim-genes \
	mondo-otar-subset \
	mondo-malacards \
	nando-mappings \
	gard \
	nord \
	ordo-subsets

# The following target simulates the EMC pipeline. It runs it in exactly the same way
# as it would be run in the context of the Mondo repo. This way, we can test Mondo 
# in exactly the same state as it would look like when the EMC pipeline was run properly.
# In particular, this allows us to use QC tests that are reliant on the various pre- and 
# postprocessing steps needed, like Animal QC (which relies on the rare subset pipeline,
# which is SPARQL postprocessing based).

$(TMPDIR)/mondo-with-simulated-emc-run.owl: $(TMPDIR)/mondo_repo_built $(foreach n,$(EXTERNAL_FILES), $(EXTERNAL_CONTENT_DIR)/$(n).robot.owl)
	mkdir -p $(TMPDIR)/mondo/src/ontology/tmp/external/
	$(foreach n,$(EXTERNAL_FILES), cp -f $(EXTERNAL_CONTENT_DIR)/$(n).robot.owl $(TMPDIR)/mondo/src/ontology/tmp/external/processed-$(n).robot.owl;) \
	cd $(TMPDIR)/mondo/src/ontology && \
	touch mondo-edit.owl && \
	cp mondo-edit.owl mondo-edit.owl.bak && \
	cp mondo-edit.obo mondo-edit.obo.bak && \
	make update-external-content-incl-rare -B MIR=false IMP=false MIR=false DOWNLOAD_EXTERNAL=false &&\
	make mondo-edit.owl MIR=false IMP=false MIR=false
	cp $(TMPDIR)/mondo/src/ontology/mondo-edit.owl $@
	mv $(TMPDIR)/mondo/src/ontology/mondo-edit.owl.bak $(TMPDIR)/mondo/src/ontology/mondo-edit.owl
	mv $(TMPDIR)/mondo/src/ontology/mondo-edit.obo.bak $(TMPDIR)/mondo/src/ontology/mondo-edit.obo

$(TMPDIR)/mondo-incl-robot-report.tsv: $(TMPDIR)/mondo-with-simulated-emc-run.owl config/robot_report_external_content.txt
	$(ROBOT) report -i $(TMPDIR)/mondo-with-simulated-emc-run.owl --profile config/robot_report_external_content.txt --base-iri "http://purl.obolibrary.org/obo/MONDO_" --fail-on None -o $@

$(EXTERNAL_CONTENT_DIR)/processed-%.robot.tsv: $(EXTERNAL_CONTENT_DIR)/%.robot.tsv $(SCRIPTSDIR)/post_process_externally_managed_content.py $(TMPDIR)/mondo-incl-robot-report.tsv 
	python $(SCRIPTSDIR)/post_process_externally_managed_content.py --emc-template-tsv $(EXTERNAL_CONTENT_DIR)/$*.robot.tsv --robot-report $(TMPDIR)/mondo-incl-robot-report.tsv --output $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/processed-%.robot.tsv

.PHONY: update-externally-managed-content
update-externally-managed-content: $(foreach n,$(EXTERNAL_FILES), $(EXTERNAL_CONTENT_DIR)/processed-$(n).robot.owl)
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

###### GARD #########

# Managed here: https://docs.google.com/spreadsheets/d/1W2wDcnU4Nw0OApe3AvHtXSaOlA4RtmG5/edit?gid=1163320745#gid=1163320745

$(EXTERNAL_CONTENT_DIR)/gard.robot.tsv:
	wget "https://docs.google.com/spreadsheets/d/1W2wDcnU4Nw0OApe3AvHtXSaOlA4RtmG5/pub?gid=1163320745&single=true&output=tsv" -O $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/gard.robot.tsv

###### NORD #########

$(TMPDIR)/nord.tsv:
	wget "https://rdbdev.wpengine.com/wp-content/uploads/mondo-export/rare_export.tsv" -O $@

$(EXTERNAL_CONTENT_DIR)/nord.robot.tsv: $(TMPDIR)/nord.tsv config/external-content-robot-headers.json
	mkdir -p $(EXTERNAL_CONTENT_DIR)
	python ../scripts/add-robot-template-header.py $^ | \
	awk 'NR==1 { gsub(/synonym_type/, "preferred_label_for_community") } \
	     NR==2 { gsub(/>A oboInOwl:hasSynonymType/, ">A OMO:0002001") } \
		 NR > 2 { gsub(/http:\/\/purl.obolibrary.org\/obo\/mondo#NORD_LABEL/, "https://w3id.org/information-resource-registry/nord") } \
	     { print }' > $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/nord.robot.tsv

###### ORDO #########

$(TMPDIR)/ordo-subsets.tsv: $(TMPDIR)/mirror-ordo.owl
	$(ROBOT) query -i $< --query ../sparql/select-ordo-subsets.sparql $@

$(EXTERNAL_CONTENT_DIR)/ordo-subsets.robot.tsv: $(TMPDIR)/ordo-subsets.tsv $(TMPDIR)/mondo.sssom.tsv
	mkdir -p $(EXTERNAL_CONTENT_DIR)
	python3 $(SCRIPTSDIR)/ordo_subsets.py \
	--mondo-mappings-path $(TMPDIR)/mondo.sssom.tsv \
	--class-subsets-tsv-path $(TMPDIR)/ordo-subsets.tsv \
	--onto-config-path metadata/ordo.yml \
	--outpath $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/ordo-subsets.robot.tsv

###### OMIM #########

$(EXTERNAL_CONTENT_DIR)/mondo-omim-genes.robot.tsv:
	mkdir -p $(EXTERNAL_CONTENT_DIR)
	wget "https://github.com/monarch-initiative/omim/releases/latest/download/mondo-omim-genes.robot.tsv" -O $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/mondo-omim-genes.robot.tsv

$(EXTERNAL_CONTENT_DIR)/mondo-omim-susceptibility-subset.robot.tsv:
	mkdir -p $(EXTERNAL_CONTENT_DIR)
	wget "https://github.com/monarch-initiative/omim/releases/latest/download/mondo-omim-susceptibility-subset.robot.tsv" -O $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/mondo-omim-susceptibility-subset.robot.tsv

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

###### MedGen #########

$(EXTERNAL_CONTENT_DIR)/mondo-medgen.robot.tsv:
	wget "https://github.com/monarch-initiative/medgen/releases/latest/download/medgen-xrefs.robot.template.tsv" -O $@

###### MalaCards #########

# Managed by support@genecards.org

$(TMPDIR)/malacards.tsv:
	wget "https://genecardscustomers.blob.core.windows.net/mondo/Mondo_MalaCards_Current.tsv" -O $@

$(EXTERNAL_CONTENT_DIR)/mondo-malacards.robot.tsv: $(TMPDIR)/malacards.tsv
	awk 'NR==1 { print; print "ID	AT obo:mondo#curated_content_resource^^xsd:anyURI	>A oboInOwl:source"; next } { print }' $< > $@
.PRECIOUS: $(EXTERNAL_CONTENT_DIR)/mondo-malacards.robot.tsv

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
mapped-deprecated-terms-docs: $(DOCS_DIR)/reports/mapped_deprecated.md

# todo: ideally `deprecated_in_mondo.py` would also take file path(s) as input args. Currently, running `mapped_deprecated_%.md` for any source will trigger this for all sources.
$(DOCS_DIR)/reports/mapped_deprecated.md $(DOCS_DIR)/reports/mapped_deprecated_%.md: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n)_mapped_deprecated_terms.robot.template.tsv)
#$(DOCS_DIR)/reports/mapped_deprecated.md $(foreach n,$(ALL_COMPONENT_IDS), $(DOCS_DIR)/reports/mapped_deprecated_$(n).md): $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n)_mapped_deprecated_terms.robot.template.tsv)
	python3 $(SCRIPTSDIR)/deprecated_in_mondo.py --docs

.PHONY: mapped-deprecated-terms-artefacts
mapped-deprecated-terms-artefacts: $(foreach n,$(ALL_COMPONENT_IDS), $(REPORTDIR)/$(n)_mapped_deprecated_terms.robot.template.tsv)

$(REPORTDIR)/%_mapped_deprecated_terms.robot.template.tsv: $(REPORTDIR)/%_mapping_status.tsv $(TMPDIR)/mondo.sssom.tsv
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
	$(ROBOT) query -i $(TMPDIR)/merged.owl --query $< $@

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
	# - Synchronization: synonyms
	@echo "sync-synonyms"
	@echo "Runs 'sync-synonyms' part of synchronization pipeline, creating outputs for all sources for each of the 4 cases - 'added', 'confirmed', 'updated', and 'deleted'.\n"
	@echo "reports/%.subclass.added.robot.tsv"
	@echo "ROBOT template TSV to create which will contain synonyms that aren't yet integrated into Mondo for all mapped source terms.\n"
	@echo "reports/%.subclass.confirmed.robot.tsv"
	@echo "ROBOT template TSV to create which will contain synonym confirmations; combination of synonym scope predicate and synonym string exists in both source and Mondo for a given mapping.\n"
	@echo "reports/%.subclass.deleted.robot.tsv"
	@echo "ROBOT template TSV to create which will contain synonym deletions; exists in Mondo but not in source(s) for a given mapping.\n"
	@echo "reports/%.subclass.updated.robot.tsv"
	@echo "ROBOT template TSV to create which will contain updates to synonym scope predicate; cases where the synonym exists in Mondo and on the mapped source term, but the scope predicate is different.\n"
	@echo "reports/sync-synonyms.added.tsv"
	@echo "Combination of all 'added' synonym outputs for all sources.\n"
	@echo "reports/sync-synonyms.confirmed.tsv"
	@echo "Combination of all 'confirmed' synonym outputs for all sources.\n"
	@echo "reports/sync-synonyms.updated.tsv"
	@echo "Combination of all 'updated' synonym outputs for all sources.\n"
	# - Refresh externally managed content
	@echo "update-externally-managed-content"
	@echo "Downloads and processes all externally managed content like cross references, subsets and labels, including NORD and GARD.\n"
