# Mondo Ingest Workflows

## How to run the workflows
Workflows should all be run from the `src/ontology/` directory.  

**Syntax**: `sh run.sh make COMMAND`  
**Example**: `sh run.sh make slurp-all`

#### Prerequisites
1. Updated code: Make sure your clone of `mondo-ingest` is up to date and that you are on the correct branch, e.g.: `git checkout main && git pull`
2. Docker: You need Docker running. [Docker Desktop](https://www.docker.com/products/docker-desktop/) is is really nice, and comes with a GUI too. 
3. Up-to-date container: The container these commands run on is `obolibrary/odkfull`. If you don't have the container downloaded, it should be downloaded automatically when you run a command. However, it is good to keep it up-to-date, which can be done via: (i) Look at the latest version number 'VERSION' in https://github.com/INCATools/ontology-development-kit/releases, and (ii) run `docker pull obolibrary/odkfull:VERSION`. 

---

## Slurp / migration
These workflows will determine slurpable / migratable terms. That is, terms that are candidates for integration into Mondo.

#### Makefile goals
1. `slurp/%.tsv` and `slurp-%`: For a given ontology, determine all slurpable / migratable terms. That is, terms that are candidates for integration into Mondo.
2. `slurp-all`: Runs slurp / migrate for all ontologies.

## Mapping progress
These workflows will create a [mapping progress report](../reports/unmapped.md) with statistics, with linked pages for each ontology that show unmapped terms.

#### Makefile goals
1. `reports/%_mapping_status.tsv`: Running this also runs  `reports/%_unmapped_terms.tsv`. Creates a table of all terms for ontology `%`, along with labels, and other columns `is_excluded`, `is_mapped`, `is_deprecated`.
2. `reports/%_unmapped_terms.tsv`: Running this also runs `reports/%_mapping_status.tsv`. Creates a table of unmapped terms for ontology `%` and their labels.
3. `unmapped-terms-tables`: Generates `reports/%_mapping_status.tsv` and  `reports/%_unmapped_terms.tsv` for all ontologies.
4. `unmapped-terms-docs`: Based on the set of `reports/%_mapping_status.tsv` and  `reports/%_unmapped_terms.tsv` for all ontologies, uses these to create the [mapping progress report](../reports/unmapped.md) and other related pages. 
5. `mapping-progress-report`: Runs `unmapped-terms-tables` and `unmapped-terms-docs`. Creates mapping progress report [mapping progress report](../reports/unmapped.md) and pages for each ontology which list their umapped terms. Also generates `reports/%_mapping_status.tsv` and `reports/%_unmapped_terms.tsv` for all ontologies.

## Mapped deprecated terms
These workflows will create a [report of deprecated terms with Mondo xrefs](../reports/mapped_deprecated.md) with statistics, with linked pages for each ontology that show deprecated terms with existing xrefs in Mondo.

#### Makefile goals
1. `reports/%_mapped_deprecated_terms.robot.template.tsv`: A table of all of the deprecated terms from a given ontology that have existing mappings in Mondo.
2. `mapped-deprecated-terms-artefacts`: Creates a reports/%_mapped_deprecated_terms.robot.template.tsv for all ontologies.
3. `mapped-deprecated-terms-docs`: Creates a report of statistics for mapped deprecated terms (docs/reports/mapped_deprecated.md) and pages for each ontology which list their deprecated terms with existing xrefs in Mondo.
4. `mapped-deprecated-terms`: Creates a report of statistics for mapped deprecated terms (docs/reports/mapped_deprecated.md) and pages for each ontology which list their deprecated terms with existing xrefs in Mondo. Also creates a reports/%_mapped_deprecated_terms.robot.template.tsv for all ontologies.


## Exclusions
These workflows will help with excluding certain terms from integration into Mondo.

#### Makefile goals
1. `reports/%_term_exclusions.txt`: A list of terms to exclude from integration into Mondo from the given ontology.
2. `reports/%_exclusion_reasons.ttl`: A list of terms to exclude from integration into Mondo from the given ontology, in TTL format.
3. `reports/%_excluded_terms_in_mondo_xrefs.tsv`: A list of terms excluded from integration in Mondo that still have xrefs in Mondo.
4. `excluded-xrefs-in-mondo` and `reports/excluded_terms_in_mondo_xrefs.tsv`: Runs `reports/%_excluded_terms_in_mondo_xrefs.tsv` for all ontologies.
5. `exclusions-%`: Runs `reports/%_term_exclusions.txt`, `reports/%_exclusion_reasons.ttl`, and `reports/%_excluded_terms_in_mondo_xrefs.tsv` for a given ontology.
6. `reports/excluded_terms.ttl`: Runs reports/%_exclusion_reasons.ttl for all ontologies. and combines into a single file.
7. `reports/excluded_terms.txt`: Runs reports/%_term_exclusions.txt for all ontologies and combines into a single file.
8. `reports/exclusion_reasons.robot.template.tsv`: Runs reports/%_exclusion_reasons.robot.template.tsv for all ontologies and combines into a single file. 
9. `exclusions-all`: Runs all exclusion artefacts for all ontologies.
