# How to add a new source to the Mondo Ingest
In several of the filename patterns below, `*` represents the ontology name/id.

## 1. `mondo-ingest-odk.yaml`
### 1.1. Add source info
Add a new filename and URL to the `products` > `components` section in [src/ontology/mondo-ingest-odk.yaml](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/mondo-ingest-odk.yaml).

### 1.2. `update_repo`
From `src/ontology`, run `sh run.sh make update_repo`.

What this does: This will update several files, including the addition of components goals to src/ontology/Makefile.

It is possible you may need to run this command twice. The first time will update the update process itself, and the 
second time will run the update.


## 2. `metadata/*.yaml`
Add a new metadata file to [src/ontology/metadata](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/metadata). It is important we try and document as much about the source as we can.

## 3. Docs 
### 3.1. `mkdocs.yaml`
Update the Website Table of Contents in [mkdocs.yaml](https://github.com/monarch-initiative/mondo-ingest/blob/main/mkdocs.yaml)

### 3.2. `docs/sources/*.md`
Run `sh run.sh make ../../docs/sources/*.md` from `src/ontology`. Then edit it manually to add any more informatoin.

### 3.3. `docs/sources.md`
Add a link to your new `.md` file created in the last step.

### 3.4. `docs/metrics/*.md`
Run `sh run.sh make ../../docs/metrics/*.md` from `src/ontology`.

### 3.5. `docs/metrics.md`
Add a link to your new `.md` file created in the last step.
