import click
import os
import re
import pandas as pd
import logging

from collections import defaultdict

logger = logging.getLogger(__name__)

# Columns a source treats as a unique key. Listing a source here is opt-in: one
# identifier shared by several MONDO terms is legitimate in general, and within
# externally managed content a parent and its subtype may share one by design.
UNIQUE_ID_COLUMNS = {
    "nord": "report_ref",
}


def _get_column_of_external_source_related_to_qc_failure(qc_failure, erroneous_row, external):
    # We already know the subject is the same as the mondo_id in the record
    # Now we only need to ensure that the qc failure is related to that specific external content
    
    columns = [] 
    
    if external == "nord":
        columns = ["report_ref", "preferred_name", "subset"]
    elif external == "mondo-otar-subset":
        columns = ["subset"]
    elif external == "mondo-omim-genes":
        columns = ["hgnc_id"]
    elif external == "mondo-omim-susceptibility-subset":
        columns = ["subset", "omim_id"]
    elif external == "mondo-clingen":
        columns = ["synonym", "subset"]
    elif external == "mondo-medgen":
        columns = ["xref_id"]
    elif external == "mondo-efo":
        columns = ["xref"]
    elif external == "nando-mappings":
        columns = ["object_id"]
    elif external == "ordo-subsets":
        columns = ["subset"]
    elif external == "ncit-rare":
        columns = ["subset", "ncit_id"]
    elif external == "gard":
        columns = ["subset", "gard_id"]
    elif external == "mondo-malacards":
        columns = ["malacards_url", "source"]
    elif external == "doid-rare":
        columns = ["subset", "doid_id"]
    else:
        raise ValueError(f"Unknown external source {external}")
    
    for column in columns:
        if column in erroneous_row:
            value = erroneous_row[column]
            qc_value = qc_failure["Value"]
            if value == qc_value:
                return column
            else:
                print(f"Value: {value}| QC Value: {qc_value}")
                qc_value = qc_value.replace("obo:mondo#", "http://purl.obolibrary.org/obo/mondo#")
                if value == qc_value:
                    return column
    
    return None

def data_rows(df_external_content):
    # Row 0 is the ROBOT template row, not data.
    return df_external_content.iloc[1:].iterrows()


def cell(row, column):
    """The value of a cell, as a string. Empty cells come back as ""."""
    value = row[column]
    return "" if pd.isna(value) else str(value)


def report_row(df_external_content, row, report, source, rule, property, detail=None):
    error_report = df_external_content.loc[row].to_dict()
    error_report['Source'] = source
    error_report['Check'] = f"{rule} ({property})"
    if detail:
        error_report['Detail'] = detail
    report.append(error_report)


def check_invalid_mondo_ids(df_external_content, source, report):
    """Rows whose first column is present but is not a well-formed MONDO term.

    Sources write the term either as a CURIE or as a full IRI. A blank is not a
    violation: a source may list a term it has not mapped to MONDO yet.
    """
    id_column = df_external_content.columns[0]
    pattern = r"(MONDO:|http://purl\.obolibrary\.org/obo/MONDO_)\d{7}"

    rows_to_drop = []
    for index, row in data_rows(df_external_content):
        mondo_id = cell(row, id_column)
        if not mondo_id.strip():
            continue
        if not re.fullmatch(pattern, mondo_id):
            report_row(df_external_content, index, report, source, "invalid_mondo_id", "IRI")
            rows_to_drop.append(index)
    return rows_to_drop


def check_duplicate_external_ids(df_external_content, source, report):
    """Rows whose external identifier is claimed by more than one MONDO term."""
    column = UNIQUE_ID_COLUMNS.get(source)
    if column is None or column not in df_external_content.columns:
        return []

    id_column = df_external_content.columns[0]

    # Which MONDO terms claim each identifier. A set means one identifier
    # repeated on a single term is not counted as a conflict. Blanks are
    # skipped: a row may assert subset membership without an identifier.
    claimed_by = defaultdict(set)
    for _, row in data_rows(df_external_content):
        identifier = cell(row, column).strip()
        if identifier:
            claimed_by[identifier].add(cell(row, id_column))

    rows_to_drop = []
    for index, row in data_rows(df_external_content):
        identifier = cell(row, column).strip()
        if not identifier:
            continue
        others = sorted(claimed_by[identifier] - {cell(row, id_column)})
        if not others:
            continue
        report_row(
            df_external_content, index, report, source,
            "duplicate_external_id", column,
            detail=f"{identifier} is also on {', '.join(others)}",
        )
        rows_to_drop.append(index)
    return rows_to_drop


def _write_nice_report(report, external):
    nice_report = f"../ontology/external/{external}-qc-failures.md"
    
    df_records = pd.DataFrame(report)
    df_records.fillna("", inplace=True)
    
    if report:
        report_string = df_records.to_markdown(index=False)
    else:
        report_string = "No QC failures found."
    
    failure_report = f"""
# QC Report for {external}

{report_string}
"""
    
    with open(nice_report, "w") as f:
        f.write(failure_report)

def _remove_erroneous_values_from_externally_managed_content(external_content_file, robot_report_file, external_content_file_out):
    df_robot_report = pd.read_csv(robot_report_file, sep="\t")
    report = []
    source = os.path.basename(external_content_file).split(".")[0]
    if not os.path.exists(external_content_file):
        logger.warning(f"External content file {external_content_file} does not exist.")
        return
    df_external_content = pd.read_csv(external_content_file, sep="\t")
    for _, qc_failure in df_robot_report.iterrows():
        mondo_id_failure = qc_failure["Subject"]
        if mondo_id_failure in df_external_content.iloc[:, 0][1:].tolist():
            erroneous_rows = df_external_content[df_external_content.iloc[:, 0] == mondo_id_failure]
            for index, erroneous_row in erroneous_rows.iterrows():
                ## if the row is erroneous because of qc_failure is related to this specififc external content
                erroneous_column = _get_column_of_external_source_related_to_qc_failure(qc_failure, erroneous_row, source)
                if erroneous_column:
                    erroneous_row_cp = erroneous_row.copy()
                    for col in erroneous_rows.columns:
                            if col != erroneous_rows.columns[0] and col != erroneous_column:
                                erroneous_row_cp.at[col] = ""
                    error_report = erroneous_row_cp.to_dict()
                    error_report['Source'] = source
                    rule = qc_failure["Rule Name"]
                    property = qc_failure["Property"]
                    error_report['Check'] = f"{rule} ({property})"
                    report.append(error_report)
                    df_external_content.at[index, erroneous_column] = ""

    # Checks not covered by the ROBOT report. A failing row is dropped, not
    # repaired. Every check sees the same rows, so one failing two checks is
    # reported under both.
    rows_to_drop = set()

    checks = (
        check_invalid_mondo_ids,
        check_duplicate_external_ids,
    )

    for check in checks:
        rows_to_drop.update(check(df_external_content, source, report))
    df_external_content.drop(index=sorted(rows_to_drop), inplace=True)

    df_external_content.to_csv(external_content_file_out, sep="\t", index=False)
    _write_nice_report(report, source)


@click.command()
@click.option('--emc-template-tsv', help='ID of the externally managed content file to process.', required=True)
@click.option('--robot-report', help='Location of the robot report with violations.', required=True)
@click.option('--output', help='Location of the processed externally managed content file.', required=True)
def remove_erroneous_values_from_externally_managed_content(emc_template_tsv, robot_report, output):
    """
    Post-process externally managed content.
    """
    _remove_erroneous_values_from_externally_managed_content(emc_template_tsv, robot_report, output)

if __name__ == '__main__':
    remove_erroneous_values_from_externally_managed_content()
