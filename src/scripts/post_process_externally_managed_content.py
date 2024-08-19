import click
import os
import pandas as pd



def is_qc_failure_related_to_external_source(qc_failure, erroneous_row, external):
    # We already know the subject is the same as the mondo_id in the record
    # Now we only need to ensure that the qc failure is related to that specific external content
    
    columns = [] 
    
    if external == "nord.robot.tsv":
        columns = ["report_ref", "preferred_name", "subset"]
    elif external == "mondo-otar-subset.robot.tsv":
        columns = ["subset"]
    elif external == "mondo-omim-genes.robot.tsv":
        columns = ["hgnc_id"]
    elif external == "mondo-clingen.robot.tsv":
        columns = ["synonym", "subset"]
    elif external == "mondo-medgen.robot.tsv":
        columns = ["xref_id"]
    elif external == "mondo-efo.robot.tsv":
        columns = ["xref"]
    elif external == "nando-mappings.robot.tsv":
        columns = ["object_id"]
    elif external == "ordo-subsets.robot.tsv":
        columns = ["subset"]
    else:
        raise ValueError(f"Unknown external source {external}")
    
    for column in columns:
        if column in erroneous_row:
            value = erroneous_row[column]
            qc_value = qc_failure["Value"]
            if value == qc_value:
                return column
    
    return False

def write_nice_report(report, external):
    if not report:
        return
    nice_report = f"../ontology/external/{external}-qc-failures.md"
    print(f"Writing nice report to {nice_report}")
    
    df_records = pd.DataFrame(report)
    df_records.fillna("", inplace=True)
    
    failure_report = f"""
# QC Failure Report for {external}

## Removed from the resource

{df_records.to_markdown(index=False)}
"""
    
    with open(nice_report, "w") as f:
        f.write(failure_report)

def process_externally_managed_source(source, external_content_dir, robot_report_file):
    df_robot_report = pd.read_csv(robot_report_file, sep="\t")
    report = []
    drop_rows_indexes = []
    external_content_file = f"{external_content_dir}/{source}"
    df_external_content = pd.read_csv(external_content_file, sep="\t")
    for _, qc_failure in df_robot_report.iterrows():
        mondo_id_failure = qc_failure["Subject"]
        if mondo_id_failure in df_external_content.iloc[:, 0][1:].tolist():
            erroneous_rows = df_external_content[df_external_content.iloc[:, 0] == mondo_id_failure]
            for index, erroneous_row in erroneous_rows.iterrows():
                ## if the row is erroneous because of qc_failure is related to this specififc external content
                erroneous_column = is_qc_failure_related_to_external_source(qc_failure, erroneous_row, source)
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

    df_external_content.drop(drop_rows_indexes, inplace=True)
    df_external_content.to_csv(external_content_file, sep="\t", index=False)
    write_nice_report(report, source)


    @click.command()
    @click.option('--emc-id', help='ID of the externally managed content file to process.', required=True, multiple=True)
    @click.option('--emc-dir', help='Directory where the externally managed content (emc) is located.')
    @click.option('--robot-report', help='Location of the robot report with violations.')
    def post_process_externally_managed_content(emc_id, emc_dir, robot_report):
        """
        Post-process externally managed content.
        """
        
        for _emc_id in emc_id:
            process_externally_managed_source(_emc_id, emc_dir, robot_report)

    if __name__ == '__main__':
        post_process_externally_managed_content()
