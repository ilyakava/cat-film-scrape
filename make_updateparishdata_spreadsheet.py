"""
Example usage:
python3 make_cpe_spreadsheet.py "cpe_data/*.html" "cpe.tsv"
"""
import argparse
import collections
from dataclasses import dataclass
import glob
import json
import os

import validators
from models import Person, Phone

from tqdm import tqdm

def _remove_trailing_nonalpha(text):
    lasti = len(text) - 1
    while text[lasti] not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
        lasti -= 1
    return text[:lasti+1]

def _truncate_church_name(text):
    lasti = 0
    while lasti < len(text):
        if lasti > 5 and text[lasti] not in ' .abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
            break
        lasti += 1
    return text[:lasti].strip()

def _remove_chars(text, chars):
    outtext = []
    for c in text:
        if c in chars:
            continue
        outtext.append(c)
    return "".join(outtext)

def _get_first_identity(s):
    s, *rest = s.split(",")
    s, *rest = s.split("-")
    s, *rest = s.split(";")
    s, *rest = s.split("/")
    s = s.replace("\t", " ")
    return s

_BAD_EMAILS = ("hyperdreams", )

# words are followed by a space
_PASTOR_TITLE_WORDS = ("Administrator", "Bishop", "Cardinal", "Deacon", "Dean", "Father", "Monsignor", "Pastoral", "Reverend", "Pastor", "RIGHT", "The", "Very", "Emeritius", "Parochial", "Mother", "Farther", "(Administrator)", "Reverendo", "Fathers")
# abbreviations are followed by a period or a space
_PASTOR_TITLE_ABBREVIATIONS = ("Dcn", "Dn", "Dr", "Fr", "GB", "Lm", "Mon", "Most", "Msgr", "Pbro", "Re", "Rev", "Rt", "V", "ev")

def _startswith_title(identity):
    lid = identity.lower()
    # equal
    for title in _PASTOR_TITLE_WORDS:
        if lid == title.lower():
            return title
    for title in _PASTOR_TITLE_ABBREVIATIONS:
        if lid == title.lower():
            return title
    # startswith
    for title in _PASTOR_TITLE_WORDS:
        if not lid.startswith(f"{title.lower()} "):
            continue
        return title
    for title in _PASTOR_TITLE_ABBREVIATIONS:
        if lid.startswith(f"{title.lower()} ") or lid.startswith(f"{title.lower()}."):
            return title
    return ""

def _split_titles(identity):
    titles = []
    while _startswith_title(identity):
        t = _startswith_title(identity)
        identity = identity[len(t):]
        if identity.startswith("."):
            identity = identity[1:]
        identity = identity.strip()
        # fix spellings
        if t == "Farther" or t == "Fathers":
            t = "Father"
        if t == "(Administrator)":
            t = "Administrator"
        titles.append(t)
    return " ".join(titles), identity

    

@dataclass
class Pastor:
    title: str = ""
    first: str = ""
    middle: str = ""
    last: str = ""
    names_text: str = ""

    def __init__(self, pastor_name_text):
        fid = _get_first_identity(pastor_name_text)
        fid = _remove_chars(fid, "?:+")
        fid = fid.strip()

        self.title, names_text = _split_titles(fid)

        
        self.names_text = names_text.strip()
        rest = Person(self.names_text.split(" "))
        self.first = rest.first
        self.middle = rest.middle
        self.last = rest.last

        # if self.first.startswith("Mat") or self.first.startswith("Mardean") or self.first.startswith("Satheesh"):
        #     return
        # if self.first.startswith("Theo"):
        #     return
        # for title in _PASTOR_TITLE_WORDS:
        #     if title.lower() in self.first.lower():
        #         print(f"<{names_text}> HAS WORD {title} OF <{fid}> FROM <{pastor_name_text}>")
        # for title in _PASTOR_TITLE_ABBREVIATIONS:
        #     if f"{title} ".lower() in self.first.lower():
        #         print(f"<{names_text}> HAS ABR {title} OF <{fid}> FROM <{pastor_name_text}>")
        #     if f"{title}.".lower() in self.first.lower():
        #         print(f"<{names_text}> HAS ABR {title} OF <{fid}> FROM <{pastor_name_text}>")



@dataclass
class Church:
    short_name: str = ""
    full_name: str = ""
    email: str = ""
    title: str = ""
    first: str = ""
    middle: str = ""
    last: str = ""
    raw_pastor_text: str = ""
    type_name: str = ""
    diocese_name: str = ""
    diocese_type_name: str = ""
    rite_type_name: str = ""
    english: bool = False
    language: str = ""
    lat: float = 0.0
    lng: float = 0.0
    street: str = ""
    state: str = ""
    zip: str = ""
    phone: str = ""
    phone_ext: str = ""
    website: str = ""
    last_updated: str = ""
    id: str = ""
    

    def fill(self, details_dict):
        self.full_name = details_dict.pop("name", "")
        if self.full_name:
            self.short_name = _truncate_church_name(self.full_name)
        self.type_name = details_dict.pop("church_type_name", "")
        self.diocese_name = details_dict.pop("diocese_name", "")
        self.diocese_type_name = details_dict.pop("diocese_type_name", "")
        self.rite_type_name = details_dict.pop("rite_type_name", "")
        self.id = details_dict.pop("id", "")
        lat_string = details_dict.pop("latitude", "")
        if lat_string:
            self.lat = float(lat_string)
        lng_string = details_dict.pop("longitude", "")
        if lng_string:
            self.lng = float(lng_string)
        email = details_dict.pop("email", "")
        if email and "@" in email:
            self.email = _remove_trailing_nonalpha(email.strip())
            if any(bad in email for bad in _BAD_EMAILS):
                self.email = ""
        website_url = details_dict.pop("url", "")
        if validators.url(website_url):
            self.website = website_url

        pastor_name_text = details_dict.pop("pastors_name", "")
        if pastor_name_text:
            self.raw_pastor_text = pastor_name_text
            pastor = Pastor(pastor_name_text)
            self.title = pastor.title
            self.first = pastor.first
            self.middle = pastor.middle
            self.last = pastor.last
            

        phone_text = details_dict.pop("phone", "")
        if not phone_text:
            phone_text = details_dict.pop("phone_number", "")
        if phone_text:
            phone = Phone(phone_text)
            self.phone = phone.number
            self.phone_ext = phone.extension

        self.last_updated = details_dict.pop("last_update", "")

        lang = details_dict.pop("language_name", "").lower().strip()
        self.language = lang
        if "english" in lang:
            self.english = True

        self.city = details_dict.pop("church_address_city_name", "")
        self.state = details_dict.pop("church_address_providence_name", "")
        self.zip = details_dict.pop("church_address_postal_code", "")
        self.street = details_dict.pop("church_address_street_address", "")

        ignore_fields = ("church_address_country_territory_name", "church_address_county", "comments", "lat_long_source", "military_time", "wheel_chair_access", "distance", "resultID", "directions", "church_worship_times")
        for field in ignore_fields:
            details_dict.pop(field, None)

        return details_dict
    
    @classmethod
    def header(cls):
        return "id\tshort_name\tfull_name\temail\ttitle\tfirst\tmiddle\tlast\traw_pastor_text\ttype_name\tdiocese_name\tdiocese_type_name\trite_type_name\tenglish\tlanguage\tlat\tlng\tstreet\tstate\tzip\tphone\tphone_ext\twebsite\tlast_updated"
    
    def __str__(self):
        return f"{self.id}\t{self.short_name}\t{self.full_name}\t{self.email}\t{self.title}\t{self.first}\t{self.middle}\t{self.last}\t{self.raw_pastor_text}\t{self.type_name}\t{self.diocese_name}\t{self.diocese_type_name}\t{self.rite_type_name}\t{self.english}\t{self.language}\t{self.lat}\t{self.lng}\t{self.street}\t{self.state}\t{self.zip}\t{self.phone}\t{self.phone_ext}\t{self.website}\t{self.last_updated}"

def get_filenames(file_pattern):
    filenames = []
    if os.path.isfile(file_pattern):
        filenames.append(file_pattern)
    else:
        filenames.extend(glob.glob(file_pattern))
    for filename in filenames:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File {filename} does not exist")
    return filenames

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process json files scraped.")
    parser.add_argument("--input", help="Path to the input directory")
    parser.add_argument("--output", help="Path to the output file")
    args = parser.parse_args()


    filenames = get_filenames(args.input)
    print(f"Processing {len(filenames)} files...")

    churches = {}
    nrecords = 0
    emails = set()

    for filename in tqdm(filenames):
        with open(filename, 'r') as file:
            data = json.load(file)
            for record in data:
                parsed_church = Church()
                nrecords += 1
                leftover = parsed_church.fill(record)
                if leftover:
                    print(f"Some unused keys in {leftover}")
                    exit(0)
                if not parsed_church.id:
                    print(f"Church with no ID: {parsed_church}")
                    exit(0)
                if parsed_church.id and id not in churches:
                    churches[parsed_church.id] = parsed_church
                emails.add(parsed_church.email)
    
    print(f"Found {len(churches)} churches in {nrecords} records")
    print(f"Found {len(emails)} unique emails")


    with open(args.output, "w") as f:
        f.write(Church.header() + "\n")
        for church in churches.values():
            f.write(str(church) + "\n")
    print(f"TSV file created: {args.output} with {len(churches)} rows.")
