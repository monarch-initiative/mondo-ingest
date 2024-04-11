# NORD - National Organization for Rare Disorders

**Source name:** NORD - Externally managed content

**Source description:** 

> NORD advances practical, meaningful, and enduring change so people with rare diseases can live their fullest and best lives. Every day, we elevate care, advance research, and drive policy in a purposeful and holistic manner to lift up the rare disease community. (https://rarediseases.org/, 22.02.2024)

NORD provides three datatypes to us:

* Cross-references to NORD content
* Subset-declarations, which basically correspond to "what NORD considers a Rare Disease"
* Preferred Names for certain diseases

The content is provided by an API endpoint at NORD:

```
https://rdbdev.wpengine.com/wp-content/uploads/mondo-export/rare_export.tsv
```

For additional information, see [mondo-ingest.Makefile](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/mondo-ingest.Makefile), in particular the goal called `$(TMPDIR)/nord.tsv:`.


**Homepage:** https://rarediseases.org/

**Comments about this source:** 

The pipeline works like this:

1. The TSV is downloaded from the NORD endpoint
2. A script injects a ROBOT template header into  the TSV and then compiles it into OWL.
3. On the Mondo repo side, we have a script that deletes old NORD content, and merges in the updated version.
4. As of 22.02.2024, the NORD TSV file needs to be manually updated on the NORD side. This does not affect us, but could explain why certain things are not updated in sync with their website. NORD knows about this and tries to find a solution.
