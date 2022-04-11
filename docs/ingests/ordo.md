Removed relations:

Orphanet:317343
Orphanet:317344
Orphanet:317345
Orphanet:317346
Orphanet:317348
Orphanet:317349
Orphanet:327767
Orphanet:410295
Orphanet:410296
Orphanet:465410
Orphanet:C016
Orphanet:C017
Orphanet:C020
Orphanet:C022
Orphanet:C025
Orphanet:C026

# Design decisions:

1. We are not importing information that are on obsolete Mondo terms. (MONDO:ObsoleteEquivalent)


Ordo is not really OWL - disease 2 gene, some, some logical
ramona wartz disease can have a mutation in _any_ of these genes.



For every orphanet class that is associated with more than a gene, we should check if that gene is associated with a subclass. If so, we could have a gap. 

Probably the d2g links for gap filling 