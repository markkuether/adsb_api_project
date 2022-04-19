import re


def is_airport(airport: dict):
    # Used to seperate out airports from heliports or seaports
    return airport["Facility Type"].upper() == "AIRPORT"


def is_public(airport: dict):
    # Used to seperate out private from public airports
    return airport["Use"].upper() == "PU"


def is_paved(runways: list):
    # Used to seperate out only grass strips
    paved = False
    for rwy in runways:
        surface = rwy["Surface Type Condition"]
        if surface.startswith("ASPH") or surface.startswith("CONC"):
            paved = True
            break
    return paved


def is_long_enough(runways: list):
    # Used to test if runways long enough.
    long_enough = False
    for rwy in runways:
        if int(rwy["Length"]) >= 2000:
            long_enough = True
            break
    return long_enough


def use_airport(airport: dict, runways: list):
    # Tests various conditions to determine if we want to use this airport.
    can_use = is_airport(airport) and is_public(
        airport) and is_long_enough(runways) and is_paved(runways)
    return can_use


def dms_to_dd(dms: str):
    '''
    Converts dms to d.dec
    Inputs string "DD-MM-SS.ssssNW"
    returns float (-)DD.ddddd
    returns 0.0 if no postion found.
    '''
    p = re.compile("\d+[-]\d+[-]\d+[.]\d+[NSEW]$")
    if not bool(p.match(dms)):
        return 0.0

    degrees = 0
    minutes = 1
    seconds = 2
    dms = dms.upper()

    dms_parts = dms.split("-")
    ending = dms_parts[seconds][-1]

    dms_parts[seconds] = dms_parts[seconds][0:-1]
    dec_deg = float(dms_parts[degrees])
    dec_min = float(dms_parts[minutes])/60
    dec_sec = float(dms_parts[seconds])/3600
    deg_dec = round(dec_deg + dec_min + dec_sec, 8)
    if ending in ["W", "S"]:
        deg_dec *= -1

    return deg_dec


def transform_airport_data(airport: dict):
    '''
    Assigns airport data to updated field names.
    Changes Lat and Lon data from DMS to DD format.
    Ensures Pattern Altitude is populated.

    Returns transformed airport dictionary
    '''
    trans_airport = {}
    trans_airport["Loc Id"] = airport["Loc Id"]
    trans_airport["State Id"] = airport["State Id"]
    trans_airport["Elevation"] = airport["Elevation"]
    if not airport["Traffic Pattern Altitude"]:
        elevation = float(airport["Elevation"])
        trans_airport["Pattern Altitude"] = int(elevation)+1000
    else:
        trans_airport["Pattern Altitude"] = airport["Traffic Pattern Altitude"]

    trans_airport["Latitude"] = dms_to_dd(airport["ARP Latitude"])
    trans_airport["Longitude"] = dms_to_dd(airport["ARP Longitude"])

    return trans_airport


def transform_runway_data(airport: str, runways: list):
    '''
    Replaces airport Site Id with Loc ID for lookup
    Breaks runways into seperate records
    Assigns runway data to updated field names.
    Changes Lat and Lon data from DMS to DD format.

    Returns list of transformed runways dictionaries
    '''

    rwy_list = []
    for runway_combo in runways:
        two_rwys = runway_combo["Runway Id"].split("/")
        is_base = True
        for rwy in two_rwys:
            this_rwy = {}
            this_rwy["Loc Id"] = airport
            this_rwy["Runway Id"] = chr(34) + str(rwy) + chr(34)
            this_rwy["Length"] = runway_combo["Length"]
            this_rwy["Surface Type Condition"] = runway_combo["Surface Type Condition"]
            if is_base:
                this_rwy["True Hdg"] = runway_combo["Base True Heading"]
                this_rwy["Elevation"] = runway_combo["Base Elevation"]
                this_rwy["Latitude"] = dms_to_dd(
                    runway_combo["Base Latitude DMS"])
                this_rwy["Longitude"] = dms_to_dd(
                    runway_combo["Base Longitude DMS"])
            else:
                this_rwy["True Hdg"] = runway_combo["Reciprocal True Heading"]
                this_rwy["Elevation"] = runway_combo["Reciprocal Elevation"]
                this_rwy["Latitude"] = dms_to_dd(
                    runway_combo["Reciprocal Latitude DMS"])
                this_rwy["Longitude"] = dms_to_dd(
                    runway_combo["Reciprocal Longitude DMS"])
            is_base = not is_base
            rwy_list.append(this_rwy)
    return rwy_list
