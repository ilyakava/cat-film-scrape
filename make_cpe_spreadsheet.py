"""
Example usage:
python3 make_cpe_spreadsheet.py "cpe_data/*.html" "cpe.tsv"
"""
import argparse
import os
import re
import glob
import argparse
from dataclasses import dataclass
import warnings

from bs4 import BeautifulSoup
from tqdm import tqdm
import validators

from models import Contact, ProgramDetails, Phone, parse_address, email_to_person

@dataclass
class Program:
    name: str
    address: str
    street: str
    city: str
    state: str
    zip: str
    phone: str
    phone_ext: str
    website: str
    email: str
    first: str
    middle: str
    last: str
    units_offered: str

    def __init__(self):
        pass

    def fill(self, details_dict):
        self.name = details_dict.pop("name", "")
        self.address = details_dict.pop("address", "")
        


        parsed_address = parse_address(self.address)
        if parsed_address is None and self.address:
            raise ValueError(f"Could not parse address: {self.address}")
        
        if self.address:
            self.street = parsed_address.pop("street", "")
            self.city = parsed_address.pop("city", "")
            self.state = parsed_address.pop("state", "")
            self.zip = parsed_address.pop("zip", "")
        else:
            self.street = self.city = self.state = self.zip = ""
        
        phone_text = details_dict.pop("phone", "")
        phone = Phone(phone_text)
        self.phone = phone.number
        self.phone_ext = phone.extension
        self.website = details_dict.pop("website", "")
        self.email = details_dict.pop("email", "")
        if self.email:
            person = email_to_person(self.email)
            if person is not None:
                self.first, self.middle, self.last = person.first, person.middle, person.last
            else:
                self.first = self.middle = self.last = ""
        else:
            self.first = self.middle = self.last = ""
        self.units_offered = details_dict.pop("units offered", "")
        
        return details_dict
    
    def __str__(self):
        return f"{self.name}\t{self.street}\t{self.city}\t{self.state}\t{self.zip}\t{self.address}\t{self.phone}\t{self.phone_ext}\t{self.website}\t{self.email}\t{self.first}\t{self.middle}\t{self.last}\t{self.units_offered}"

    @classmethod
    def header(cls):
        return "Name\tStreet\tCity\tState/Province Code\tZip/Postal Code\tAddress\tPhone Number\tPhone Extension\tWebsite\tEmail\tGuessed First\tGuessed Middle\tGuessed Last\tUnits Offered"

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

def _contacts(soup, file_path):
    contacts = []
    table = soup.find("table")
    if not table:
        print(f"No contacts table found in the HTML file {file_path}")
        return contacts
    rows = table.find_all("tr")
    if not rows:
        raise ValueError("No rows found in the table")
    header, *rest = rows
    for row in rest:
        items = row.find_all("td")
        contacts.append(Contact([item.text.strip() for item in items]))
    return contacts

def _unify_key(key):
    key = key.lower()
    if key.startswith("phone"):
        return "phone"
    if key.startswith("website"):
        return "website"
    if key == "extended":
        return "units offered"
    if key == "location":
        return "address"
    if key == "other email": # appears to be only email for this record
        return "email"
    return key

def _programs(soup, file_path):
    ret = []
    details_dict = {}
    programs = soup.find_all("h3", class_="wp-block-heading")
    if not programs:
        return ret
        # raise ValueError(f"No programs found in the HTML file: {file_path}")
    for program in programs:
        parsed_program = Program()
        details_dict = {}
        details_dict["name"] = program.text
        next_element = program.find_next_sibling()
        while next_element is not None and next_element.name == "p":
            item = next_element.text
            if ":" not in item:
                next_element = next_element.find_next_sibling()
                continue
                # raise ValueError(f"Item {item} does not have a colon")
            key, value = item.split(":", 1)
            key = key.strip()
            value = value.strip().replace("\n", " ")
            details_dict[_unify_key(key)] = value
            # move to next
            next_element = next_element.find_next_sibling()
        leftover = parsed_program.fill(details_dict)
        if leftover:
            print(f"Some unused keys/values in {leftover}, used {parsed_program}")
        ret.append(parsed_program)
    return ret

def format_one_file(file_path):
    out = []
    if not file_path.endswith(".html"):
        raise ValueError(f"File must be an HTML file: {file_path}")
    id = os.path.splitext(os.path.basename(file_path))[0]
    with open(file_path, "r") as html_content:
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        soup = BeautifulSoup(html_content, "html.parser")
        # contacts = _contacts(soup, file_path)
        return _programs(soup, file_path)
    #     for contact in contacts:
    #         out.append(f"{id}\t{contact}\t{details}")
    # return out
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process HTML files in a CPE directory.")
    parser.add_argument("input", help="Path to the input directory")
    parser.add_argument("output", help="Path to the output file")
    parser.add_argument("-e", "--exclude", help="Path to the TSV file to exclude")
    args = parser.parse_args()

    ignore_emails = set()
    if args.exclude:
        idx = None
        with open(args.exclude, "r") as f:
            for i, line in enumerate(f):
                if idx is None:
                    headers = line.strip().split("\t")
                    for j, header in enumerate(headers):
                        if header.lower() == "email":
                            idx = j
                            break
                if idx is not None and i > 0:
                    items = line.strip().split("\t")
                    email = items[idx]
                    if email:
                        ignore_emails.add(email)
        if not ignore_emails:
            raise ValueError(f"No emails found in the exclude file: {args.exclude}")
        print(f"Loaded {len(ignore_emails)} emails to ignore")

    if not args.input or not args.output:
        raise ValueError("Input and output paths must be provided")
    
    filenames = get_filenames(args.input)
    print(f"Processing {len(filenames)} files...")
    out = []
    for filename in tqdm(filenames):
        id = os.path.splitext(os.path.basename(filename))[0]
        new_rows = format_one_file(filename)
        # print(new_rows)
        for row in new_rows:
            if row.email in ignore_emails:
                print(f"Ignoring email: {row.email}")
                continue
            out.append(f"{id}\t{row}")
    
    header = f"ID\t{Program.header()}"

    with open(args.output, "w") as f:
        f.write(header + "\n")
        for row in out:
            f.write(row + "\n")
    print(f"TSV file created: {args.output} with {len(out)} rows.")
