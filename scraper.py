import logging
from pathlib import Path, PosixPath
import re
import requests
import shutil

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)


def get_talks_metadata(year: int, month: str) -> list[dict]:
    """
    Get the talk urls from the main conference landing page for year and month

    :param year: year of conference
    :param month: month of conference
    :return: list or urls
    """
    # First get the overall conference meta data for the conference
    conference_url = f"https://site.churchofjesuschrist.org/study/general-conference/{year}/{month}?lang=eng"
    conference_page = requests.get(conference_url)
    conference_soup = BeautifulSoup(conference_page.content, "html.parser")

    # List of all talks in the conference
    list_of_talks_metadata = list()

    # Loop through all sessions and grab metadata talk
    list_of_all_sessions = conference_soup.find(class_="doc-map").find_all("ul")
    for session in list_of_all_sessions:
        for talk in session.find_all("li"):
            # On the site, this class determines if its a talk and not a session header
            if talk.find_all(class_="primaryMeta"):
                talk_metadata = dict()
                talk_metadata['speaker'] = talk.find("p", class_="primaryMeta").text
                talk_metadata['title'] = talk.find("p", class_="title").text
                talk_metadata['talk_url'] = talk.a['href']
                list_of_talks_metadata.append(talk_metadata)

    return list_of_talks_metadata


def get_talk_text(talk_url: str, file: PosixPath = None) -> str:
    """
    Get the talk text for a given talk url.

    :param talk_url: url for conference talk
    :param file: if given, saves to file location defined; otherwise to save.
    :return: text of the given talk in string form
    """

    logging.info(f"Getting text from: {talk_url}")

    # Get the soup
    page = requests.get(talk_url)
    talk_soup = BeautifulSoup(page.content, "html.parser")

    # Get talk text
    talk_text = talk_soup.find(class_='body-block').text

    # Save to file if passed in
    if file:
        with open(file, "w") as text_file:
            text_file.write(talk_text)

    return talk_text


def create_output_file_name(current_conference_directory: PosixPath,
                            talk_metadata: dict,
                            year: int,
                            month: str) -> PosixPath:
    """
    Create a clean talk file name that can be easily parsed later.

    :param current_conference_directory: directory where talks are being stored for the current conferenece.
    :param talk_metadata: dictionary of talk metadata.
    :param year: year of the conference.
    :param month: month of the conference
    :return: file name to save talk text to
    """

    # Remove punctuation and standardize for speaker
    clean_speaker = (talk_metadata['speaker']
                     .replace(' ', '-')
                     .replace('.', '')
                     .replace(',', '')
                     .lower())
    # Remove punctuation and standardize for talk title
    clean_talk_title = (talk_metadata['title']
                        .replace(' ', '-')
                        .lower())
    clean_talk_title = re.sub(r'[^\w\s-]', '', clean_talk_title)

    return Path(current_conference_directory, f"{year}_{month}_{clean_speaker}_{clean_talk_title}.txt")


if __name__ == "__main__":

    # Name of main directory to store all data
    CONFERENCES_DIRECTORY = "conference_talks"

    # Create directory for storage if it doesn't exist
    Path(CONFERENCES_DIRECTORY).mkdir(parents=True, exist_ok=True)

    # Loop through conference years
    for year in range(2020, 2000, -1):
        # Loop through April and October sessions
        for month in ['10', '04']:
            try:
                logging.info(f"Getting data for {year}-{month}")

                # If current conference directory doesn't exist yet
                if not Path(CONFERENCES_DIRECTORY, f"{year}_{month}").exists():

                    # Create specific conference directory
                    current_conference_directory = Path(CONFERENCES_DIRECTORY, f"{year}_{month}")
                    Path(current_conference_directory).mkdir(parents=True, exist_ok=True)

                    # Get talk urls for the specified conference
                    talks_metadata = get_talks_metadata(year, month)

                    # Look through each talk link. Keep track of counts
                    for talk in talks_metadata:

                        # Prepend the full link to access the page
                        talk_url_full = f"https://site.churchofjesuschrist.org{talk['talk_url']}"

                        if "video" not in talk['title'].lower():
                            # Get talk text and save to file
                            talk_output_file = create_output_file_name(current_conference_directory, talk, year, month)
                            talk_text = get_talk_text(talk_url_full, file=talk_output_file)
                else:
                    logging.info(f"Already ran for conference {year}-{month}")

            except Exception as e:
                logging.info(f"Not able to get data for conference {year}-{month} "
                             f"because of the following error: {e}")

                # Remove current conference directory so later iterations will rerun when checking for directory
                shutil.rmtree(current_conference_directory)
