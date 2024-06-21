import logging
from os.path import abspath, dirname, join
from os import listdir
from typing import TextIO

import click
import pandas as pd
from oaklib import OntologyResource
from oaklib.implementations import SqlImplementation
from sssom import compare_dataframes
from sssom.parsers import parse_sssom_table, split_dataframe
from sssom.util import MappingSetDataFrame, filter_redundant_rows, sort_df_rows_columns

SRC = dirname(dirname(abspath(__file__)))
MAPPINGS = join(SRC, "mappings")
ONTS_DIR = join(SRC, "ontology")
LEXMATCH_DIR = join(ONTS_DIR, "lexmatch")
SPLIT_DIR = join(LEXMATCH_DIR, "split-mapping-set")
TMP = join(ONTS_DIR, "tmp")
REPORTS_DIR = join(ONTS_DIR, "reports")
MONDO_SSSOM = join(TMP, "mondo.sssom.tsv")
DB_FILE = join(TMP, "merged.db")
ROBOT_ROW_DICT = {
        "subject_id": ["ID"],
        "predicate_id": [">A oboInOwl:source"],
        "object_id": ["A oboInOwl:hasDbXref"],
    }


DESIRED_COLUMN_ORDER = [
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

input_argument = click.argument("input", required=True, type=click.Path(), nargs=-1)


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


@main.command("combine_unmapped_lex_exacts")
def combine_unmapped_lex_exacts() -> None:
    file_list = [file for file in listdir(LEXMATCH_DIR) if file.endswith("_lex_exact.tsv")]
    # Initialize an empty DataFrame to store the merged data
    merged_lex_exact_df = pd.DataFrame()

    # Concatenate all the files into a single DataFrame
    for file in file_list:
        file_path = join(LEXMATCH_DIR, file)
        df = pd.read_csv(file_path, delimiter="\t")
        merged_lex_exact_df = pd.concat([merged_lex_exact_df, df])

    merged_lex_exact_df = pd.concat(
        [pd.DataFrame.from_dict(ROBOT_ROW_DICT, orient="columns"), merged_lex_exact_df],
        axis=0,
    )

    merged_lex_exact_df.drop_duplicates(inplace=True)

    merged_lex_exact_df.to_csv(join(LEXMATCH_DIR, "all_exact.robot.tsv"), sep="\t", index=False)


@main.command("extract_unmapped_matches")
@input_argument
@click.option(
    "--matches",
    type=click.File(mode="r"),
    help="Lexmatch SSSOM file.",
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(),
    help="Output directory where all results must be saved.",
    default=LEXMATCH_DIR,
)
@click.option(
    "--summary",
    type=click.File(mode="w+"),
    help="Add summary to markdown file.",
)
@click.option(
    "--exclusion",
    multiple=True,
    help="exclusion files which are basically a list of CURIES to be excluded.",
)
def extract_unmapped_matches(input: str, matches: TextIO, output_dir: str, summary: TextIO, exclusion: str):
    mondo_match_dir = join(output_dir, "mondo-only")
    msdf_lex = parse_sssom_table(matches.name)
    msdf_mondo = parse_sssom_table(MONDO_SSSOM)

    # Get the exclusion list
    exclusion_list = []
    summary.write("# MONDO ingest lexical mapping pipeline.")
    summary.write("\n")
    summary.write("## Content of directories:")
    summary.write("\n")
    summary.write(
        "* mondo-only: Positive mappings in MONDO not caught by the lexical mapping pipeline"
    )
    summary.write("\n")
    summary.write("* split-mapping-set: Unmapped mappings broken down by predicate_id")
    summary.write("\n")
    summary.write("## Summary of mappings:")
    summary.write("\n")
    for file_path in exclusion:
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
    msdf_mondo.df["object_label"] = msdf_mondo.df["object_id"].apply(
        lambda x: oi.label(x)
    )

    condition_mondo_sssom_subj = msdf_mondo.df["subject_id"].str.contains("MONDO")
    condition_mondo_lex_obj = msdf_lex.df["object_id"].str.contains("MONDO")
    condition_mondo_lex_subj = msdf_lex.df["subject_id"].str.contains("MONDO")
    non_mondo_subjects_df = pd.DataFrame(
        msdf_lex.df[(~condition_mondo_lex_subj & condition_mondo_lex_obj)]
    )
    mondo_subjects_df = pd.DataFrame(msdf_lex.df[(condition_mondo_lex_subj & ~condition_mondo_lex_obj)])

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

    new_subjects_df = new_subjects_df[DESIRED_COLUMN_ORDER]
    new_subjects_df["predicate_id"] = new_subjects_df["predicate_id"].apply(
        lambda x: flip_predicate(x)
    )
    lex_df = pd.concat([mondo_subjects_df, new_subjects_df], ignore_index=True)
    condition_lex_df_mondo_subj = lex_df["subject_id"].str.contains("MONDO")
    ont_df_list = []

    for _, ont in enumerate(input):
        # Map ontology filenames to prefixes
        ont2 = ont.upper()
        if ont == "omim":
            ont2 = "|".join((["OMIM", "OMIMPS"]))
        elif ont == "ordo":
            ont2 = "|".join((["ORDO", "Orphanet"]))
        elif ont == "icd11foundation":
            ont2 = 'icd11.foundation'

        mondo_ont_df = msdf_mondo.df[condition_mondo_sssom_subj & msdf_mondo.df['object_id'].str.contains(ont2)]
        mondo_ont_lex_df = lex_df[(condition_lex_df_mondo_subj & lex_df['object_id'].str.contains(ont2))]
        ont_comparison_df = compare_and_comment_df(mondo_ont_df, mondo_ont_lex_df)

        if not ont_comparison_df.empty:
            unmapped_ont_df = get_unmapped_df(
                ont_comparison_df, in_lex_but_not_mondo_list, in_mondo_but_not_lex_list
            )

            export_unmatched_exact(
                unmapped_ont_df, "LEXMATCH", join(LEXMATCH_DIR, f"unmapped_{ont}_lex.tsv"), summary
            )

            export_unmatched_exact(
                unmapped_ont_df,
                "MONDO_MAPPINGS",
                join(mondo_match_dir, f"unmapped_{ont}_mondo.tsv"),
                summary,
            )

            ont_df_list.append(unmapped_ont_df)

    combined_df = pd.concat(ont_df_list) if ont_df_list else pd.DataFrame()

    combined_msdf = MappingSetDataFrame(
        df=combined_df, converter=msdf_lex.converter, metadata=msdf_lex.metadata
    )
    df_dict = split_dataframe(combined_msdf)
    summary.write("## mondo_XXXXmatch_ontology")
    summary.write("\n")
    for match in df_dict.keys():
        fn = match + ".tsv"
        summary.write(
            " * Number of mappings in [`"
            + match
            + "`](split-mapping-set/"
            + str(fn)
            + "): "
            + str(len(df_dict[match].df))
        )
        summary.write("\n")

        df_dict[match].df.to_csv(join(SPLIT_DIR, fn), sep="\t", index=False)

    summary.close()


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
    object_prefixes = (
        df["object_id"].str.split(":").apply(lambda x: x[0]).drop_duplicates()
    )
    subject_prefixes = (
        df["subject_id"].str.split(":").apply(lambda x: x[0]).drop_duplicates()
    )
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
    if not df.empty:
        df["comment"] = df["comment"].str.replace("UNIQUE_1", "MONDO_MAPPINGS")
        df["comment"] = df["comment"].str.replace("UNIQUE_2", "LEXMATCH")
    return df


def get_unmapped_df(
    comparison_df, in_lex_but_not_mondo_list, in_mondo_but_not_lex_list
):
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
    if 'confidence' not in new_df.columns:
        new_df['confidence'] = 0.5
    else:
        new_df['confidence'] = pd.to_numeric(new_df['confidence'], errors='coerce')  # Convert to numeric, invalid parsing will be NaN
        new_df['confidence'] = new_df['confidence'].apply(lambda x: x if 0 <= x <= 1 else 0.5)  # Replace out of range values with default
        new_df['confidence'].fillna(0.5, inplace=True)  # Replace NaN with default value

    new_df.to_csv("check_me_out.sssom.tsv", sep="\t")
    filtered_new_df = filter_redundant_rows(new_df)
    return filtered_new_df


def export_unmatched_exact(unmapped_df, match_type, fn, summary):
    columns_to_remove = ["subject_preprocessing", "object_preprocessing"]
    if any(item in columns_to_remove for item in unmapped_df.columns):
        cols = [
            col_name
            for col_name in unmapped_df.columns
            if col_name in columns_to_remove
        ]
        unmapped_df.drop(cols, axis=1, inplace=True)
    unmapped_exact = unmapped_df[
        (unmapped_df["comment"] == match_type)
        & (unmapped_df["predicate_id"] == "skos:exactMatch")
    ]
    unmapped_exact = replace_by_mondo_preds(unmapped_exact)
    column_seq = unmapped_exact.columns
    unmapped_exact = pd.concat(
        [pd.DataFrame.from_dict(ROBOT_ROW_DICT, orient="columns"), unmapped_exact],
        axis=0,
    )
    unmapped_exact = unmapped_exact[column_seq]
    unmapped_exact = sort_df_rows_columns(unmapped_exact)
    unmapped_exact = unmapped_exact.drop_duplicates()
    actual_fn = fn.split("/")[-1].replace(".tsv", "")
    fn_path = (
        fn.split("/")[-1]
        if str(actual_fn).endswith("_lex")
        else "mondo-only/" + fn.split("/")[-1]
    )

    summary.write(
        " * Number of mappings in [`"
        + actual_fn
        + "`]("
        + fn_path
        + "): "
        + str(len(unmapped_exact))
    )
    summary.write("\n")
    # Split out exact match i.e. subj_label.lowercase()==obj_label.lowercase() into a separate file.
    unmapped_exact_exact = unmapped_exact.loc[
        unmapped_exact["subject_label"].str.lower()
        == unmapped_exact["object_label"].str.lower()
    ]
    new_fn = fn.replace(".tsv", "_exact.tsv")
    actual_fn_exact = new_fn.split("/")[-1].replace(".tsv", "")
    fn_path_exact = (
        "mondo-only/" + fn.split("/")[-1]
        if str(actual_fn_exact).endswith("_mondo_exact")
        else fn.split("/")[-1]
    )

    unmapped_exact_exact = pd.concat(
        [
            pd.DataFrame.from_dict(ROBOT_ROW_DICT, orient="columns"),
            unmapped_exact_exact,
        ],
        axis=0,
    )
    unmapped_exact_exact = unmapped_exact_exact[DESIRED_COLUMN_ORDER]
    unmapped_exact_exact.to_csv(join(new_fn), sep="\t", index=False)
    unmapped_exact_logical = unmapped_exact.loc[
        unmapped_exact["subject_label"].str.lower()
        != unmapped_exact["object_label"].str.lower()
    ]
    unmapped_exact_logical = unmapped_exact_logical[DESIRED_COLUMN_ORDER]
    unmapped_exact_logical.to_csv(join(fn), sep="\t", index=False)

    summary.write(
        " * Number of mappings in [`"
        + actual_fn_exact
        + "`]("
        + fn_path_exact
        + "): "
        + str(len(unmapped_exact_logical))
    )
    summary.write("\n")


def mapped_curie_list(df):
    all_id_df = pd.DataFrame(
        pd.concat([df["subject_id"], df["object_id"]])
    ).drop_duplicates(ignore_index=True)
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
