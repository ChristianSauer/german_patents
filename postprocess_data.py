import os

import pandas as pd
import plotly.graph_objs as go
import plotly.offline as py
import sys

CITY_COL = "City"

MIN_NO_PATENTS = 25

DATE_COL = "Date"

PLZ_COL = "PLZ"


def _get_csv_path():
    # first arg is the name of the file itself
    if len(sys.argv) != 2:
        print("Please provide the path to the results.csv folder via cmd", file=sys.stderr)
        exit(1)

    # given path must be a dir and exist
    maybe_csv_path = sys.argv[1]
    if not os.path.isfile(maybe_csv_path) or not os.path.exists(maybe_csv_path):
        print("The provided patents path '{}' is not valid".format(maybe_csv_path), file=sys.stderr)
        exit(1)

    print("Using csv path {}".format(maybe_csv_path))

    return maybe_csv_path


def get_data(file_path):
    df = pd.DataFrame.from_csv(file_path, sep=";", encoding="latin1")
    return df


def extract_city(row):
    adress = row["Inventors_0_Address"]

    if not isinstance(adress, str):
        return None

    splitted = adress.split(" ")

    if len(splitted) < 1:
        return None
    else:
        rv = " ".join(splitted[1:])
        return rv


def extract_plz(row):

    adress = row["Inventors_0_Address"]

    if not isinstance(adress, str):
        return None

    splitted = adress.split(" ")

    try:
        int(splitted[0])
    except (TypeError, ValueError):
        return None

    return splitted[0]


def main():
    path = _get_csv_path()

    df = get_data(path)

    df = _cleanup_data(df)

    plot_plz_freq(df)


def plot_plz_freq(df):
    plz_freqs = df[PLZ_COL].value_counts()
    top_plz = plz_freqs[plz_freqs > MIN_NO_PATENTS]

    x_values = top_plz.index.values.astype("str")
    x_values = ["PLZ " + x for x in x_values]

    df_by_plz = df.groupby(PLZ_COL)

    texts = []
    for relevant_plz in top_plz.index.values:
        plz_data = df_by_plz.get_group(relevant_plz)
        unique_city_names = plz_data[CITY_COL].unique()
        city_names = ", ".join(unique_city_names)
        texts.append(city_names)

    # noinspection PyUnresolvedReferences
    data = [go.Bar(
        x=x_values,
        y=top_plz,
        text=texts,
    )]

    annotations = [
        dict(
            text="Only PLZs with more than {} patents are shown".format(MIN_NO_PATENTS),
            x=.51,
            xref="paper",
            y=0.93,
            yref="paper"
        )
    ]

    # noinspection PyUnresolvedReferences
    layout = go.Layout(
        title='Number of Patents for a PLZ ',
        annotations=annotations
    )

    # noinspection PyUnresolvedReferences
    fig = go.Figure(data=data, layout=layout)

    py.plot(fig, filename='plz_frequencies.html')


def _cleanup_data(df):
    # we need only a few columns
    df = df[['Country', 'Date', "Document_ID", "Inventors_0_Address", "Inventors_0_Country", "Inventors_0_Name"]]

    # drop all cases which are not from germany - we don't have addresses anyway
    df = df[df.Inventors_0_Country == "DE"]

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], yearfirst=True)

    # address is stored as a combination of City Name + PLZ - get only the PLZ into a new column
    _split_plz_and_city_into_columns(df)

    return df


def _split_plz_and_city_into_columns(df):
    df[PLZ_COL] = df.apply(extract_plz, axis=1)
    df[CITY_COL] = df.apply(extract_city, axis=1)


if __name__ == "__main__":
    main()
