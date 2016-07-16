import glob
import sys
import os

import cytoolz
from lxml import etree
import pandas as pd

INVENTORS = "Inventors"

APPLICANTS = "Applicants"

COUNTRY = "Country"

ADDRESS = "Address"

NAME = "Name"

DATE = "Date"

COUNTRY = "Country"

ADDRESS_KEYS = [NAME, ADDRESS, COUNTRY]

DOCUMENT_ID = "Document_ID"
NAMESPACES = namespaces = {'p': 'http://www.dpma.de/standards/XMLSchema/DE-PATGBM-RegisterExt'}


def _get_patents_path():
    # first arg is the name of the file itself
    if len(sys.argv) != 2:
        print("Please provide the path to the patents folder via cmd", file=sys.stderr)
        exit(1)

    # given path must be a dir and exist
    maybe_patents_path = sys.argv[1]
    if not os.path.isdir(maybe_patents_path) or not os.path.exists(maybe_patents_path):
        print("The provided patents path '{}' is not valid".format(maybe_patents_path), file=sys.stderr)
        exit(1)

    print("Using patent path {}".format(maybe_patents_path))

    return maybe_patents_path


def _get_data_from_file(path):
    # using binary here b/c lxml throws an error otherwise -> lxml determines the encoding from the gixen declaration
    # in the xml
    with open(path, 'rb') as fp:
        text = fp.read()

    xml = etree.fromstring(text)

    result = {}

    _add_doc_information(xml, result)
    _add_applicants(xml, result)
    _add_inventors(xml, result)

    return result


def _add_applicants(xml, result):

    all_applicant_infos = []
    applicants = xml.findall(".//p:parties/p:applicants/p:applicant", namespaces=NAMESPACES)

    _get_address_information(all_applicant_infos, applicants)

    result[APPLICANTS] = all_applicant_infos


def _get_address_information(infos, node):
    for applicant in node:
        name = applicant.find(".//p:addressbook/p:name", namespaces=NAMESPACES)
        address = applicant.find(".//p:addressbook/p:address/p:address-1", namespaces=NAMESPACES)
        country = applicant.find(".//p:addressbook/p:address/p:country", namespaces=NAMESPACES)

        name = name.text if name is not None else None
        address = address.text if address is not None else None
        country = country.text if country is not None else None

        info = {NAME: name,
                ADDRESS: address,
                COUNTRY: country}

        infos.append(info)


def _add_inventors(xml, result):
    all_invetor_infos = []
    party_elem = xml.find(".//p:parties", namespaces=NAMESPACES)
    inventors = party_elem.findall("p:inventors/p:inventor", namespaces=NAMESPACES)

    _get_address_information(all_invetor_infos, inventors)
    result[INVENTORS] = all_invetor_infos


def _add_doc_information(xml, result):
    doc_id = xml.xpath("//p:application-reference/p:document-id/p:doc-number", namespaces=NAMESPACES)
    country = xml.xpath("//p:application-reference/p:document-id/p:country", namespaces=NAMESPACES)
    date = xml.xpath("//p:application-reference/p:document-id/p:date", namespaces=NAMESPACES)

    result[DOCUMENT_ID] = cytoolz.first(doc_id).text
    result[COUNTRY] = cytoolz.first(country).text
    result[DATE] = cytoolz.first(date).text


def _to_data_frame():
    df = pd.DataFrame.from_dict(all_patent_infos)

    df = _make_columns_from_inner_data(df, all_patent_infos, APPLICANTS)
    df = df.drop(APPLICANTS, axis=1)

    df = _make_columns_from_inner_data(df, all_patent_infos, INVENTORS)
    df = df.drop(INVENTORS, axis=1)
    return df


def _make_columns_from_inner_data(df, all_patent_infos, column_key):
    """
    We need append our variable length addreess information to the df.
    Therefore, we need N columns, where N is the maximum number of available address fields in the column_key column.
    Empty columns need None values, to avoid missing values for the rows.

    :param df:
    :param column_key:
    :return:
    """

    max_cols = max(x for x in [len(y[column_key]) for y in all_patent_infos])
    print("Adding {} columns for {}".format(max_cols, column_key))

    column_names = ["{}_{}_{}".format(column_key, x, y) for x in range(max_cols) for y in ADDRESS_KEYS]

    column_name_to_data = {
        x: [] for x in column_names
        }

    for row in df[column_key]:
        for i, list_elem in enumerate(row):
            for key in list_elem:
                col_name = "{}_{}_{}".format(column_key, i, key)
                column_name_to_data[col_name].append(list_elem[key])

        if len(row) < max_cols:
            _fill_empty_columns_with_none(column_key, column_name_to_data, len(row), max_cols)

    df = df.assign(**column_name_to_data)
    return df


def _fill_empty_columns_with_none(column_key, column_name_to_data, i, max_applicant_cols):
        for x in range(i, max_applicant_cols):
            for key in ADDRESS_KEYS:
                col_name = "{}_{}_{}".format(column_key, x, key)
                column_name_to_data[col_name].append(None)


if __name__ == "__main__":
    patent_path = _get_patents_path()

    patent_files_pattern = os.path.join(patent_path, "*.xml")
    matching_files = glob.glob(patent_files_pattern)

    number_of_matches = len(matching_files)

    print("Found {} valid patents. Gathering information now".format(number_of_matches))

    all_patent_infos = []
    for counter, file_path in enumerate(matching_files):
        if counter % 1000 == 0:
            print("Finished {} patents".format(counter))

        patent_info = _get_data_from_file(file_path)

        if counter == 100:
            pass
            # break

        all_patent_infos.append(patent_info)

    print("Finished gathering data, transforming to DataFrame now")

    data_frame = _to_data_frame()

    output_path = os.path.join(patent_path, "result.csv")

    print("Done, writing output to: {}".format(output_path))
    data_frame.to_csv(output_path, sep=";")


