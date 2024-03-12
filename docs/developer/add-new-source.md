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

## 2. More config updates
### 2.1. `metadata/*.yaml`
Add a new metadata file to [src/ontology/metadata](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/metadata). It is important we try and document as much about the source as we can.

### 2.2. `metadata/mondo.sssom.config.yml`
Prefixes need to be entered in the following places in the yml:
- `curie_map`
- `extended_prefix_map`

### 2.3. `config/prefixes.csv`
Add prefixes.

### 2.4. `config/context.json`
Add prefixes.

## 3. Docs 
### 3.1. `mkdocs.yaml`
Update the Website Table of Contents in [mkdocs.yaml](https://github.com/monarch-initiative/mondo-ingest/blob/main/mkdocs.yaml)

### 3.2. `docs/sources/*.md`
Run `sh run.sh make ../../docs/sources/*.md` from `src/ontology`. Then edit it manually to add any more information.

### 3.3. `docs/sources.md`
Add a link to your new `.md` file created in the last step.

### 3.4. `docs/metrics/*.md`
Run `sh run.sh make ../../docs/metrics/*.md` from `src/ontology`.

### 3.5. `docs/metrics.md`
Add a link to your new `.md` file created in the last step.

## 4. Everything else
Steps 1-3 take care of the basic setup. Ideally, if everything is automated correctly and the nature of the ontology 
being ingested is not significantly different than what has been ingested before, running `make build-mondo-ingest` 
should include all of the output artefacts and remaining documentation for the new ontology.

However, in practice, because `build-mondo-ingest` takes a long time to run, it might be a good idea to look at each of 
its steps and try running pieces of them to make sure they are working as expected. It might even be a good idea to run 
all of the steps, but with modifications so that you're only running it for the new ontology rather than all of them. 
For example, instead of `make slurp-all` you'd run `make slurp-*`.

There are a few other files that will probably need to be added as well, such as `src/ontology/config/*_exclusions.tsv`.
A full list of such things should be found in [this issue](https://github.com/monarch-initiative/mondo-ingest/issues/2).