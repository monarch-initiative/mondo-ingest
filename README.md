# Mondo Source Ingest

This repo is dedicated to the integration of various clinical terminologies and ontologies into Mondo. For more details 
see the [documentation](https://monarch-initiative.github.io/mondo-ingest/).

Work on the Mondo Source Ingest is funded by the _NHGRI Phenomics First Grant 1RM1HG010860-01_.

## Prerequisites
Python is a dev dependency. It's not needed to run the docker containers, but needed for local development situations 
/ debugging.
1. Python 3.9+
2. Docker
3. Docker images  
  One or both of the following, depending on if you want to run the stable build `latest` or `dev`:
    - a. `docker pull obolibrary/odkfull:latest`
    - b. `docker pull obolibrary/odkfull:dev`
4. Optional: [`odkrunner`](https://github.com/gouttegd/odkrunner): Alternative to `run.sh`. If using this, you would run
    like `odkrun make build-mondo-ingest` instead of `sh run.sh make build-mondo-ingest`. Suggestion: rename the binary 
    to `odk`; this is the convention of `mondo-ingest` developers. 

## Running
### Full build
`sh run.sh make build-mondo-ingest`

### [Workflows](./docs/developer/workflows.md)

## Reports
A variety of reports are committed as static files in `src/ontology/reports/` and are documented in the 
[reports codebook](src/ontology/reports/README.md), but some additional reports get rendered into markdown pages as 
noted below.

### Mapping progress report
The [mapping progress report](./docs/reports/unmapped.md) consists lists of all unmapped terms fo each ontology, as well 
as a table of statistics showing total number of terms, excluded terms, deprecated terms, and unmapped terms.

### Mapped deprecated terms
The [_mapped deprecated terms_ page](./docs/reports/mapped_deprecated.md) contains a table of statistics showing total number of deprecated terms that 
have existing xrefs in Mondo, for each ontology. There is also a link to a page for each ontology which shows the term 
IDs and their corresponding mapped Mondo ID(s). 

### Migratable terms
The [_migrate_ page](./docs/reports/migrate.md) contains a table of statistics showing of terms ready for migration / 
integration into Mondo.
