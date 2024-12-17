from dataclasses import dataclass
import re
import usaddress


def _break_full_name(full_identity):
    if not full_identity:
        return "", "", ""
    identifiers = full_identity.split(",")
    full_name, *degrees = identifiers
    names = full_name.split()
    names = [name.capitalize() if name.islower() or name.isupper() else name for name in names]
    if len(names) == 1:
        return names[0], "", ""
    elif len(names) == 2:
        return names[0], "", names[1]
    else:
        return names[0], " ".join(names[1:-1]), names[-1]

@dataclass
class Contact:
    full_name: str
    email: str
    phone: str
    phone_ext: str
    first_name: str
    middle_name: str
    last_name: str

    def __init__(self, text_list):
        if len(text_list) < 2:
            raise ValueError("Expected name and email in contact")
        self.full_name = text_list[0]
        self.first_name, self.middle_name, self.last_name = _break_full_name(self.full_name)
        self.email = text_list[1]
        if len(text_list) > 2:
            phone = Phone(text_list[2])
            self.phone = phone.number
            self.phone_ext = phone.extension
        else:
            self.phone = ""
            self.phone_ext = ""

    def __str__(self):
        return f"{self.first_name}\t{self.middle_name}\t{self.last_name}\t{self.email}\t{self.phone}\t{self.phone_ext}"
    
    @classmethod
    def header(cls):
        return "First Name\tMiddle Name\tLast Name\tEmail\tPhone\tPhone Ext"

@dataclass
class Person:
    first: str
    middle: str
    last: str

    def __init__(self, names):
        names = [re.sub(r'[^a-zA-Z-]', '', name.capitalize()) for name in names]
        if len(names) == 1:
            self.first = names[0]
            self.middle = ""
            self.last = ""
        elif len(names) == 2:
            self.first = names[0]
            self.middle = ""
            self.last = names[1]
        else:
            self.first = names[0]
            self.middle = names[1]
            self.last = names[2]

@dataclass
class Phone:
    number: str
    extension: str

    def __init__(self, s):
        digits = re.findall(r'\d', s)
        
        if len(digits) < 10:
            self.number = ""
            self.extension = ""
            return
        
        if len(digits) == 10 or len(digits) == 11:
            self.number = "".join(digits)
            self.extension = ""
            return
        
        all_digits = "".join(digits)
        self.number = all_digits[:10]
        self.extension = all_digits[10:]

def _email_to_person(address, separator="."):
    parts = address.split(separator)
    if len(parts) > 3:
        return None
    return Person(parts)

def email_to_person(email):
    if not email:
        return None
    address = email.split("@")[0]
    if "." in address:
        return _email_to_person(address, ".")
    elif "_" in address:
        return _email_to_person(address, "_")
    else:
        return None

def parse_address(address_string):
    """
    This function parses an address string into street, city, state, and zip using usaddress library.

    Args:
        address_string: The address string to parse.

    Returns:
        A dictionary containing keys 'street', 'city', 'state', and 'zip', or None if parsing fails.
    """
    # Parse the address using usaddress.tag
    if not address_string:
        return None
    
    try:
        parsed_data, address_type = usaddress.tag(address_string)

        # Extract relevant components from the parsed data (OrderedDict)
        if parsed_data:
            address_components = {
                'street': f"{parsed_data.get('AddressNumber', '')} {parsed_data.get('StreetName', '')} {parsed_data.get('StreetNamePostType', '')} {parsed_data.get('StreetNamePostDirectional', '')}",
                'city': parsed_data.get('PlaceName', ''),
                'state': parsed_data.get('StateName', ''),
                'zip': parsed_data.get('ZipCode', '')
            }
            return address_components
        else:
            return None
    except usaddress.RepeatedLabelError:
        start, *rest = address_string.split(',')
        rest = ','.join(rest)
        ret_dict = parse_address(rest)
        if ret_dict is None:
            raise ValueError(f"Got None in recursive address parsing of: {address_string}")
        ret_dict['street'] = f"{start}, {ret_dict['street']}"
        return ret_dict

@dataclass
class ProgramDetails:
    account_name: str
    program_type: str
    street: str
    city: str
    state: str
    zip: str
    account_phone: str
    account_phone_ext: str
    account_fax: str
    account_fax_ext: str
    website: str
    other_email: str

    def __init__(self):
        pass
   

    def fill(self, details_dict):
        self.account_name = details_dict.pop("Account Name", "")
        self.program_type = details_dict.pop("Program Type", "")
        self.street = details_dict.pop("Street", "")
        self.city = details_dict.pop("City", "")
        self.state = details_dict.pop("Shipping State/Province Code", "")
        self.zip = details_dict.pop("Zip/Postal Code", "")

        account_phone = Phone(details_dict.pop("Account Phone", ""))
        account_fax = Phone(details_dict.pop("Account Fax", ""))

        self.account_phone = account_phone.number
        self.account_phone_ext = account_phone.extension
        self.account_fax = account_fax.number
        self.account_fax_ext = account_fax.extension
        
        self.website = details_dict.pop("Website", "")
        self.other_email = details_dict.pop("Other Email", "")
        return details_dict

    def size(self):
        """
        Input fields like name and phone that are split to multiple internal fields
        should not be counted as multiples
        """
        count = 0
        fields = [self.account_name, self.program_type, self.street, self.city, self.state, self.zip, self.account_phone, self.account_fax, self.website]
        for field in fields:
            if field:
                count += 1
        return count

    @classmethod
    def header(cls):
        return "Account Name\tProgram Type\tStreet\tCity\tState/Province Code\tZip/Postal Code\tAccount Phone\tAccount Phone Ext\tAccount Fax\tAccount Fax Ext\tWebsite"
    
    def __str__(self):
        return f"{self.account_name}\t{self.program_type}\t{self.street}\t{self.city}\t{self.state}\t{self.zip}\t{self.account_phone}\t{self.account_phone_ext}\t{self.account_fax}\t{self.account_fax_ext}\t{self.website}\t{self.other_email}"
