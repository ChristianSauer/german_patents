# German Patents
Scripts to collect statistics for patents from the german patent office (dpma)
Unfortunately, the data set is not available to the public - but you can download about 68.000 patents from the 
[dpma website](http://www.dpma.de/service/e_dienstleistungen/datenabgabe/dpmadatenabgabe/index.html]).
Choose the link from the row "Daten aus DPMAregister".

## convert_patents
This script processes the given patents and extracts information about the country of application, the date, the document id and the applicants / inventors address.
Expects the path to the folder containing the patents as input.

The information is stored in the patents folder in a file named result.csv (using ";" as delimeter).
Please note that number of columns for applicants and inventors is not stable, there are up to N columns, depending on the information in the patents.
Column format: Applicants_N_Name where N specifies the number of the applicant.


## postprocess_data

Todo