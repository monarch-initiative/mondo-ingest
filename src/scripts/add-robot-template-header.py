import click
import json
import pandas as pd
from io import StringIO

@click.command()
@click.argument('tsv_file', type=click.File('r'))
@click.argument('json_file', type=click.File('r'))
def add_robot_template_header(tsv_file, json_file):
    # Load the JSON configuration
    config = json.load(json_file)

    # Read the TSV file into a DataFrame
    df = pd.read_csv(tsv_file, sep='\t')

    # Create a new row based on the JSON config
    new_row = {col: config.get(col, '') for col in df.columns}

    # Append the new row to the DataFrame
    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)

    # Output the modified DataFrame
    output = StringIO()
    df.to_csv(output, sep='\t', index=False)
    click.echo(output.getvalue())

if __name__ == '__main__':
    add_robot_template_header()
