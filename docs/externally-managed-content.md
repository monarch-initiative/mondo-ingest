## Externally managed content

Externally managed content is content that is provided by trusted providers and is merged in _unreviewed_. Currently, we support three types of externally managed content:

1. Preferred names / labels. If a partner organisation of Monarch has a certain preference for a name this can be recorded as part of the metadata.
2. Cross-references and linkouts. Partner organisations can provide cross-references and linkout to important resources related to a disease.
3. Subsets. Partner organisations can provide subset information to Mondo. This is used in a variety of ways, such as:
   - NORD declares which diseases it consideres "rare"
   - Open Targets declares which diseases are used for their drug-prediction framework

### Typical workflows

1. External provider provides a TSV. (Ideally they use the same template that NORD uses - see `src/ontology/external/nord.robot.tsv`).
2. We pull it in and turn it into a ROBOT template and transform it to owl.

### Related issues and PRs:

- [Issue: Represent Externally Managed Content in the Mondo Ingest](https://github.com/monarch-initiative/mondo-ingest/issues/439)
- [PR: Add pipeline for externally managed content](https://github.com/monarch-initiative/mondo-ingest/pull/440)