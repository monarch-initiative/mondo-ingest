# Architecture of the Ingest Pipeline

To synchronise with external ontologies, we employ a data pipeline that downloads, cleans, maps and ingests external terminologies, called the "Symbiont Pipeline". 

_Goals of the Symbiont pipeline:_

1. To migrate terms from a source terminology (or ontology) to another target ontology
2. To keep migrated terms in the target ontology in sync with the source ontology

We will describe it in detail in the following.

## Pipeline overview

_Input_:
- Source Ontology (O_s): the origin of the terms to be ingested
- Target Ontology (O_t): the ontology to which the terms should be migrated
- Source Target Mapping (M): a mapping file between terms in the Source ontology and terms in the Target ontology.
- Terms to migrate (T): A list of terms to migrate from O_s to O_t.
- Source Schema (S): a schema for the source ontology, describing which properties are allowed, which axiom structures and basic rules over literal values.
- Excluded axioms (Ex): A list of axioms that were manually rejected from the migration.

1. Preprocessing: _Extract_ the portion of interest from the source ontology and _transform_ it to conform to the source schema.
2. Mapping: Map previously unmapped terms between the source and the target ontology (optional)
3. Migration: Migrate terms from the source to the target ontology
4. Postprocessing: Review terms to migrate, reject or accept new assertions

### Preprocessing phase

Ontologies come in a number of shapes and forms, using different relationships for classification, different annotation properties for synonys and definitions and so on. The goal of the preprocessing phase is to `transform the source ontology into the Mondo schema`.

