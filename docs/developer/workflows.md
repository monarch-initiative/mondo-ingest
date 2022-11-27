# Mondo Ingest Workflows

## Excluded xrefs in Mondo analysis

See [pull request](https://github.com/monarch-initiative/mondo-ingest/pull/35) for details.

To run the analysis.

```
sh run.sh make excluded-xrefs-in-mondo
```

## Mapping progress
These workflows will create a [mapping progress report](../reports/unmapped.md) with statistics, with linked pages for each ontology that show unmapped terms.

#### Makefile goals
1. `reports/%_mapping_status.tsv`: Running this also runs (2). Creates a table of all terms for ontology `%`, along with labels, and other columns `is_excluded`, `is_mapped`, `is_deprecated`.
2. `reports/%_unmapped_terms.tsv`: Running this also runs (1). Creates a table of unmapped terms for ontology `%` and their labels.
3. `unmapped-terms-tables`: Generates (1) and (2) for all ontologies.
4. `unmapped-terms-docs`: Based on the set of (1) and (2) for all ontologies, uses these to create the [mapping progress report](../reports/unmapped.md) and other related pages. 
