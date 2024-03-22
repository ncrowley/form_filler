import argparse
from collections import Counter
import csv
from jinja2 import (
    BaseLoader,
    FileSystemLoader,
    Environment,
    meta,
)
import os

"""
Current goals:
Long term goals:
    maybe break things out into different modules
"""


class InvalidDelimiterError(Exception):
    pass


class MissingVariableException(Exception):
    pass


def main():
    parser = build_parser()
    try:
        args = vars(parser.parse_args())
    except InvalidDelimiterError as e:
        print("FATAL: Invalid csv delimiter: ", str(e))
        print("Delimiter must be one character")
        quit()

    data_path = None if not "data_src" in args.keys() else args["data_src"]
    csv_delimiter = (
        None if not "csv_delimiter" in args.keys() else args["csv_delimiter"]
    )
    output_path = args["output"]
    template_dir = os.path.split(args["template"].name)[0]
    template_file = os.path.split(args["template"].name)[1]

    environment = init_jinja(template_dir)

    # Start a loop to get input from user for those fields
    undeclared_vars = get_undeclared_vars(environment, template_file)
    input_data = None
    try:
        input_data = build_input_data(
            data_path, undeclared_vars, csv_delimiter
        )
    except MissingVariableException as e:
        print("FATAL: Missing variables: ", str(e))

    template = environment.get_template(template_file)
    # Now feed those values back in to the template and output to the output file
    create_output(template, input_data, output_path)
    print("Execution completed successfully.")


def init_jinja(template_dir):
    # Init jinja environment
    return Environment(loader=FileSystemLoader(template_dir))


def get_csv_data(data_path, csv_delimiter):
    retval = []
    csv_delimiter = "," if csv_delimiter == None else csv_delimiter
    with open(data_path.name, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=csv_delimiter)
        for row_num, row in enumerate(reader):
            retval.append(row)
    return retval


def generate_output_filename(output_path_split, data_num, var_dict):
    # Check for jinja tags in the output path
    if not "{{" in output_path_split[0]:
        return f"{output_path_split[0]}{data_num + 1}{output_path_split[1]}"
    template = Environment(loader=BaseLoader).from_string(output_path_split[0])
    return f"{template.render(var_dict)}{output_path_split[1]}"


def create_output(template, input_data, output_path):
    print("Writing output...")
    var_dict = {}
    output_path_split = os.path.splitext(output_path)
    for item in input_data[0]:
        var_dict[item] = None
    for data_num, data in enumerate(input_data[1:]):
        for item_num, item in enumerate(data):
            var_dict[input_data[0][item_num]] = item
        if not "row_num" in input_data[0]:
            var_dict["row_num"] = data_num

        rendered_string = template.render(var_dict)
        # Slide the number in just before the extension
        output_filename = generate_output_filename(
            output_path_split, data_num, var_dict
        )
        print("Writing row ", data_num + 1, " to ", output_filename)
        with open(output_filename, "w") as file:
            file.write(rendered_string)
    print("Output complete")


def get_undeclared_vars(environment, template_file):
    # Get a list of fields that need to be populated
    template_source = environment.loader.get_source(environment, template_file)
    parsed_content = environment.parse(template_source)
    return meta.find_undeclared_variables(parsed_content)


def build_input_data(data_path, undeclared_vars, csv_delimiter):
    retval = []
    if data_path:
        retval = get_csv_data(data_path, csv_delimiter)
        found_vars = []
        for item in retval[0]:
            if item in undeclared_vars:
                found_vars.append(item)
        duplicate_column_headers = [
            k for k, v in Counter(retval[0]).items() if v > 1
        ]
        # TODO: Do this in a pythonic way throwing exceptions
        if duplicate_column_headers:
            print(
                "WARNING: Duplicate column name(s): ", duplicate_column_headers
            )
            print("First column bearing the name will be used")
        elif set(undeclared_vars) != set(found_vars):
            raise MissingVariableException(
                set(undeclared_vars) - set(found_vars)
            )
            quit()
        elif set(retval[0]) != set(found_vars):
            print(
                "WARNING: unassigned var(s): ",
                (set(retval[0]) - set(found_vars)),
            )
        else:
            print(
                "Sucessfully mapped data headers to required fields for template."
            )
    else:
        retval = []
        retval.append(undeclared_vars)
        i = 1
        while True:
            retval.append([None * len(retval[0])])
            for item_num, item in enumerate(undeclared_vars):
                retval[i][item_num] = input(f"Enter value for {item}: ")
            response = None
            while response and (response != "y" or response != "n"):
                response = input("Enter another set of input? y/n: ")
                response = response.lower()
            if response == "n":
                break
            i += 1
    return retval


def build_parser():
    parser = argparse.ArgumentParser(
        description="Process jinja templates into "
        "output using manual input or data from a csv."
    )
    parser.add_argument(
        "--csv-delimiter",
        type=delimiter_validator,
        help="Set a custom csv delimiter.",
    )
    parser.add_argument(
        "--data-src",
        "-d",
        type=argparse.FileType("r"),
        help="Input data csv",
        required=False,
    )
    # Can't validate this until we have data to sub into tags
    parser.add_argument(
        "--output-path",
        "-o",
        help="The output file location. Jinja fields can be used to create "
        "unique paths. The {{row_num}} field is exposed for use as long as it "
        "does not conflict with a data field. If no fields are used to create "
        "unique filenames the row number is inserted before the file extension "
        "to create a unique filename. If a duplicate filename is detected the "
        "row number is inserted before the filename extension into the "
        "filename to create a unique identifier.",
        required=True,
    )
    parser.add_argument(
        "--template",
        "-t",
        type=argparse.FileType("r"),
        help="The jinja template file",
        required=True,
    )
    return parser


def delimiter_validator(string):
    if len(string) < 1 or len(string) > 1:
        raise InvalidDelimiterError(string)
    return string


if __name__ == "__main__":
    main()
