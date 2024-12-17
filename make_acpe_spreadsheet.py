"""
Example usage:
python3 make_acpe_spreadsheet.py "data/*.html" "./cpe.tsv"
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

from models import Contact, ProgramDetails


def get_filenames(file_pattern):
    filenames = []
    if os.path.isfile(file_pattern):
        filenames.append(file_pattern)
    else:
        filenames.extend(glob.glob(file_pattern))
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

def _program_details(soup):
    program_details_div = soup.find("div", class_="card-heading", text=re.compile(r"^Program Details"))
    if not program_details_div:
        raise ValueError("No program details found in the HTML file")
    span = program_details_div.find_next("span")
    if not span:
        raise ValueError("No span found after the program details div")
    list_items = span.find_all("li")
    if not list_items:
        raise ValueError("No list items found in the program details")
    list_texts = [item.text.strip() for item in list_items]
    details_dict = {}
    for i, item in enumerate(list_texts):
        if "\n" not in item:
            continue # its empty
        key, value = item.split("\n", 1)
        key = key.strip()
        value = value.strip().replace("\n", " ")
        
        if key == "Website":
            website_li = list_items[i]
            website_a = website_li.find("a")
            if not website_a:
                continue
            website_url = website_a.get("href")
            if not validators.url(website_url):
                print(f"Found Invalid website URL: {website_url}")
                continue
            details_dict[key] = website_url
        else:
            details_dict[key] = value
                
            
    ret = ProgramDetails()
    leftover = ret.fill(details_dict)
    if leftover:
        print(f"Some unused keys in {leftover.keys()}")
    return ret

def format_one_file(file_path):
    out = []
    if not file_path.endswith(".html"):
        raise ValueError("File must be an HTML file")
    id = os.path.splitext(os.path.basename(file_path))[0]
    with open(file_path, "r") as html_content:
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        soup = BeautifulSoup(html_content, "html.parser")
        contacts = _contacts(soup, file_path)
        details = _program_details(soup)
        # if the details has an email add an extra contact
        if details.other_email:
            contacts.append(Contact(["", details.other_email]))
            details.other_email = ""
        # dedupe based on email
        emails = set()
        out_contacts = []
        for contact in contacts:
            if contact.email not in emails:
                emails.add(contact.email)
                out_contacts.append(contact)
        for contact in out_contacts:
            out.append(f"{id}\t{contact}\t{details}")
    return out
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process HTML files in a directory.")
    parser.add_argument("input", help="Path to the input directory")
    parser.add_argument("output", help="Path to the output file")
    args = parser.parse_args()

    if not args.input or not args.output:
        raise ValueError("Input and output paths must be provided")

    filenames = get_filenames(args.input)
    print(f"Processing {len(filenames)} files...")
    out = []
    for filename in tqdm(filenames):
        new_rows = format_one_file(filename)
        for row in new_rows:
            out.append(row)
    
    header = f"ID\t{Contact.header()}\t{ProgramDetails.header()}"

    with open(args.output, "w") as f:
        f.write(header + "\n")
        for row in out:
            f.write(row + "\n")
    print(f"TSV file created: {args.output} with {len(out)} rows.")
