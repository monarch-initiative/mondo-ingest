## ORDO / Orphanet Ingest

### Guidance for manual steps for upkeep

#### About Jinja templates and their usage in this project
[Jinja tempates](https://jinja.palletsprojects.com/en/3.1.x/) are special files written in the declarative Jinja 
templating language, meant for preprocessing to generate an output file in another language. They have file extensions 
like `.jinja`, `.jinja2`, etc.

In this project, these templates are used to create SPARQL queries. The specific use case involves Orphanet's "precision
 mapping strings". We have Python scripts that will take the Jinja template, and take a CSV file where these mapping 
strings and their meanings are provided, and it will populate that information into a new SPARQL file.

The files in question are:
- `sparql/ordo-replace-annotation-based-mappings.ru.jinja2`
- `sparql/ordo-mapping-annotations-violation.sparql.jinja2`

#### When and how to create new SPARQL files from Jinja templates
If there is a new `ordo.owl` that has new "precision mapping strings", this will be detected by the QC (Quality Control)
 check process. That process will run `ordo-mapping-annotations-violation.sparql`, which contains a list of all hitherto
 known "precision mapping strings". Here's an example of one of them:

> `NTBT (ORPHA code's Narrower Term maps to a Broader Term)`

If this QC check fails, it means that it has located new "precision mapping strings". If that happens, then the next 
thing to do would be to find those new strings and determine their meaning. A good way to find all the strings is to run
 the command:

> `make report-mapping-annotations` 
 
This should be run from within `src/ontology/`. It will print a JSON report of all the strings, as well as other 
analytics, to the console.

After that, curators should look over the strings and determine their meanings. If there are new strings with new  
meanings, then the following file should be updated:

- `src/ontology/config/ordo-mapping-codes_relationship-curies.csv`

This file contains two columns, `ordo_mapping_code` and `relationship_curie`. The `ordo_mapping_code` column does not 
actually contain precision mapping strings, but contains what are called "ordo mapping codes". These codes can be found 
at the beginning of the precision mapping strings. In the example from earlier, 
`NTBT (ORPHA code's Narrower Term maps to a Broader Term)`, the mapping code would be:

> `NTBT`

So basically, this file should be updated not when there is a new precision mapping string, but when there is a new 
mapping code.

After the new code and its relationship curie has been entered into `ordo-mapping-codes_relationship-curies.csv`, the 
Jinja templates can be re-instantiated via the command:

> `make update-jinja-sparql-queries`

This should be run from within `src/ontology/`. Once the SPARQL queries have been updated, commit and push the changes.   
