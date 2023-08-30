# MONDO - MedGen Alignment

**Source name:** MedGen

**Source description:** Organizes information related to human medical genetics, such as attributes of conditions with a genetic contribution. 

**Homepage:** https://www.ncbi.nlm.nih.gov/medgen/

## Comments about this source:
### Mappings
Mappings are created from [MedGenIDMappings.txt.gz](https://ftp.ncbi.nlm.nih.gov/pub/medgen/MedGenIDMappings.txt.gz) downloadable from MedGen's [FTP site](https://ftp.ncbi.nlm.nih.gov/pub/medgen/).

Predicates: All mappings in that file can be interpreted as `skos:exactMatch`, per verbal confirmation with MedGen staff.

---

The data pipeline that generates the source is implemented in `make`, in this source file: [src/ontology/mondo-ingest.Makefile](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/mondo-ingest.Makefile).

You can make issues or ask questions about this source [here](https://github.com/monarch-initiative/mondo-ingest/issues).
