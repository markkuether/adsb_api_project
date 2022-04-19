import trans_airport_mod as tam
import csv
import sys
import pathlib

'''
To assess an aircrafts proximity and position
relative to an airport, details about an airports
latitude, longitude, elevation, pattern altitude,
and runwawys is needed.

The FAA provides an XLSX spreadsheet containing many
details about airports, but it is difficult to use.

This code reads data from CSV sheets saved from the XLSX
spreadsheet and transforms the data into a simpler CSV
format to be imported as SQL tables. SQL can then be used to
retrieve airport and runway data for this project.

DEPENDENCY: This code requires the airport and runway
CSV sheets to be sorted ascending by the "Site Id" column 
prior to running. 
'''


def set_fields():
    # Sets Initial fields used for transformations.
    airport_fields = ["Site Id", "Facility Type", "Loc Id", "State Id", "Use"]
    airport_fields += ["Elevation", "ARP Latitude",
                       "ARP Longitude", "Traffic Pattern Altitude"]
    airport_fld_pos = [0, 1, 2, 6, 13, 27, 22, 24, 31]
    airports = {fld_name: airport_fld_pos[index]
                for index, fld_name in enumerate(airport_fields)}

    runway_fields = ["Site Id", "Runway Id",
                     "Length", "Surface Type Condition"]
    runway_fields += ["Base End Id", "Base True Heading"]
    runway_fields += ["Base Elevation",
                      "Base Latitude DMS", "Base Longitude DMS"]
    runway_fields += ["Reciprocal End Id", "Reciprocal True Heading"]
    runway_fields += ["Reciprocal Elevation",
                      "Reciprocal Latitude DMS", "Reciprocal Longitude DMS"]
    runway_fld_pos = [0, 2, 3, 5, 15, 16, 25, 21, 23, 74, 75, 84, 80, 82]
    runways = {fld_name: runway_fld_pos[index]
               for index, fld_name in enumerate(runway_fields)}

    # Transformed fields
    trans_airports = ["Loc Id", "State Id", "Elevation",
                      "Pattern_Altitude", "Latitude", "Longitude"]
    trans_runways = ["Loc Id", "Runway Id", "Length", "Surface Type Condition",
                     "True Hdg", "Elevation", "Latitude", "Longitude"]

    all_fields = [airports, trans_airports, runways, trans_runways]
    return all_fields


def get_csv_objects(start_path: str):
    '''
    Inputs a path string.
    Builds a set of CSV Readers and Writers
    for the airport and runway csv files.

    OUTPUT: List of [arp_read, arp_write, rnwy_read, rnwy_write]
    '''
    base_path = pathlib.Path(start_path)
    airport_file_name = "all_airports.csv"
    runway_file_name = "all_runways.csv"
    airport_out_name = "airports.csv"
    runway_out_name = "runways.csv"
    airport_file = base_path / airport_file_name
    runway_file = base_path / runway_file_name
    airport_out_file = base_path / airport_out_name
    runway_out_file = base_path / runway_out_name

    try:
        airport_csv = open(airport_file, "r", encoding='utf-8-sig')
        runway_csv = open(runway_file, "r", encoding='utf-8-sig')
    except IOError as e:
        print(f"Error opening input files: {e}")
        sys.exit()

    try:
        airport_csv_out = open(airport_out_file, "w", newline="")
        runway_csv_out = open(runway_out_file, "w", newline="")
    except IOError as e:
        print(f"Error opening output files: {e}")
        sys.exit()

    airport_reader = csv.reader(airport_csv, dialect="excel")
    runway_reader = csv.reader(runway_csv, dialect="excel")
    airport_writer = csv.writer(airport_csv_out, dialect="excel")
    runway_writer = csv.writer(runway_csv_out, dialect="excel")

    csv_objects = [airport_reader, airport_writer]
    csv_objects += [runway_reader, runway_writer]
    csv_objects += [airport_csv, airport_csv_out]
    csv_objects += [runway_csv, runway_csv_out]

    return csv_objects


def close_files(file_objects: list):
    # Closes open CSV files.

    is_closed = False
    airport_csv, airport_csv_out = file_objects[0:2]
    runway_csv, runway_csv_out = file_objects[2:4]

    try:
        airport_csv.close()
        runway_csv.close()
        airport_csv_out.close()
        runway_csv_out.close()
    except IOError as e:
        print(f"Error closing files: {e}")
        sys.exit()

    is_closed = True
    return is_closed


def parse_runways(airport_id, runway_reader, runways, next_row):
    '''
    Using Airport_ID, determines if rows in runway file
    are for the specific airport.
    Uses tans_airport_mod (tam) to determine
    if the runways are desireable for the database.

    Returns list of runways, and last row read.
    Returns empty list if runways not desireable.
    '''

    # Read past runways for skipped airports.
    while next_row[0] < airport_id:
        next_row = next(runway_reader)

    all_runways = []
    while next_row[0] == airport_id:
        runway = {column: next_row[runways[column]] for column in runways}
        if not runway["Runway Id"].startswith("H"):
            all_runways.append(runway)
        try:
            next_row = next(runway_reader)
        except:
            break

    if all_runways:
        if tam.is_long_enough(all_runways) and tam.is_paved(all_runways):
            return [all_runways, next_row]
        else:
            all_runways = []

    return [all_runways, next_row]


##################################################
################ MAIN CODE START #################
##################################################
print("Starting...")

start_path = "<root dir>"
all_fields = set_fields()
airports = all_fields[0]
trans_airports = all_fields[1]
runways = all_fields[2]
trans_runways = all_fields[3]

csv_objects = get_csv_objects(start_path)
airport_reader, airport_writer = csv_objects[0:2]
runway_reader, runway_writer = csv_objects[2:4]
file_objects = csv_objects[4:]

# Advance reader position past header.
# Write header in transformed output file.
arp_header = next(airport_reader)
rwy_header = next(runway_reader)
trans_arp_header = [col_name for col_name in trans_airports]
trans_rwy_header = [col_name for col_name in trans_runways]
airport_writer.writerow(trans_arp_header)
runway_writer.writerow(trans_rwy_header)

next_row = [""]
for airport_row in airport_reader:
    airport = {column: airport_row[airports[column]] for column in airports}
    if tam.is_airport(airport) and tam.is_public(airport):
        airport_id = airport["Site Id"]
        all_runways, next_row = parse_runways(
            airport_id, runway_reader, runways, next_row)
        if all_runways:
            trans_airport = tam.transform_airport_data(airport)
            loc_id = trans_airport["Loc Id"]
            trans_runways = tam.transform_runway_data(loc_id, all_runways)
            trans_airport_row = [trans_airport[column]
                                 for column in trans_airport]
            airport_writer.writerow(trans_airport_row)

            for each_runway in trans_runways:
                trans_runway_row = [each_runway[column]
                                    for column in each_runway]
                runway_writer.writerow(trans_runway_row)

is_closed = close_files(file_objects)

print("Finished")
