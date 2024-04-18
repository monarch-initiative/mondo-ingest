# How to add a new source to the Mondo Ingest
In several of the filename patterns below, `*` represents the ontology name/id.

## 1. `mondo-ingest-odk.yaml`
### 1.1. Add source info
Add a new filename and URL to the `products` > `components` section in [src/ontology/mondo-ingest-odk.yaml](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/mondo-ingest-odk.yaml).

### 1.2. Run `update_repo`
From `src/ontology`, run `sh run.sh make update_repo`.

What this does: This will update several files, including the addition of components goals to `src/ontology/Makefile`.

It is possible you may need to run this command twice. The first time will update the update process itself, and the 
second time will run the update.

## 2. More config updates
### 2.1. `metadata/*.yaml`
Add a new metadata file to [src/ontology/metadata](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/metadata). It is important we try and document as much about the source as we can.

### 2.2. `metadata/mondo.sssom.config.yml`
Prefixes need to be entered in the following places in the yml:
- `curie_map`
- `extended_prefix_map`
- `subject_prefixes`

### 2.3. `config/prefixes.csv`
Add prefixes.

### 2.4. `config/context.json`
Add prefixes.

### 2.5. `lexmatch-sssom-compare.py`
There is a section of branching logic with a comment "Map ontology filenames to prefixes". Add an entry there if either
(a) there is 1 prefix you care about, and it is spelled differently than the component filename (e.g. the prefix is 
`myontology`, but the filename is `components/my-ontology.owl`), or (b) there is more than 1 prefix.

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

## 4. The `components/` goal
When `mondo-ingest-odk.yaml` is edited and `update_repo` is run, a new `component-download-SOURCE.owl` goal is added to 
`src/ontology/Makefile`. This essentially downloads a copy of the source. But, for it to be used in `mondo-ingest`, it 
needs to be modified. This is done by creating a `$(COMPONENTSDIR)/omim.owl` goal in `mondo-ingest.Makefile` which runs 
a composite `robot` command. Here are some sections you'll likely want to add that command:  
- `rename --mappings config/SOURCE-property-map.sssom.tsv`: You'll notice that there are two other lines on most goals 
for `property-map.sssom.tsv` and `property-map-2.sssom.tsv`. These handle some common renamings. However, 
if your source has any properties that need to be renamed which are specific to that source, then you should create a 
new file for that. While doing this, it might be useful to check any other `SOURCE-property-map.sssom.tsv` files to see 
if they share any of the same property renamings. If so, it might be a good idea to move them to 
`property-map.sssom.tsv` instead.
- `query --update ../sparql/SPARQL.ru`: There may be more complex modifications that need to be made to the ontology. If
 so, this can be done by 1 or more SPARQL queries.
- `remove -T config/properties.txt --select complement --select properties --trim true`: `properties.txt` contains a 
list of the only allowable properties for any component. If there are any properties in the source that are not in this 
file that you wish to keep, they should be added.

## 5. Everything else
Steps 1-3 take care of the basic setup. Ideally, if everything is automated correctly and the nature of the ontology 
being ingested is not significantly different than what has been ingested before, running `make build-mondo-ingest` 
should include all of the output artefacts and remaining documentation for the new ontology.

However, in practice, because `build-mondo-ingest` takes a long time to run, it might be a good idea to look at each of 
its steps and try running pieces of them to make sure they are working as expected. It might even be a good idea to run 
all of the steps, but with modifications so that you're only running it for the new ontology rather than all of them. 
For example, instead of `make slurp-all` you'd run `make slurp-*`.

There are a few other files that will probably need to be added as well, such as `src/ontology/config/*_exclusions.tsv`.
A full list of such things should be found in [this issue](https://github.com/monarch-initiative/mondo-ingest/issues/2).