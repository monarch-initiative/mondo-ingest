# Mapping progress report
| Ontology                                         | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-------------------------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md)               | 12,542      | 0              | 0                | 0                         | 12,542                                    | 18                        | 12,524                      | 99.9%                     |
| [ICD10CM](./unmapped_icd10cm.md)                 | 95,847      | 15,452         | 0                | 0                         | 80,395                                    | 1,166                     | 79,229                      | 98.5%                     |
| [ICD11FOUNDATION](./unmapped_icd11foundation.md) | 57,874      | 0              | 5,775            | 5,772                     | 52,099                                    | 4,104                     | 47,995                      | 92.1%                     |
| [NCIT](./unmapped_ncit.md)                       | 191,123     | 169,937        | 5,221            | 5,216                     | 15,965                                    | 3,840                     | 12,125                      | 75.9%                     |
| [DOID](./unmapped_doid.md)                       | 14,372      | 2,675          | 2,502            | 2,490                     | 11,695                                    | 11,442                    | 253                         | 2.2%                      |
| [ORDO](./unmapped_ordo.md)                       | 15,632      | 6,310          | 1,444            | 1,272                     | 9,322                                     | 9,196                     | 126                         | 1.4%                      |
| [OMIM](./unmapped_omim.md)                       | 29,746      | 19,511         | 1,373            | 1,326                     | 8,863                                     | 8,839                     | 24                          | 0.3%                      |

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