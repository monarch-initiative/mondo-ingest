# Mapping progress report
| Ontology                                         | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-------------------------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md)               | 12,597      | 0              | 0                | 0                         | 12,597                                    | 209                       | 12,388                      | 98.3%                     |
| [ICD10CM](./unmapped_icd10cm.md)                 | 97,903      | 16,225         | 0                | 0                         | 81,678                                    | 2,066                     | 79,612                      | 97.5%                     |
| [ICD11FOUNDATION](./unmapped_icd11foundation.md) | 57,874      | 0              | 5,775            | 5,773                     | 52,099                                    | 4,594                     | 47,505                      | 91.2%                     |
| [NCIT](./unmapped_ncit.md)                       | 209,933     | 186,872        | 5,614            | 5,608                     | 17,447                                    | 3,810                     | 13,637                      | 78.2%                     |
| [DOID](./unmapped_doid.md)                       | 14,797      | 2,695          | 2,515            | 2,496                     | 12,101                                    | 11,882                    | 219                         | 1.8%                      |
| [ORDO](./unmapped_ordo.md)                       | 15,841      | 6,391          | 1,468            | 1,293                     | 9,450                                     | 9,372                     | 78                          | 0.8%                      |
| [OMIM](./unmapped_omim.md)                       | 30,303      | 19,860         | 1,383            | 1,333                     | 9,064                                     | 9,014                     | 50                          | 0.6%                      |

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