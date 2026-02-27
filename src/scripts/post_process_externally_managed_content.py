import click
import os
import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)


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

    # Additional checks on the pandas dataframe that are not covered by SPARQL
    
    # BANANA ERROR: Search the entire external content for occurrences of the pattern 'MONDO:MONDO'
    pattern = r"^MONDO:MONDO:.*$"
    result = df_external_content.applymap(lambda x: bool(re.match(pattern, str(x))))
    rows_to_drop = result.any(axis=1).index[result.any(axis=1)].tolist()
    for row in rows_to_drop:
        error_report = df_external_content.loc[row].to_dict()
        error_report['Source'] = source
        rule = "MONDO:MONDO_pattern"
        property = "IRI"
        error_report['Check'] = f"{rule} ({property})"
        report.append(error_report)
        df_external_content.drop(index=rows_to_drop, inplace=True)
    
    # X ERROR: TBD
    
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
