## Externally managed content (EMC)

Externally managed content is content that is provided by trusted providers and is merged in _unreviewed_. Currently, we support three types of externally managed content:

1. Preferred names / labels. If a partner organisation of Monarch has a certain preference for a name this can be recorded as part of the metadata.
2. Cross-references and linkouts. Partner organisations can provide cross-references and linkout to important resources related to a disease.
3. Subsets. Partner organisations can provide subset information to Mondo. This is used in a variety of ways, such as:
   - NORD declares which diseases it consideres "rare"
   - Open Targets declares which diseases are used for their drug-prediction framework

### Typical workflows

1. External provider provides a TSV. (Ideally they use the same template that NORD uses - see `src/ontology/external/nord.robot.tsv`).
2. We pull it in and turn it into a ROBOT template and transform it to owl.

### QC system

We have implemented a full QC system for EMC here: https://github.com/monarch-initiative/mondo-ingest/pull/628.

It works like this:

1. A check is added to `src/ontology/config/robot_report_external_content.txt` (this is a standard ROBOT profile.txt). This check _must_ confirm to the ROBOT report formatting requirements, e.g. return exactly three variables (`?entity`, `?propert`, `?value`).
2. The QC system first transforms the externally managed content to OWL, then it tests it against the ROBOT report, then it removes _any_ ID - value combination identified to to be problematic by the QC. Note: Right now all EMCs are checked at once, and the QC system cant know for sure where which value has originally come from. This is usually a reasonable assumption, but may occassionally lead to false positives, i.e. where a value that is correct in one source was indeed correct in another. The most likely scenario is that two sources say "X" is a synonym, but source A says "narrow" and source B says "broad" - the QC system will remove them both as it cannot distinguish from the check alone which is the offending one.
3. After the QC system has removed all of the faulty values, it writes them to a report for the stakeholders which is shared in the src/ontology/external directory for each EMC source. It also produces a variant of the EMC file which is labelled "processed".
4. The "processed" variant should be used by the the Mondo pipeline when updating EMC.

### Adding a new EMC to Mondo ingest

1. Add the id of the EMC to the `EXTERNAL_FILES` variable, e.g.
   ```
   EXTERNAL_FILES = \
	efo-proxy-merges \
	mondo-new
   ```
2. Add a goal that handles the update (add helpful comments where the information is pulled from for future souls), e.g:
   ```
   ###### ClinGen #########

   # Managed in Google Sheets:
   # https://docs.google.com/spreadsheets/d/1JAgySABpRkmXl-8lu5Yrxd9yjTGNbH8aoDcMlHqpssQ/edit?gid=637121472#gid=637121472

   $(EXTERNAL_CONTENT_DIR)/mondo-clingen.robot.tsv:
      wget "https://docs.google.com/spreadsheets/d/e/2PACX-1vRiYDV1n1nDuJOgnlFx6DsYGyIGlbgI1HeDzI740OgmOKYy2RCCyBqLHiBh-IMadYXjVglsxDPypArh/pub?gid=637121472&single=true&output=tsv" -O $@
   ```
3. Add the active columns in that file to `src/scripts/post_process_externally_managed_content.py`, to the method `def _get_column_of_external_source_related_to_qc_failure(qc_failure, erroneous_row, external)`. Only add the columns which actually contain values, like xrefs and synonyms, not the columns which contain provenance information.

### Related issues and PRs:

- [Issue: Represent Externally Managed Content in the Mondo Ingest](https://github.com/monarch-initiative/mondo-ingest/issues/439)
- [PR: Add pipeline for externally managed content](https://github.com/monarch-initiative/mondo-ingest/pull/440)