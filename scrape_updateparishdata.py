"""
Example usage:
python3 -u scrape_updateparishdata.py --output data/updateparishdata --dry-run | tee data/updateparishdata/logs/dry.txt

python3 -u scrape_updateparishdata.py --output data/updateparishdata/canada | tee data/updateparishdata/logs/canada.txt
"""
import argparse
from dataclasses import dataclass
import json
import os
from geopy.geocoders import Nominatim
from typing import Tuple
import requests
import datetime
import time

@dataclass
class Request:
    response: json
    lat: float
    lng: float
    city: str
    page: int

# _URL = "https://apiv4.updateparishdata.org/Churchs/?lat=38.5815719&long=-121.4943996&pg=1"
_WIKI_USA_CITIES = ["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ", "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "Jacksonville, FL", "Austin, TX", "Fort Worth, TX", "San Jose, CA", "Columbus, OH", "Charlotte, NC", "Indianapolis, IN", "San Francisco, CA", "Seattle, WA", "Denver, CO", "Oklahoma City, OK", "Nashville, TN", "Washington, DC", "El Paso, TX", "Las Vegas, NV", "Boston, MA", "Detroit, MI", "Portland, OR", "Louisville, KY", "Memphis, TN", "Baltimore, MD", "Milwaukee, WI", "Albuquerque, NM", "Tucson, AZ", "Fresno, CA", "Sacramento, CA", "Mesa, AZ", "Atlanta, GA", "Kansas City, MO", "Colorado Springs, CO", "Omaha, NE", "Raleigh, NC", "Miami, FL", "Virginia Beach, VA", "Long Beach, CA", "Oakland, CA", "Minneapolis, MN", "Bakersfield, CA", "Tulsa, OK", "Tampa, FL", "Arlington, TX", "Wichita, KS", "Aurora, CO", "New Orleans, LA", "Cleveland, OH", "Honolulu, HI", "Anaheim, CA", "Henderson, NV", "Orlando, FL", "Lexington, KY", "Stockton, CA", "Riverside, CA", "Corpus Christi, TX", "Irvine, CA", "Cincinnati, OH", "Santa Ana, CA", "Newark, NJ", "Saint Paul, MN", "Pittsburgh, PA", "Greensboro, NC", "Durham, NC", "Lincoln, NE", "Jersey City, NJ", "Plano, TX", "Anchorage, AK", "North Las Vegas, NV", "St. Louis, MO", "Madison, WI", "Chandler, AZ", "Gilbert, AZ", "Reno, NV", "Buffalo, NY", "Chula Vista, CA", "Fort Wayne, IN", "Lubbock, TX", "Toledo, OH", "St. Petersburg, FL", "Laredo, TX", "Irving, TX", "Chesapeake, VA", "Glendale, AZ", "Winston-Salem, NC", "Port St. Lucie, FL", "Scottsdale, AZ", "Garland, TX", "Boise, ID", "Norfolk, VA", "Spokane, WA", "Richmond, VA", "Fremont, CA", "Huntsville, AL", "Frisco, TX", "Cape Coral, FL", "Santa Clarita, CA", "San Bernardino, CA", "Tacoma, WA", "Hialeah, FL", "Baton Rouge, LA", "Modesto, CA", "Fontana, CA", "McKinney, TX", "Moreno Valley, CA", "Des Moines, IA", "Fayetteville, NC", "Salt Lake City, UT", "Yonkers, NY", "Worcester, MA", "Rochester, NY", "Sioux Falls, SD", "Little Rock, AR", "Amarillo, TX", "Tallahassee, FL", "Grand Prairie, TX", "Columbus, GA", "Augusta, GA", "Peoria, AZ", "Oxnard, CA", "Knoxville, TN", "Overland Park, KS", "Birmingham, AL", "Grand Rapids, MI", "Vancouver, WA", "Montgomery, AL", "Huntington Beach, CA", "Providence, RI", "Brownsville, TX", "Tempe, AZ", "Akron, OH", "Glendale, CA", "Chattanooga, TN", "Fort Lauderdale, FL", "Newport News, VA", "Mobile, AL", "Ontario, CA", "Clarksville, TN", "Cary, NC", "Elk Grove, CA", "Shreveport, LA", "Eugene, OR", "Aurora, IL", "Salem, OR", "Santa Rosa, CA", "Rancho Cucamonga, CA", "Pembroke Pines, FL", "Fort Collins, CO", "Springfield, MO", "Oceanside, CA", "Garden Grove, CA", "Lancaster, CA", "Murfreesboro, TN", "Palmdale, CA", "Corona, CA", "Killeen, TX", "Salinas, CA", "Roseville, CA", "Denton, TX", "Surprise, AZ", "Macon, GA", "Paterson, NJ", "Lakewood, CO", "Hayward, CA", "Charleston, SC", "Alexandria, VA", "Hollywood, FL", "Springfield, MA", "Kansas City, KS", "Sunnyvale, CA", "Bellevue, WA", "Joliet, IL", "Naperville, IL", "Escondido, CA", "Bridgeport, CT", "Savannah, GA", "Olathe, KS", "Mesquite, TX", "Pasadena, TX", "McAllen, TX", "Rockford, IL", "Gainesville, FL", "Syracuse, NY", "Pomona, CA", "Visalia, CA", "Thornton, CO", "Waco, TX", "Jackson, MS", "Columbia, SC", "Lakewood, NJ", "Fullerton, CA", "Torrance, CA", "Victorville, CA", "Midland, TX", "Orange, CA", "Miramar, FL", "Hampton, VA", "Warren, MI", "Stamford, CT", "Cedar Rapids, IA", "Elizabeth, NJ", "Palm Bay, FL", "Dayton, OH", "New Haven, CT", "Coral Springs, FL", "Meridian, ID", "West Valley City, UT", "Pasadena, CA", "Lewisville, TX", "Kent, WA", "Sterling Heights, MI", "Fargo, ND", "Carrollton, TX", "Santa Clara, CA", "Round Rock, TX", "Norman, OK", "Columbia, MO", "Abilene, TX", "Athens, GA", "Pearland, TX", "Clovis, CA", "Topeka, KS", "College Station, TX", "Simi Valley, CA", "Allentown, PA", "West Palm Beach, FL", "Thousand Oaks, CA", "Vallejo, CA", "Wilmington, NC", "Rochester, MN", "Concord, CA", "Lakeland, FL", "North Charleston, SC", "Lafayette, LA", "Arvada, CO", "Independence, MO", "Billings, MT", "Fairfield, CA", "Hartford, CT", "Ann Arbor, MI", "Broken Arrow, OK", "Berkeley, CA", "Cambridge, MA", "Richardson, TX", "Antioch, CA", "High Point, NC", "Clearwater, FL", "League City, TX", "Odessa, TX", "Manchester, NH", "Evansville, IN", "Waterbury, CT", "West Jordan, UT", "Las Cruces, NM", "Westminster, CO", "Lowell, MA", "Nampa, ID", "Richmond, CA", "Pompano Beach, FL", "Carlsbad, CA", "Menifee, CA", "Provo, UT", "Elgin, IL", "Greeley, CO", "Springfield, IL", "Beaumont, TX", "Lansing, MI", "Murrieta, CA", "Goodyear, AZ", "Allen, TX", "Tuscaloosa, AL", "Everett, WA", "Pueblo, CO", "New Braunfels, TX", "South Fulton, GA", "Miami Gardens, FL", "Gresham, OR", "Temecula, CA", "Rio Rancho, NM", "Peoria, IL", "Tyler, TX", "Sparks, NV", "Concord, NC", "Santa Maria, CA", "Ventura, CA", "Buckeye, AZ", "Downey, CA", "Sugar Land, TX", "Costa Mesa, CA", "Conroe, TX", "Spokane Valley, WA", "Davie, FL", "Hillsboro, OR", "Jurupa Valley, CA", "Centennial, CO", "Edison, NJ", "Boulder, CO", "Dearborn, MI", "Edinburg, TX", "Sandy Springs, GA", "Green Bay, WI", "West Covina, CA", "Brockton, MA", "St. George, UT", "Bend, OR", "Renton, WA", "Lee's Summit, MO", "Fishers, IN", "El Monte, CA", "South Bend, IN", "Rialto, CA", "Woodbridge, NJ", "El Cajon, CA", "Inglewood, CA", "Burbank, CA", "Wichita Falls, TX", "Vacaville, CA", "Carmel, IN", "Palm Coast, FL", "Fayetteville, AR", "Quincy, MA", "San Mateo, CA", "Chico, CA", "Lynn, MA", "Albany, NY", "Yuma, AZ", "New Bedford, MA", "Suffolk, VA", "Hesperia, CA", "Davenport, IA"]
_CANADA_CITIES = ["Toronto Ontario ", "Montreal  Quebec", "Calgary Alberta ", "Ottawa  Ontario ", "Edmonton  Alberta ", "Winnipeg  Manitoba  ", "Mississauga Ontario ", "Vancouver British Columbia  ", "Brampton  Ontario ", "Hamilton  Ontario ", "Surrey  British Columbia  ", "Quebec ", "Halifax Nova Scotia", "Laval Quebec", "London  Ontario ", "Markham Ontario ", "Vaughan Ontario ", "Gatineau  Quebec", "Saskatoon Saskatchewan  ", "Kitchener Ontario ", "Longueuil Quebec", "Burnaby British Columbia  ", "Windsor Ontario ", "Regina  Saskatchewan  ", "Oakville  Ontario", "Richmond  British Columbia  ", "Richmond Hill Ontario ", "Burlington  Ontario ", "Oshawa  Ontario ", "Sherbrooke  Quebec", "Greater Sudbury Ontario ", "Abbotsford  British Columbia  ", "Lévis Quebec", "Coquitlam British Columbia  ", "Barrie  Ontario ", "Saguenay  Quebec", "Kelowna British Columbia  ", "Guelph  Ontario ", "Trois-Rivières  Quebec", "Whitby  Ontario", "Cambridge Ontario ", "St. Catharines  Ontario ", "Milton  Ontario", "Langley British Columbia", "Kingston  Ontario ", "Ajax  Ontario", "Waterloo  Ontario ", "Terrebonne  Quebec", "Saanich British Columbia", "St. John's  Newfoundland and Labrador ", "Thunder Bay Ontario ", "Delta British Columbia  ", "Brantford Ontario ", "Chatham-Kent  Ontario", "Clarington  Ontario", "Red Deer  Alberta ", "Nanaimo British Columbia  ", "Strathcona County Alberta", "Pickering Ontario ", "Lethbridge  Alberta ", "Kamloops  British Columbia  ", "Saint-Jean-sur-Richelieu  Quebec", "Niagara Falls Ontario ", "Cape Breton Nova Scotia", "Chilliwack  British Columbia  ", "Victoria  British Columbia  ", "Brossard  Quebec", "Maple Ridge British Columbia  ", "North Vancouver British Columbia", "Newmarket Ontario", "Repentigny  Quebec", "Peterborough  Ontario ", "Saint-Jérôme  Quebec", "Moncton New Brunswick ", "Drummondville Quebec", "Kawartha Lakes  Ontario ", "New Westminster British Columbia  ", "Prince George British Columbia  ", "Caledon Ontario", "Airdrie Alberta ", "Wood Buffalo  Alberta", "Sault Ste. Marie  Ontario ", "Sarnia  Ontario ", "Saint John  New Brunswick ", "Granby  Quebec", "St. Albert  Alberta ", "Norfolk County  Ontario ", "Grande Prairie  Alberta ", "Medicine Hat  Alberta ", "Fredericton New Brunswick ", "Halton Hills  Ontario", "Aurora  Ontario", "Port Coquitlam  British Columbia  ", "Mirabel Quebec  ", "Blainville  Quebec", "North Vancouver British Columbia  ", "Saint-Hyacinthe Quebec", "Welland Ontario ", "Belleville  Ontario ", "North Bay Ontario "]
_CANADA_CITIES = [f"{city.strip()}, Canada" for city in _CANADA_CITIES]
_UK_IRELAND_CITIES = ["Bath, England, United Kingdom", "Birmingham, England, United Kingdom", "Bradford, England, United Kingdom", "Brighton & Hove, England, United Kingdom", "Bristol, England, United Kingdom", "Cambridge, England, United Kingdom", "Canterbury, England, United Kingdom", "Carlisle, England, United Kingdom", "Chelmsford, England, United Kingdom", "Chester, England, United Kingdom", "Chichester, England, United Kingdom", "Colchester, England, United Kingdom", "Coventry, England, United Kingdom", "Derby, England, United Kingdom", "Doncaster, England, United Kingdom", "Durham, England, United Kingdom", "Ely, England, United Kingdom", "Exeter, England, United Kingdom", "Gloucester, England, United Kingdom", "Hereford, England, United Kingdom", "Kingston-upon-Hull, England, United Kingdom", "Lancaster, England, United Kingdom", "Leeds, England, United Kingdom", "Leicester, England, United Kingdom", "Lichfield, England, United Kingdom", "Lincoln, England, United Kingdom", "Liverpool, England, United Kingdom", "London, England, United Kingdom", "Manchester, England, United Kingdom", "Milton Keynes, England, United Kingdom", "Newcastle-upon-Tyne, England, United Kingdom", "Norwich, England, United Kingdom", "Nottingham, England, United Kingdom", "Oxford, England, United Kingdom", "Peterborough, England, United Kingdom", "Plymouth, England, United Kingdom", "Portsmouth, England, United Kingdom", "Preston, England, United Kingdom", "Ripon, England, United Kingdom", "Salford, England, United Kingdom", "Salisbury, England, United Kingdom", "Sheffield, England, United Kingdom", "Southampton, England, United Kingdom", "Southend-on-Sea, England, United Kingdom", "St Albans, England, United Kingdom", "Stoke on Trent, England, United Kingdom", "Sunderland, England, United Kingdom", "Truro, England, United Kingdom", "Wakefield, England, United Kingdom", "Wells, England, United Kingdom", "Westminster, England, United Kingdom", "Winchester, England, United Kingdom", "Wolverhampton, England, United Kingdom", "Worcester, England, United Kingdom", "York, England, United Kingdom", "Armagh, Northern Ireland, United Kingdom", "Bangor, Northern Ireland, United Kingdom", "Belfast, Northern Ireland, United Kingdom", "Lisburn, Northern Ireland, United Kingdom", "Londonderry, Northern Ireland, United Kingdom", "Newry, Northern Ireland, United Kingdom", "Aberdeen, Scotland, United Kingdom", "Dundee, Scotland, United Kingdom", "Dunfermline, Scotland, United Kingdom", "Edinburgh, Scotland, United Kingdom", "Glasgow, Scotland, United Kingdom", "Inverness, Scotland, United Kingdom", "Perth, Scotland, United Kingdom", "Stirling, Scotland, United Kingdom", "Bangor, Wales, United Kingdom", "Cardiff, Wales, United Kingdom", "Newport, Wales, United Kingdom", "St Asaph, Wales, United Kingdom", "St Davids, Wales, United Kingdom", "Swansea, Wales, United Kingdom", "Wrexham, Wales, United Kingdom", "Dublin, Ireland", "Limerick, Ireland", "Waterford, Ireland", "Cork, Ireland", "Galway, Ireland", "Kilkenny, Ireland", "Derry, Ireland"]
_AUSTRALIA_CITIES = ["Sydney   New South Wales ", "Melbourne  Victoria", "Brisbane   Queensland", "Perth  Western Australia ", "Adelaide   South Australia ", "Gold Coast–Tweed Heads   Queensland New South Wales ", "Newcastle–Maitland   New South Wales ", "Canberra–Queanbeyan  Australian Capital Territory New South Wales ", "Sunshine Coast   Queensland", "Central Coast  New South Wales ", "Wollongong   New South Wales ", "Geelong  Victoria", "Hobart   Tasmania", "Townsville   Queensland", "Cairns   Queensland", "Toowoomba  Queensland", "Darwin   Northern Territory", "Ballarat   Victoria", "Bendigo  Victoria", "Albury–Wodonga   New South Wales Victoria", "Launceston   Tasmania", "Mackay   Queensland", "Rockhampton  Queensland", "Bunbury  Western Australia ", "Bundaberg  Queensland", "Coffs Harbour  New South Wales ", "Hervey Bay   Queensland", "Wagga Wagga  New South Wales ", "Shepparton–Mooroopna   Victoria", "Mildura–Buronga  Victoria", "Port Macquarie   New South Wales ", "Gladstone  Queensland", "Ballina  New South Wales ", "Warragul–Drouin  Victoria", "Tamworth   New South Wales ", "Busselton  Western Australia ", "Traralgon–Morwell  Victoria", "Orange   New South Wales ", "Bowral–Mittagong   New South Wales ", "Dubbo  New South Wales ", "Geraldton  Western Australia ", "Nowra–Bomaderry  New South Wales ", "Bathurst   New South Wales ", "Albany   Western Australia ", "Warrnambool  Victoria", "Devonport  Tasmania", "Mount Gambier  South Australia ", "Kalgoorlie–Boulder   Western Australia ", "Victor Harbor–Goolwa   South Australia ", "Morisset–Cooranbong  New South Wales ", "Alice Springs  Northern Territory", "Nelson Bay   New South Wales ", "Burnie–Somerset  Tasmania", "Maryborough  Queensland", "Lismore  New South Wales ", "Taree  New South Wales ", "Bacchus Marsh  Victoria", "Goulburn   New South Wales ", "Armidale   New South Wales ", "Gympie   Queensland", "Gisborne   Victoria", "Echuca–Moama   Victoria New South Wales ", "Moe–Newborough   Victoria", "Whyalla  South Australia ", "Yeppoon  Queensland", "Forster–Tuncurry   New South Wales ", "Griffith   New South Wales ", "St Georges Basin–Sanctuary Point   New South Wales ", "Wangaratta   Victoria", "Grafton  New South Wales ", "Murray Bridge  South Australia ", "Camden Haven   New South Wales ", "Karratha   Western Australia ", "Mount Isa  Queensland", "Batemans Bay   New South Wales ", "Broken Hill  New South Wales ", "Singleton  New South Wales ", "Ulladulla  New South Wales ", "Port Lincoln   South Australia ", "Horsham  Victoria", "Port Hedland   Western Australia ", "Kempsey  New South Wales ", "Warwick  Queensland", "Medowie  New South Wales ", "Broome   Western Australia ", "Bairnsdale   Victoria", "Airlie Beach–Cannonvale  Queensland", "Ulverstone   Tasmania", "Sale   Victoria", "Emerald  Queensland", "Port Pirie   South Australia ", "Port Augusta   South Australia ", "Colac  Victoria", "Muswellbrook   New South Wales ", "Esperance  Western Australia ", "Mudgee   New South Wales ", "Lithgow  New South Wales ", "Castlemaine  Victoria", "Portland   Victoria", "Byron Bay  New South Wales ", "Swan Hill  Victoria", "Kingaroy   Queensland"]
_AUSTRALIA_CITIES = [f"{city.strip()}, Australia" for city in _AUSTRALIA_CITIES]
_NEW_ZEALAND_CITIES = ["Auckland, New Zealand", "Christchurch, New Zealand", "Wellington, New Zealand", "Hamilton, New Zealand", "Tauranga, New Zealand", "Lower Hutt, New Zealand", "Dunedin, New Zealand", "Palmerston North, New Zealand", "Napier, New Zealand", "Hibiscus Coast, New Zealand", "Porirua, New Zealand", "New Plymouth, New Zealand", "Rotorua, New Zealand", "Whangarei, New Zealand", "Nelson, New Zealand", "Hastings, New Zealand", "Invercargill, New Zealand", "Upper Hutt, New Zealand", "Whanganui, New Zealand", "Gisborne, New Zealand"]
_WIKI_CITIES = _UK_IRELAND_CITIES + _AUSTRALIA_CITIES + _NEW_ZEALAND_CITIES
_REQUEST_INTERVAL = datetime.timedelta(seconds=5)

def lat_lng(city: str) -> Tuple[float, float]:
    geolocator = Nominatim(user_agent="my_app")
    location = geolocator.geocode(city)
    if location is None:
        print(f"Failed to get location for {city}")
        return (0.0,0.0)
    return location.latitude, location.longitude

def make_url(lat: float, lng: float, page: int) -> str:
    return f"https://apiv4.updateparishdata.org/Churchs/?lat={lat}&long={lng}&pg={page}"

def request_id(city, page):
    return f"{city.replace(' ', '_').replace(',', '-')}_page{page}.json"

def check_disk(dir, city, page):
    
    return os.path.exists()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query updateparishdata to get church locations.")
    parser.add_argument("--output", help="Path to the data output directory")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run")
    args = parser.parse_args()

    last_request_time = datetime.datetime.now() - datetime.timedelta(minutes=10)

    for city in _WIKI_CITIES[::-1]:
        page = 1
        response_filename = os.path.join(args.output, request_id(city, page))
        if os.path.exists(response_filename):
            print(f"Skipping already done {city} {page}")
            continue

        lat, lng = lat_lng(city)
        if not lat or not lng:
            print(f"Failed to get lat/lng for {city}")
            continue
        
        
        while page:
            response_filename = os.path.join(args.output, request_id(city, page))
            if os.path.exists(response_filename):
                print(f"Skipping already done {city} {page}")
                page += 1
                # continue
                break
            
            wait_seconds = last_request_time - datetime.datetime.now() + _REQUEST_INTERVAL
            if wait_seconds.total_seconds() > 0:
                print(f"Waiting {wait_seconds.total_seconds()} seconds")
                time.sleep(wait_seconds.total_seconds())

            url = make_url(lat, lng, page)
            print(f"Requesting {city} {page}: {url}")
            last_request_time = datetime.datetime.now()

            if args.dry_run:
                print(f"DRY RUN skipping request to {url}")
                break
            
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to get request for {city} {page}")
                break
            data = response.json()
            if not data:
                print(f"Empty data for {city} {page}")
                page = 0
                break
            with open(response_filename, "w") as f:
                json.dump(data, f)
            
            page += 1
