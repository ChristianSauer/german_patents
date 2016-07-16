import pandas as pd


def get_data(file_path):
    df = pd.DataFrame.from_csv(file_path, sep=";", encoding="latin1")
    return df


def plz_splitter(row):
    adress = row["Inventors_0_Address"]

    if not isinstance(adress, str):
        return None

    splitted = adress.split(" ")

    try:
        int(splitted[0])
    except (TypeError, ValueError):
        return None

    return splitted[0]


if __name__ == "__main__":
    path = "D:/Patents/result.csv"

    df = get_data(path)

    # we need only a few columns
    df = df[['Country', 'Date', "Document_ID", "Inventors_0_Address", "Inventors_0_Country", "Inventors_0_Name"]]

    df = df[df.Inventors_0_Country == "DE"]

    df["Date"] = pd.to_datetime(df["Date"], yearfirst=True)

    df["PLZ"] = df.apply(plz_splitter, axis=1)

    print(df["PLZ"].describe())