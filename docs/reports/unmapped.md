# Mapping progress report
| Ontology                                         | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-------------------------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md)               | 12,542      | 0              | 0                | 0                         | 12,542                                    | 209                       | 12,333                      | 98.3%                     |
| [ICD10CM](./unmapped_icd10cm.md)                 | 97,903      | 16,225         | 0                | 0                         | 81,678                                    | 2,050                     | 79,628                      | 97.5%                     |
| [ICD11FOUNDATION](./unmapped_icd11foundation.md) | 57,874      | 0              | 5,775            | 5,772                     | 52,099                                    | 4,130                     | 47,969                      | 92.1%                     |
| [NCIT](./unmapped_ncit.md)                       | 191,123     | 169,937        | 5,221            | 5,216                     | 15,965                                    | 3,841                     | 12,124                      | 75.9%                     |
| [ORDO](./unmapped_ordo.md)                       | 15,841      | 6,386          | 1,468            | 1,295                     | 9,455                                     | 9,227                     | 228                         | 2.4%                      |
| [OMIM](./unmapped_omim.md)                       | 29,835      | 19,563         | 1,373            | 1,328                     | 8,900                                     | 8,854                     | 46                          | 0.5%                      |
| [DOID](./unmapped_doid.md)                       | 14,398      | 2,676          | 2,503            | 2,490                     | 11,720                                    | 11,669                    | 51                          | 0.4%                      |

`Ontology`: Name of ontology  
`Tot terms`: Total terms in ontology  
`Tot excluded`: Total terms Mondo has excluded from mapping / integrating  
`Tot deprecated`: Total terms that the ontology source itself has deprecated  
`Tot mappable (!excluded, !deprecated)`: Total mappable candidates for Mondo; all terms that are not excluded or 
deprecated.  
`Tot mapped (mappable)`: Total mapped terms (that are mappable in Mondo). Includes exact, broad, and narrow mappings.  
`Tot unmapped (mappable)`: Total unmapped terms (that are mappable in Mondo)  
`% unmapped (mappable)`: % unmapped terms (that are mappable in Mondo)

To run the workflow that creates this data, refer to the [workflows documentation](../developer/workflows.md).