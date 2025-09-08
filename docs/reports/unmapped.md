# Mapping progress report
| Ontology                                         | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-------------------------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md)               | 12,542      | 0              | 0                | 0                         | 12,542                                    | 209                       | 12,333                      | 98.3%                     |
| [ICD10CM](./unmapped_icd10cm.md)                 | 97,903      | 16,225         | 0                | 0                         | 81,678                                    | 2,050                     | 79,628                      | 97.5%                     |
| [ICD11FOUNDATION](./unmapped_icd11foundation.md) | 57,874      | 0              | 5,775            | 5,772                     | 52,099                                    | 4,130                     | 47,969                      | 92.1%                     |
| [NCIT](./unmapped_ncit.md)                       | 203,691     | 181,107        | 5,495            | 5,458                     | 17,089                                    | 3,810                     | 13,279                      | 77.7%                     |
| [ORDO](./unmapped_ordo.md)                       | 15,841      | 6,386          | 1,468            | 1,295                     | 9,455                                     | 9,227                     | 228                         | 2.4%                      |
| [DOID](./unmapped_doid.md)                       | 14,452      | 2,679          | 2,506            | 2,490                     | 11,771                                    | 11,665                    | 106                         | 0.9%                      |
| [OMIM](./unmapped_omim.md)                       | 29,901      | 19,609         | 1,375            | 1,328                     | 8,920                                     | 8,854                     | 66                          | 0.7%                      |

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