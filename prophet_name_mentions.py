import csv
import logging
from pathlib import Path
import string

logging.basicConfig(level=logging.INFO)


def read_in_talk_text(talk_file: str) -> str:
    """
    Given a talk file, read in text.

    :param talk_file: path to talk text.
    :return: string of talk text.
    """

    if Path(talk_file).exists():
        logging.info(f"Talk exists, getting text from: {talk_file}")
        with open(talk_file, "r") as text_file:
            talk_text = text_file.read()
        return talk_text
    else:
        raise ValueError("file does not exist")


def get_prophet_occurence(talk_text: str, search_terms: list) -> int:
    """
    Given talk text and word, find the number of mentions. Currently deprecated.

    :param talk_text: text to count word in
    :param search_terms: list of possible search terms
    :return: the number of times the prophet was mentioned
    """

    # Remove punctuation and split text
    talk_text_cleaned = (talk_text
                         .translate(str.maketrans('', '', string.punctuation))
                         .lower())

    # Split into bigrams
    mentions = 0
    for i in zip(talk_text_cleaned.split(" ")[:-1], talk_text_cleaned.split(" ")[1:]):
        bigrams = " ".join(i)
        for s in search_terms:
            if s in bigrams:
                mentions += 1

    return mentions


def save_results_to_file(data: dict, file: str):
    """
    Save the results (in dictionary format) to a file.

    :param data: dictionary of the data we are saving
    :param file: name of file to save results to
    """

    # First check if file exits, if it does append row, if not write to a new file
    results_file_exists = Path(file)
    if results_file_exists.is_file():
        with open(file, "a") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=list(data.keys()))
            writer.writerow(data)
    else:
        with open(file, "w") as csv_file:
            # first write header
            csv_file.write(','.join(data.keys()) + "\n")
            writer = csv.DictWriter(csv_file, fieldnames=list(data.keys()))
            writer.writerow(data)


if __name__ == "__main__":

    # Global variables
    CONFERENCES_DIRECTORY = "conference_talks"
    PROPHET = "nelson"
    RESULTS_FILE = f"results_for_president_{PROPHET}.csv"

    # Loop through conference years prophet was current prophet
    for year in range(2023, 2017, -1):
        # Loop through April and October sessions
        for month in ['10', '04']:
            if (month == '10') & (year == '2023'):
                logging.info("skipping, conference hasn't happened yet")
            else:
                try:
                    # keep track of total number of talks for that conference (including audits, etc.)
                    total_talk_count = 0
                    # keep track of total number of eligible talks (talks that aren't given by prophet, audits, etc.
                    total_eligible_talk_count = 0
                    # keep track of prophet's name mentions
                    total_mentions = 0

                    for talk_file in Path(CONFERENCES_DIRECTORY, f"{year}_{month}").glob('*.txt'):
                        total_talk_count += 1

                        # Assumes file names have author and title info built in
                        talk_author = talk_file.name.split("_")[2]
                        talk_title = talk_file.name.split("_")[3]

                        if (PROPHET not in talk_author) & \
                                ("auditing" not in talk_title) & \
                                ("sustaining" not in talk_title):
                            # Read in talk text
                            talk_text = read_in_talk_text(talk_file)
                            total_eligible_talk_count += 1

                            if PROPHET.lower() in talk_text.lower():
                                total_mentions += 1

                    # Now save numbers to file
                    data_to_save = {"year": year,
                                    "month": month,
                                    "talk_count": total_talk_count,
                                    "talk_eligible_count": total_eligible_talk_count,
                                    "talks_with_mention_count": total_mentions,
                                    "ratio": total_mentions/total_eligible_talk_count}
                    save_results_to_file(data_to_save, RESULTS_FILE)

                except Exception as e:
                    logging.info(f"Not able to get data for conference {year}-{month} "
                                 f"because of the following error: {e}")


