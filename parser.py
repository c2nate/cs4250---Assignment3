#-------------------------------------------------------------------
# Nathaniel Dale
# parser.py
# parses through crawled cpp website content stored in mongoDB
# cs4250 - Assignment #3 Q6
#-------------------------------------------------------------------

from bs4 import BeautifulSoup
from pymongo import MongoClient, errors
import re
import logging


# logging for error tracking and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# connect to the MongoDB client
try:
    db_client = MongoClient("mongodb://localhost:27017/")
    logger.info("Connected to MongoDB successfully.")
except errors.ConnectionFailure as e:
    logger.error(f"MongoDB connection failed: {e}")
    exit(1)

university_db = db_client.cs_crawler
htmlPages = university_db.pages  # collection for storing HTML content of pages
facultyCollection = university_db.professors  # collection to store extracted faculty details


# function to parse and extract details of faculty members from HTML
def parseFacultyDetails(html_content):
    try:
        # create a BeautifulSoup object to parse the HTML
        parsed_html = BeautifulSoup(html_content, 'html.parser')

        faculty_list = []  # List to hold extracted faculty data

        # find all div elements with the class 'clearfix', which contain faculty information
        faculty_divs = parsed_html.find_all('div', class_='clearfix')

        if not faculty_divs:
            logger.warning("No faculty members found on the page.")

        for faculty in faculty_divs:
            # extract faculty name from the <h2> tag
            name_element = faculty.find('h2')
            faculty_name = name_element.get_text(strip=True) if name_element else 'Unknown'

            # default values for missing information
            position, office_location, contact_number, email_address, personal_site = 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown'

            # look for a <p> tag that may contain additional information
            info_element = faculty.find('p')

            if info_element:
                # search for specific data labels such as Title, Office, Phone, Email, Website
                title_label = info_element.find(string=re.compile(r"Title"))
                office_label = info_element.find(string=re.compile(r"Office"))
                phone_label = info_element.find(string=re.compile(r"Phone"))
                email_label = info_element.find(string=re.compile(r"Email"))
                website_label = info_element.find(string=re.compile(r"Web"))

                # extract corresponding values if the labels are found
                if title_label:
                    position = title_label.find_next('br').previous_sibling.strip() if title_label.find_next('br') else 'Unknown'
                if office_label:
                    office_location = office_label.find_next('br').previous_sibling.strip() if office_label.find_next('br') else 'Unknown'
                if phone_label:
                    contact_number = phone_label.find_next('br').previous_sibling.strip() if phone_label.find_next('br') else 'Unknown'
                if email_label:
                    email_link = email_label.find_next('a', href=re.compile(r"^mailto:"))
                    email_address = email_link.get_text(strip=True) if email_link else 'Unknown'
                if website_label:
                    website_link = website_label.find_next('a', href=re.compile(r"^http"))
                    personal_site = website_link['href'] if website_link else 'Unknown'

            # store the extracted information for each faculty member
            faculty_info = {
                'name': faculty_name,
                'position': position,
                'office_location': office_location,
                'contact_number': contact_number,
                'email_address': email_address,
                'personal_site': personal_site,
            }

            faculty_list.append(faculty_info)

        return faculty_list

    except Exception as e:
        logger.error(f"Error while parsing faculty details: {e}")
        return []


# function to save extracted faculty details into MongoDB and print the results
def saveFacultyDetails(faculty_details):
    if not faculty_details:
        logger.warning("No faculty details to save.")
        return

    try:
        # insert the faculty data into MongoDB
        for faculty in faculty_details:
            facultyCollection.insert_one(faculty)
        
        # log the number of professors added
        logger.info(f"Successfully saved {len(faculty_details)} faculty members.")

        # print the data of all inserted professors
        logger.info("Details of all the added professors:")
        for faculty in faculty_details:
            print(f"Name: {faculty['name']}")
            print(f"Position: {faculty['position']}")
            print(f"Office Location: {faculty['office_location']}")
            print(f"Contact Number: {faculty['contact_number']}")
            print(f"Email Address: {faculty['email_address']}")
            print(f"Personal Website: {faculty['personal_site']}")
            print("-" * 40)  # separator for clarity
        
    except errors.PyMongoError as e:
        logger.error(f"Error while saving data to MongoDB: {e}")


# function to fetch and process the faculty page HTML
def fetchFacultyPageData():
    page_url = "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"

    try:
        # retrieve the stored HTML content of the faculty page from the pages collection
        page_data = htmlPages.find_one({"url": page_url})

        if not page_data:
            logger.error("Target page not found in the database.")
            return

        # debugging: print the fetched page data for verification
        logger.info(f"Fetched Page Data: {page_data.get('url')}")

        # check if the page content exists
        if 'html' in page_data:
            page_html = page_data['html']
            faculty_details = parseFacultyDetails(page_html)  # extract faculty data
            saveFacultyDetails(faculty_details)  # save the extracted data
            logger.info(f"Successfully extracted and saved data for {len(faculty_details)} faculty members.")
        else:
            logger.error("Error: 'html' field missing in the page data.")

    except Exception as e:
        logger.error(f"Error fetching faculty page data: {e}")


if __name__ == "__main__":
    fetchFacultyPageData()
