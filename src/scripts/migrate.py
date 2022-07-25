"""Migration pipeline

#### THIS IS PSEUDO CODE NOT PYTHON OR ANYTHING
#### THIS IS PSEUDO CODE NOT PYTHON OR ANYTHING
#### THIS IS PSEUDO CODE NOT PYTHON OR ANYTHING
#### THIS IS PSEUDO CODE NOT PYTHON OR ANYTHING

TODOs:
  - add CLI: look to makefile for what to include
"""
import oakliblib
import pandas


#Inputs:
source_ontology = ''  #e.g. omim
sssom_map = ''  # e.g. mondo.sssom.tsv
min_id = ''
termlist_mondo = ''


def run(source_ontology = '', sssom_map = '', min_id = '', termlist_mondo = ''):
    """source_ontology = ''  #e.g. omim
    sssom_map = ''  # e.g. mondo.sssom.tsv
    min_id = ''
    termlist_mondo = ''"""
    #Outputs:
    data = []

    for t in source_ontology:
        if t not in sssom_map['object_id']:
            parents = []
            migrate = True
            for p in oaklib.get_direct_parents(t):
                if p not in sssom_map['object_id']:
                    migrate = False
                    break
                elif sssom_map[sssom_map['object_id']==p]['predicate_id'] = 'skos:exactMatch' \
                    or sssom_map[sssom_map['object_id']==p]['predicate_id'] = 'skos:narrowMatch':
                    # In other words, if the parent is mapped, and the mapping is either exact or narrower
                    parents.append(sssom_map[sssom_map['object_id']==p]['subject_id'])
                else:
                    # Its fine, just continue looking for other parents in this case
            if migrate and parents:
                next_mondo_id = determine_next_available_mondo_id(min_id, termlist_mondo) # satrting from min_id, then counting up and checking if it does not already exist.
                label = oaklib.get_label(t)
                definition = oaklib.get_definition(t)
                data.append({'mondo_id':next_mondo_id, 'xref': t, 'label': label, 'definition': definition})

    pandas.DataFrame(data).to_csv(fn, sep="\t")


if __name__ == '__main__':
    run()
