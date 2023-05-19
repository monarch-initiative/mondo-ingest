# Mapping progress report
| Ontology                           | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-----------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md) | 12,542      | 0              | 0                | 0                         | 12,542                                    | 18                        | 12,524                      | 99.9%                     |
| [ICD10CM](./unmapped_icd10cm.md)   | 95,847      | 15,452         | 0                | 0                         | 80,395                                    | 1,161                     | 79,234                      | 98.6%                     |
| [NCIT](./unmapped_ncit.md)         | 174,300     | 154,519        | 5,055            | 5,022                     | 14,726                                    | 3,680                     | 11,046                      | 75.0%                     |
| [DOID](./unmapped_doid.md)         | 13,699      | 2,628          | 2,475            | 2,447                     | 11,070                                    | 10,911                    | 159                         | 1.4%                      |
| [ORDO](./unmapped_ordo.md)         | 10,866      | 1,720          | 1,418            | 844                       | 9,146                                     | 9,029                     | 117                         | 1.3%                      |
| [OMIM](./unmapped_omim.md)         | 28,750      | 18,962         | 1,353            | 1,309                     | 8,435                                     | 8,434                     | 1                           | 0.0%                      |

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