# Mondo Source Ingest

This repo is dedicated to the integration of various clinical terminologies and ontologies into Mondo. For more details 
see the [documentation](https://monarch-initiative.github.io/mondo-ingest/).

Work on the Mondo Source Ingest is funded by the NHGRI Phenomics First Grant 1RM1HG010860-01.

## Workflows
A variety of workflows are available to run the ingest. See the [workflows documentation](./docs/developer/workflows.md) for more details.

## Reports
### Mapping progress report
The [mapping progress report](./docs/reports/unmapped.md) consists lists of all umapped terms fo each ontology, as well 
as a table of statistics showing total number of terms, excluded terms, deprecated terms, and unmapped terms.

### Mapped deprecated terms
The [mapped deprecated terms](./docs/reports/mapped_deprecated.md) contains a table of statistics showing total number of deprecated terms that have existing xrefs in Mondo, for each ontology. There is also a link to a page for each ontology which shows the term IDs and their corresponding mapped Mondo ID(s). 
