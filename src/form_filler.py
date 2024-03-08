import argparse
from jinja2 import (
    FileSystemLoader,
    Environment,
    meta,
)

"""
Current goals:
    scan a template and determine the require fields that need to be populated
    take input data from console and build a single output from a template
Long term goals:
    take input data from a CSV and build multiple outputs
"""

template_dir = "../templates"
template_path = "example.template.txt"
output_path = "../output/example.output.txt"


def main():
    # Init jinja environment
    loader = FileSystemLoader(template_dir)
    environment = Environment(loader=loader)

    # Get a list of fields that need to be populated
    template_source = environment.loader.get_source(environment, template_path)
    parsed_content = environment.parse(template_source)
    undeclared_vars = meta.find_undeclared_variables(parsed_content)

    # Start a loop to get input from user for those fields
    var_dict = {}
    i = 0
    for item in undeclared_vars:
        i += 1
        var_dict[item] = input(f"Give me your cookies {item}: ")
        # Take user input here
        print("item: ", item)
        print("dict: ", var_dict)
    print("undecls: ", undeclared_vars)

    # Now feed those values back in to the template and output to the output file
    template = environment.get_template(template_path)
    rendering = template.render(var_dict)
    print("rendering: ", rendering)


# To be finished, let's get jinja parsing working and file output working first
def build_parser():
    parser = argparse.ArgumentParser(description="Process some templates")
    parser.add_argument(
        "template",
        metavar="t",
        type=argparse.FileType("r"),
        help="The jinja template file",
        required=True,
    )
    parser.add_argument(
        "output_filename",
        metavar="o",
        type=argparse.FileType("w"),
        help="The output file destination",
        required=True,
    )
    return parser


if __name__ == "__main__":
    main()
