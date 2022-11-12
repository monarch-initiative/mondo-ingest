import logging
from os.path import abspath, dirname, join

import click
import pandas as pd
from oaklib import OntologyResource
from oaklib.implementations import SqlImplementation
from sssom import compare_dataframes
from sssom.parsers import parse_sssom_table, split_dataframe
from sssom.util import MappingSetDataFrame

SRC = dirname(dirname(abspath(__file__)))
MAPPINGS = join(SRC, "mappings")
ONTS_DIR = join(SRC, "ontology")
LEXMATCH_DIR = join(ONTS_DIR, "lexmatch")
MONDOMATCH_DIR = join(ONTS_DIR, "mondo-match")
SPLIT_DIR = join(ONTS_DIR, "split-mapping-set")
TMP = join(ONTS_DIR, "tmp")
REPORTS_DIR = join(ONTS_DIR, "reports")
MONDO_SSSOM = join(TMP, "mondo.sssom.tsv")
DB_FILE = join(TMP, "merged.db")

EXCLUSION_FILES = [
    join(REPORTS_DIR, "doid_term_exclusions.txt"),
    join(REPORTS_DIR, "omim_term_exclusions.txt"),
    join(REPORTS_DIR, "ordo_term_exclusions.txt"),
    join(REPORTS_DIR, "ncit_term_exclusions.txt"),
    join(REPORTS_DIR, "icd10cm_term_exclusions.txt"),
]

input_argument = click.argument("input", required=True, type=click.Path())


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
def main(verbose: int, quiet: bool):
    """Run the SSSOM CLI."""
    logger = logging.getLogger()
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)


@main.command()
@input_argument
def run(input: str):
    msdf_lex = parse_sssom_table(join(MAPPINGS, input))
    msdf_mondo = parse_sssom_table(MONDO_SSSOM)
    # Get the exclusion list
    exclusion_list = []
    for file_path in EXCLUSION_FILES:
        with open(file_path) as f_input:
            exclusion_list.extend(f_input.read().split("\n"))

    all_lex_ids = mapped_curie_list(msdf_lex.df)
    all_mondo_ids = mapped_curie_list(msdf_mondo.df)

    in_lex_but_not_mondo_list = [
        x for x in all_lex_ids if x not in all_mondo_ids and x not in exclusion_list
    ]
    in_mondo_but_not_lex_list = [
        x for x in all_mondo_ids if x not in all_lex_ids and x not in exclusion_list
    ]

    ontology_resource = OntologyResource(slug=DB_FILE, local=True)
    oi = SqlImplementation(ontology_resource)
    msdf_mondo.df["object_label"] = msdf_mondo.df["object_id"].apply(lambda x: oi.label(x))

    condition_1 = msdf_mondo.df["subject_id"].str.contains("MONDO")
    condition_2 = msdf_mondo.df["object_id"].str.contains("ICD10CM")
    condition_3 = msdf_mondo.df["object_id"].str.contains("|".join((["OMIM", "OMIMPS"])))
    condition_4 = msdf_mondo.df["object_id"].str.contains("Orphanet")
    condition_5 = msdf_mondo.df["object_id"].str.contains("DOID")
    condition_6 = msdf_mondo.df["object_id"].str.contains("NCIT")
    condition_7 = msdf_lex.df["subject_id"].str.contains("MONDO")

    mondo_icd_df = msdf_mondo.df[condition_1 & condition_2]
    mondo_omim_df = msdf_mondo.df[condition_1 & condition_3]
    mondo_ordo_df = msdf_mondo.df[condition_1 & condition_4]
    mondo_doid_df = msdf_mondo.df[condition_1 & condition_5]
    mondo_ncit_df = msdf_mondo.df[condition_1 & condition_6]

    condition_mondo_obj = msdf_lex.df["object_id"].str.contains("MONDO")

    non_mondo_subjects_df = pd.DataFrame(msdf_lex.df[(~condition_7 & condition_mondo_obj)])
    mondo_subjects_df = pd.DataFrame(msdf_lex.df[(condition_7 & ~condition_mondo_obj)])
    print(len(mondo_subjects_df))
    non_mondo_subjects_df.head()

    desired_sequence = [
        "subject_id",
        "subject_label",
        "object_id",
        "predicate_id",
        "object_label",
        "mapping_justification",
        "mapping_tool",
        "confidence",
        "subject_match_field",
        "object_match_field",
        "match_string",
    ]

    new_subjects_df = non_mondo_subjects_df.rename(
        columns={
            "subject_id": "object_id",
            "subject_label": "object_label",
            "object_id": "subject_id",
            "object_label": "subject_label",
            "subject_match_field": "object_match_field",
            "object_match_field": "subject_match_field",
        }
    )

    new_subjects_df = new_subjects_df[desired_sequence]
    new_subjects_df["predicate_id"] = new_subjects_df["predicate_id"].apply(
        lambda x: flip_predicate(x)
    )
    lex_df = pd.concat([mondo_subjects_df, new_subjects_df], ignore_index=True)

    condition_8 = lex_df["subject_id"].str.contains("MONDO")
    condition_9 = lex_df["object_id"].str.contains("ICD10CM")
    condition_10 = lex_df["object_id"].str.contains("|".join((["OMIM", "OMIMPS"])))
    condition_11 = lex_df["object_id"].str.contains("Orphanet")
    condition_12 = lex_df["object_id"].str.contains("DOID")
    condition_13 = lex_df["object_id"].str.contains("NCIT")

    mondo_icd_lex_df = lex_df[(condition_8 & condition_9)]
    mondo_omim_lex_df = lex_df[(condition_8 & condition_10)]
    mondo_ordo_lex_df = lex_df[(condition_8 & condition_11)]
    mondo_doid_lex_df = lex_df[(condition_8 & condition_12)]
    mondo_ncit_lex_df = lex_df[(condition_8 & condition_13)]

    icd_comparison_df = compare_and_comment_df(mondo_icd_df, mondo_icd_lex_df)
    omim_comparison_df = compare_and_comment_df(mondo_omim_df, mondo_omim_lex_df)
    ordo_comparison_df = compare_and_comment_df(mondo_ordo_df, mondo_ordo_lex_df)
    doid_comparison_df = compare_and_comment_df(mondo_doid_df, mondo_doid_lex_df)
    ncit_comparison_df = compare_and_comment_df(mondo_ncit_df, mondo_ncit_lex_df)

    unmapped_icd_df = get_unmapped_df(
        icd_comparison_df, in_lex_but_not_mondo_list, in_mondo_but_not_lex_list
    )
    unmapped_omim_df = get_unmapped_df(
        omim_comparison_df, in_lex_but_not_mondo_list, in_mondo_but_not_lex_list
    )
    unmapped_ordo_df = get_unmapped_df(
        ordo_comparison_df, in_lex_but_not_mondo_list, in_mondo_but_not_lex_list
    )
    unmapped_doid_df = get_unmapped_df(
        doid_comparison_df, in_lex_but_not_mondo_list, in_mondo_but_not_lex_list
    )
    unmapped_ncit_df = get_unmapped_df(
        ncit_comparison_df, in_lex_but_not_mondo_list, in_mondo_but_not_lex_list
    )

    export_unmatched_exact(unmapped_icd_df, "LEXMATCH", join(LEXMATCH_DIR, "unmapped_icd_lex.tsv"))
    export_unmatched_exact(
        unmapped_omim_df, "LEXMATCH", join(LEXMATCH_DIR, "unmapped_omim_lex.tsv")
    )
    export_unmatched_exact(
        unmapped_ordo_df, "LEXMATCH", join(LEXMATCH_DIR, "unmapped_ordo_lex.tsv")
    )
    export_unmatched_exact(
        unmapped_doid_df, "LEXMATCH", join(LEXMATCH_DIR, "unmapped_doid_lex.tsv")
    )
    export_unmatched_exact(
        unmapped_ncit_df, "LEXMATCH", join(LEXMATCH_DIR, "unmapped_ncit_lex.tsv")
    )

    export_unmatched_exact(
        unmapped_icd_df,
        "MONDO_MAPPINGS",
        join(MONDOMATCH_DIR, "unmapped_icd_mondo.tsv"),
    )
    export_unmatched_exact(
        unmapped_omim_df,
        "MONDO_MAPPINGS",
        join(MONDOMATCH_DIR, "unmapped_omim_mondo.tsv"),
    )
    export_unmatched_exact(
        unmapped_ordo_df,
        "MONDO_MAPPINGS",
        join(MONDOMATCH_DIR, "unmapped_ordo_mondo.tsv"),
    )
    export_unmatched_exact(
        unmapped_doid_df,
        "MONDO_MAPPINGS",
        join(MONDOMATCH_DIR, "unmapped_doid_mondo.tsv"),
    )
    export_unmatched_exact(
        unmapped_ncit_df,
        "MONDO_MAPPINGS",
        join(MONDOMATCH_DIR, "unmapped_ncit_mondo.tsv"),
    )

    combined_df = pd.concat(
        [
            unmapped_icd_df,
            unmapped_omim_df,
            unmapped_ordo_df,
            unmapped_doid_df,
            unmapped_ncit_df,
        ]
    )

    combined_msdf = make_msdf(combined_df, msdf_lex.prefix_map, msdf_lex.metadata)
    df_dict = split_dataframe(combined_msdf)

    for match in df_dict.keys():
        fn = match + ".tsv"
        df_dict[match].df.to_csv(join(SPLIT_DIR, fn), sep="\t", index=False)


def add_distance(df, col_name, txt_dist_pkg):
    df.insert(
        len(df.columns),
        col_name,
        df.apply(
            lambda x: txt_dist_pkg(
                x.subject_label.lower(),
                x.object_label.lower() if pd.notnull(x.object_label) else "99",
            ),
            axis=1,
        ),
    )


def print_prefixes(df):
    object_prefixes = df["object_id"].str.split(":").apply(lambda x: x[0]).drop_duplicates()
    subject_prefixes = df["subject_id"].str.split(":").apply(lambda x: x[0]).drop_duplicates()
    predicate_ids = df["predicate_id"].drop_duplicates()
    print(
        f"subject_prefixes:\n {subject_prefixes} \n \
          object_prefixes:\n {object_prefixes} \n \
          predicate_ids:\n {predicate_ids} "
    )


def flip_predicate(predicate_id):
    flip_dict = {
        "skos:closeMatch": "skos:closeMatch",
        "skos:relatedMatch": "skos:relatedMatch",
        "skos:narrowMatch": "skos:broadMatch",
        "skos:broadMatch": "skos:narrowMatch",
        "skos:exactMatch": "skos:exactMatch",
    }

    return flip_dict[predicate_id]


def compare_and_comment_df(mondo_df, lex_df):
    df = compare_dataframes(mondo_df, lex_df).combined_dataframe
    df["comment"] = df["comment"].str.replace("UNIQUE_1", "MONDO_MAPPINGS")
    df["comment"] = df["comment"].str.replace("UNIQUE_2", "LEXMATCH")
    return df


def get_unmapped_df(comparison_df, in_lex_but_not_mondo_list, in_mondo_but_not_lex_list):
    #     mappings = ["LEXMATCH", "MONDO_MAPPINGS"]
    #     unmapped_df = comparison_df[
    #         (comparison_df['comment'].str.contains("|".join(mappings)))
    #     ]
    unmapped_lex_df = comparison_df[
        comparison_df["object_id"].str.contains("|".join(in_lex_but_not_mondo_list))
        & comparison_df["comment"].str.contains("LEXMATCH")
    ]

    unmapped_mondo_df = comparison_df[
        comparison_df["object_id"].str.contains("|".join(in_mondo_but_not_lex_list))
        & comparison_df["comment"].str.contains("MONDO_MAPPINGS")
    ]

    new_df = pd.concat([unmapped_lex_df, unmapped_mondo_df], axis=0)
    return new_df


def export_unmatched_exact(unmapped_df, match_type, fn):

    unmapped_exact = unmapped_df[
        (unmapped_df["comment"] == match_type) & (unmapped_df["predicate_id"] == "skos:exactMatch")
    ]
    unmapped_exact = replace_by_mondo_preds(unmapped_exact)
    robot_row_dict = {
        "subject_id": ["ID"],
        "predicate_id": ["A oboInOwl:hasDbXref"],
        "object_id": [">A oboInOwl:source"],
        "object_label": [">A sssom:object_label"],
    }
    column_seq = unmapped_exact.columns
    unmapped_exact = pd.concat(
        [pd.DataFrame.from_dict(robot_row_dict, orient="columns"), unmapped_exact],
        axis=0,
    )
    #     unmapped_exact.index += 1
    #     unmapped_exact = unmapped_exact.sort_index()
    unmapped_exact = unmapped_exact[column_seq]
    dir_name = join(SRC, fn)
    unmapped_exact.to_csv(join(dir_name, fn), sep="\t", index=False)
    return unmapped_exact.head()


def make_msdf(df, prefix_map, meta):
    combined_msdf = MappingSetDataFrame(df=df, prefix_map=prefix_map, metadata=meta)
    return combined_msdf


def mapped_curie_list(df):
    all_id_df = pd.DataFrame(pd.concat([df["subject_id"], df["object_id"]])).drop_duplicates(
        ignore_index=True
    )
    all_id_df = all_id_df[~all_id_df[0].str.startswith("MONDO")]
    return all_id_df[0].to_list()


def replace_by_mondo_preds(df):
    mondo_codes = {
        "skos:exactMatch": "MONDO:equivalentTo",
        "skos:relatedMatch": "MONDO:relatedTo",
        "skos:narrowMatch": "MONDO:mondoIsBroaderThanSource",
        "skos:broadMatch": "MONDO:mondoIsNarrowerThanSource",
    }
    df["predicate_id"] = df["predicate_id"].apply(
        lambda x: mondo_codes[x] if x in mondo_codes else x
    )
    return df


if __name__ == "__main__":
    main()
