# MONDO - GARD Alignment

**Source name:** Genetic and Rare Diseases

**Source description:**  Genetic and Rare Diseases (GARD) Information Center is a public health resource that aims to support people living with a rare disease and their families with free access to reliable, easy to understand information. 

**Homepage:** https://rarediseases.info.nih.gov/

## Comments about this source:
### [README](https://docs.google.com/document/d/1sM0B0ICdOWDwZWt0M_Y3t5QYwqL-XwOsDl3TS14XRa4/edit#): GARD::Mondo mappings analysis
#### About the [spreadsheet](https://docs.google.com/spreadsheets/d/1w5Xnzr5uNFcPrQqCT8mGBFHnGhwXDfQVzHKofw6kB7c/edit#gid=1607652739)
1. `gard.sssom+`: This is a SSSOM of GARD mappings. For how predicate_id’s were chosen, see “Assumptions” section below.
Additional columns added: mondo_id, mondo_label, and gard_mondo_mapping_type (which has 3 values: `direct_existing` (
taken from [mondo_hasdbxref_gard.sssom.tsv](https://raw.githubusercontent.com/monarch-initiative/mondo/master/src/ontology/mappings/mondo_hasdbxref_gard.sssom.tsv))
, `new_proxy`, and `unmapped_proxy_or_direct` (which is same as the `gard_unmapped_terms` sheet). 
2. `gard_unmapped_terms`: A flat list of GARD IDs that do not have existing mappings in Mondo, and no new proxy mappings found.
3. `GARD source data`: Copy of source CSV provided by GARD.
4. `gard_terms_mapping_status`: This output was mainly for us to provide to the GARD folks. This allows us to see at a 
glance the GARD IDs that exist in the GARD data source as well as in our current Mondo mappings.
5. `obsoleted_gard_terms_in_mondo`: This output was initially for us to provide to the GARD folks.This is a flat list of
 GARD IDs that have xrefs in Mondo but are no longer in GARD.

#### Assumptions
**Parent/Child relationships**  
The [GARD source data](https://docs.google.com/spreadsheets/d/1w5Xnzr5uNFcPrQqCT8mGBFHnGhwXDfQVzHKofw6kB7c/edit#gid=885755208)
has a ParentGardID column is formatted just like a Python list, comma delimited, with opening and closing brackets 
(`[` and `]`). All IDs here are considered instances of `rdfs:subClassOf` for the given record.

**Mappings**  
Joe and Nico interpreted the [GARD source data](https://docs.google.com/spreadsheets/d/1w5Xnzr5uNFcPrQqCT8mGBFHnGhwXDfQVzHKofw6kB7c/edit#gid=885755208) 
and tried to determine the best predicates to use for mappings. The results are in the [`gard.sssom+` sheet](https://docs.google.com/spreadsheets/d/1w5Xnzr5uNFcPrQqCT8mGBFHnGhwXDfQVzHKofw6kB7c/edit#gid=1504531712). 
This only applies to those rows where `gard_mondo_mapping_type`==`proxy_new`.
1. **GARD::Orphanet**: `skos:exactMatch`: Where `DataSource`==`Orphanet`, value from the `SourceID` column is an Orphanet ID.
2. **GARD::Orphanet**: `skos:broadMatch`: There is a `ParentOrphaCode` column. Any IDs from that column are considered broad matches.
3. **GARD::OMIM**: `skos:exactMatch`: I’m unsure why they called it "`Orphanet+OMIM`", but based on what Yanji said, where 
`DataSource`==`Orphanet+OMIM`, the value in the `SourceID` column is an OMIM ID.
4. **GARD::OMIM**: `skos:narrowMatch`: These come from the `OmimMember` column. Rows has 0 to many MIM#s in that column. 
Exception 1: when `DataSource`==`Orphanet+OMIM`. In that case, there is only 1 item in `OmimMember`, and it is equal to what 
is in the `SourceID` column and considered an exact match. Exception 2: when `DataSource`==`GARD`, these are considered 
related matches. Yanji told Joe that these rows are in development, so perhaps they might be exact, narrow, or perhaps 
even broad.
5. **GARD::OMIM**: `skos:relatedMatch`: For rows where `DataSource`==`GARD` (n=10), some of these rows have values in the 
`OmimMember` column (n=5). In all these cases, it’s just 1 MIM#. Yanji mentioned in email that these rows were 
tentative / being worked on. So I felt that without asking or taking a closer look, I was unsure if these would be 
narrow or exact matches.

#### Misc notes
1. Where `DataSource` `Orphanet+OMIM`: what IDs are these? OMIM or Orphanet? **Answer: OMIM**
2. Do any rows where `DataSource`==`Orphanet+OMIM` have multiple OMIM mappings in the `OmimMember` column? **Answer: No**
3. What values are in the `DataSource` column? **Answer: `GARD`, `Orphanet`, and `Orphanet+OMIM`**

#### Discussion
**Joe 2023/04/23**  
New results:  
**Unmapped GARD terms**: 181 of 12004 (1.51%)  
**Mapped GARD terms**: 11823 of 12004 (98.49%)  

I fixed the issue where I was accidentally mapping to ORDO IDs that should have been OMIM IDs. I also found some new 
columns to map to. I versioned the [spreadsheet](https://docs.google.com/spreadsheets/d/1w5Xnzr5uNFcPrQqCT8mGBFHnGhwXDfQVzHKofw6kB7c/edit#gid=1607652739), 
then updated it. The main sheet we want to look at now [is `gard.sssom+`](https://docs.google.com/spreadsheets/d/1w5Xnzr5uNFcPrQqCT8mGBFHnGhwXDfQVzHKofw6kB7c/edit#gid=1504531712).

I think you guys should review my notes in the readme to see how I determined mappings. I also added comments to some 
column headers explaining its contents and how I interpreted those fields.

I imagine you guys will be happy by this much higher mapping %! But also you will wonder why the number of unmapped 
GARD terms (n=181) is higher than the unmapped ORDO+OMIM terms (n=130). I copied the table below from the [progress 
monitor](https://github.com/monarch-initiative/mondo-ingest/blob/main/docs/reports/unmapped.md). I also got the actual 
Mondo::GARD mappings from the `mondo` repository rather than the hacky `grep` method I was using before. This resulted 
in 10 new existing Mondo::GARD mappings that weren't there in the last run. FYI, the GARD IDs in that TSV from Mondo 
are 0-padded, while the official GARD IDs are not.

| Ontology | Tot unmapped (mappable) |
|:----------|:-----|
| ORDO       | 124  |
| OMIM       | 6      |

Of the 12,410 GARD terms, 5 of them have no Orphanet or OMIM mapping. But the unmapped number is still higher than 
expected. Some reasons why this could be happening:
a. Perhaps GARD is mapping to some deprecated terms.
b. Perhaps GARD is mapping to some terms not showing up in our ingest for some reason.
c. Probably some other reason, but I'm not sure yet.

I think probably at this stage, figuring the rest of these mappings out is probably better done by manual curation than 
scripting, but if there is more work I can do that you guys think would be helpful, or if you notice errors in any of 
my assumptions, I can fix the script and rerun.

---

The data pipeline that generates the source is implemented in `make`, in this source file: [src/ontology/mondo-ingest.Makefile](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/mondo-ingest.Makefile).

You can make issues or ask questions about this source [here](https://github.com/monarch-initiative/mondo-ingest/issues).
