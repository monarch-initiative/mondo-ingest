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
These workflows will determine slurpable / migratable terms. That is, terms that are candidates for integration into 
Mondo.

#### What determines what is a slurpable / migratable term?
To be migratable, the term (i) must not already be mapped, (ii) must not be excluded (e.g. not in 
`reports/%_term_exclusions.txt`), and (iii) must not be deprecated / obsolete. Then, (iv) there are conditions 
concerning its parents. It must either (a) have no parents, or (b) have no valid parents in Mondo (i.e. all of its 
parent terms are marked obsolete in Mondo), or (c) all its parents must be mapped, and at least 1 of those parent's 
mappings must be one of `skos:exactMatch` or `skos:NarrowMatch`.  

#### Makefile goals
1. `slurp/%.tsv` and `slurp-%`: For a given ontology, determine all slurpable / migratable terms. That is, terms that 
are candidates for integration into Mondo.
2. `slurp-all`: Runs slurp / migrate for all ontologies.
3. `slurp-docs`: Creates a [page](../reports/migrate.md) listing 'n' migratable terms by ontology as well as and pages 
for each ontology with more detailed information.

## Mapping progress
These workflows will create a [mapping progress report](../reports/unmapped.md) with statistics, with linked pages for each ontology that show unmapped terms.

#### Makefile goals
1. `reports/%_mapping_status.tsv`: Running this also runs / generates  `reports/%_unmapped_terms.tsv`. Creates a table of all terms for ontology `%`, along with labels, and other columns `is_excluded`, `is_mapped`, `is_deprecated`.
2. `reports/%_unmapped_terms.tsv`: Running this also runs / generates `reports/%_mapping_status.tsv`. Creates a table of unmapped terms for ontology `%` and their labels.
3. `unmapped-terms-tables`: Generates `reports/%_mapping_status.tsv` and  `reports/%_unmapped_terms.tsv` for all ontologies.
4. `unmapped-terms-docs`: Based on the set of `reports/%_mapping_status.tsv` and  `reports/%_unmapped_terms.tsv` for all ontologies, uses these to create the [mapping progress report](../reports/unmapped.md) and other related pages. 
5. `mapping-progress-report`: Runs `unmapped-terms-tables` and `unmapped-terms-docs`. Creates mapping progress report [mapping progress report](../reports/unmapped.md) and pages for each ontology which list their umapped terms. Also generates `reports/%_mapping_status.tsv` and `reports/%_unmapped_terms.tsv` for all ontologies.
6. `unmapped/%-unmapped.owl`: Creates an OWL component of the ontology which consists only of the subset of terms which are current mapping candidates.
7. `recreate-unmapped-components`: Runs unmapped/%-unmapped.owl for all ontologies.

## Mapped deprecated terms
These workflows will create a [report of deprecated terms with Mondo xrefs](../reports/mapped_deprecated.md) with statistics, with linked pages for each ontology that show deprecated terms with existing xrefs in Mondo.

#### Makefile goals
1. `reports/%_mapped_deprecated_terms.robot.template.tsv`: A table of all of the deprecated terms from a given ontology that have existing mappings in Mondo.
2. `mapped-deprecated-terms-artefacts`: Creates a reports/%_mapped_deprecated_terms.robot.template.tsv for all ontologies.
3. `mapped-deprecated-terms-docs`: Creates a report of statistics for [mapped deprecated terms](../reports/mapped_deprecated.md) and pages for each ontology which list their deprecated terms with existing xrefs in Mondo, where these terms have not yet been marked as deprecated in Mondo.
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

## Synchronization
These workflows help synchronize Mondo with source ontologies.

### Sub-class of
#### Makefile goals
1. `generate-synchronization-files`: Runs synchronization pipeline.
2. `sync-subclassof`: Runs 'sync-subclassof' part of synchronization pipeline, generating set of outputs for all ontologies.
3. `sync-subclassof-%`: Generates subClassOf synchronization outputs for given ontology. Alias for `reports/%.subclass.added.robot.tsv`, `reports/%.subclass.confirmed.robot.tsv`, and `reports/%.subclass.direct-in-mondo-only.tsv`.
4. `reports/%.subclass.added.robot.tsv`: Creates robot template containing new subclass relationships from given ontology to be imported into Mondo. Running this also runs / generates `reports/%.subclass.added-obsolete.robot.tsv`, `reports/%.subclass.confirmed.robot.tsv`, and `reports/%.subclass.direct-in-mondo-only.tsv`.
5. `reports/%.subclass.added-obsolete.robot.tsv`: Creates robot template containing new subclass relationships from given ontology that would be imported into Mondo, except for that these terms are obsolete in Mondo. Running this also runs / generates `reports/%.subclass.added.robot.tsv`, `reports/%.subclass.confirmed.robot.tsv`, and `reports/%.subclass.direct-in-mondo-only.tsv`.
6. `reports/%.subclass.confirmed.robot.tsv`: Creates robot template containing subclass relations for given ontology that exist in Mondo and are confirmed to also exist in the source. Running this also runs / generates `reports/%.subclass.added.robot.tsv`, `reports/%.subclass.added-obsolete.robot.tsv`, and `reports/%.subclass.direct-in-mondo-only.tsv`.
7. `reports/%.subclass.direct-in-mondo-only.tsv`: Path to create file for relations for given ontology where direct subclass relation exists only in Mondo and not in the source. Running this also runs / generates `reports/%.subclass.added.robot.tsv`, `reports/%.subclass.added-obsolete.robot.tsv`, and `reports/%.subclass.confirmed.robot.tsv`.
8. `reports/sync-subClassOf.direct-in-mondo-only.tsv`: For all subclass relationships in Mondo, shows which sources do not have it and whether no source has it. Combination of all `--outpath-direct-in-mondo-only` outputs for all sources, using those as inputs, and then deletes them after.
9. `reports/sync-subClassOf.confirmed.tsv`: For all subclass relationships in Mondo, by source, a robot template containing showing what is in Mondo and are confirmed to also exist in the source. Combination of all `--outpath-confirmed` outputs for all sources.

### Synonyms
#### Makefile goals
1. `sync-synonyms`: Runs 'sync-synonyms' part of synchronization pipeline, creating outputs for all sources for each of the 4 cases - 'added', 'confirmed', 'updated', and 'deleted'.
2. `reports/%.subclass.added.robot.tsv`: ROBOT template TSV to create which will contain synonyms that aren't yet integrated into Mondo for all mapped source terms.
3. `reports/%.subclass.confirmed.robot.tsv`: ROBOT template TSV to create which will contain synonym confirmations; combination of synonym scope predicate and synonym string exists in both source and Mondo for a given mapping.
4. `reports/%.subclass.deleted.robot.tsv`: ROBOT template TSV to create which will contain synonym deletions; exists in Mondo but not in source(s) for a given mapping.
5. `reports/%.subclass.updated.robot.tsv`: ROBOT template TSV to create which will contain updates to synonym scope predicate; cases where the synonym exists in Mondo and on the mapped source term, but the scope predicate is different.
6. `reports/sync-synonyms.added.tsv`: Combination of all 'added' synonym outputs for all sources.
7. `reports/sync-synonyms.confirmed.tsv`: Combination of all 'confirmed' synonym outputs for all sources.
8. `reports/sync-synonyms.updated.tsv`: Combination of all 'updated' synonym outputs for all sources.
