import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import requests


def find_text(entry, query: str) -> str:
    element = entry.find(query)
    if element:
        return element.text
    else:
        return ""


def get_arxiv_entries(
    time_period: str = "all", category: str = "cs.CL", max_results: int = 100
) -> list[dict]:
    # Base URL for arXiv API
    base_url = "http://export.arxiv.org/api/query"

    # Calculate the date for the past day or past week
    if time_period in ["pastday", "pastweek"]:
        query_date = (datetime.utcnow() - timedelta(days=7)).strftime(
            "%Y%m%d%H%M"
        )
    else:
        query_date = None

    # Form the search query
    search_query = f"cat:{category}"
    if query_date:
        search_query += f" AND submittedDate:[{query_date} TO {datetime.utcnow().strftime('%Y%m%d%H%M')}]"

    # Parameters for the API call
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
    }

    # Fetch data from the arXiv API
    response = requests.get(base_url, params=params)

    # Check if the response is successful
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch data from arXiv API: {response.status_code}"
        )

    # Parse the XML response
    root = ET.fromstring(response.content)

    now = datetime.utcnow()

    entries = []

    # Iterate through each entry in the feed
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = find_text(entry, "{http://www.w3.org/2005/Atom}title")
        link = find_text(entry, "{http://www.w3.org/2005/Atom}id")
        published = find_text(entry, "{http://www.w3.org/2005/Atom}published")
        summary = find_text(entry, "{http://www.w3.org/2005/Atom}summary")

        # Filter entries by date if time_period is "pastday"
        entry_date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
        if time_period == "pastday" and (now - entry_date).days > 1:
            continue

        # Extract authors and affiliations
        authors = []
        for author in entry.findall("{http://www.w3.org/2005/Atom}author"):
            name = find_text(author, "{http://www.w3.org/2005/Atom}name")
            affiliation_elem = author.find(
                "{http://arxiv.org/schemas/atom}affiliation"
            )
            affiliation = (
                affiliation_elem.text if affiliation_elem is not None else "N/A"
            )
            authors.append({"name": name, "affiliation": affiliation})

        entry_data = {
            "title": title,
            "link": link,
            "published": published,
            "summary": summary,
            "authors": authors,
        }
        entries.append(entry_data)

    return entries


def print_latest_arxiv_entries(
    time_period="all", category="cs.CL", max_results=100
):
    latest_entries = get_arxiv_entries(time_period, category, max_results)
    for entry in latest_entries:
        print(f"Title: {entry['title']}")
        print(f"Link: {entry['link']}")
        print(f"Published: {entry['published']}")
        print(f"Summary: {entry['summary']}")
        print("\n")


# # Retrieve the latest entries (options: "all", "pastday", "pastweek")
# time_period = "pastday"  # Change to "pastday" or "all" as needed
# latest_entries = get_arxiv_entries(time_period)

# # Process the entries as needed for your pipeline
# for entry in latest_entries:
#     print(f"Title: {entry['title']}")
#     print(f"Link: {entry['link']}")
#     print(f"Published: {entry['published']}")
#     print(f"Summary: {entry['summary']}")
#     print("\n")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        time_period = sys.argv[1]
    else:
        time_period = "pastday"

    print_latest_arxiv_entries(time_period=time_period, category="cs.CL")
