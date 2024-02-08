# MONDO - ICD11FOUNDATION Alignment

**Source name:** International Classification of Diseases 11th Revision

**Source description:** The International Classification of Diseases (ICD) provides a common language that allows health
professionals to  share standardized information across the world. The eleventh revision contains around 17 000 unique 
codes, more than  120 000 codable terms and is now entirely digital.Feb 11, 2022
This data source in particular is the ICD11 foundation, not one of its linearizations.

**Homepage:** https://icd.who.int/

**Comments about this source:**  
_Data source_  
_Original source URL_: https://icd11files.blob.core.windows.net/tmp/whofic-2023-04-08.owl.gz

_Preprocessing_  
In the [monarch-initiative/icd11](https://github.com/monarch-initiative/icd11) repo, We remove unicode characters and 
then remove equivalent class statements as discussed below. 

_Equivalent classes_  
We remove all equivalent class statements as they are not unique and result in unintended node merges. For example 
`icd11.foundation:2000662282` (_Occupant of pick-up truck or van injured in collision with car, pick-up truck or van: 
person on outside of vehicle injured in traffic accident_) has the same exact equivalent concept expression as 
`icd11.foundation:1279712844` (_Occupant of pick-up truck or van injured in collision with two- or three- wheeled motor 
vehicle: person on outside of vehicle injured in traffic accident_).

---

The data pipeline that generates the source is implemented in `make`, in this source file: [src/ontology/mondo-ingest.Makefile](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/mondo-ingest.Makefile).

You can make issues or ask questions about this source [here](https://github.com/monarch-initiative/mondo-ingest/issues).
