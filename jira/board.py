import requests

from settings import JIRA_API_SECRET, JIRA_EMAIL


def fetch_board_tickets(jql: str) -> list:
    count = 0
    page_size = 50
    tickets = []
    while True:
        json = {"startAt": count, "maxResults": page_size, "validateQuery": "strict", "jql": jql}
        resp = requests.post(
            "https://hellobink.atlassian.net/rest/api/3/search", auth=(JIRA_EMAIL, JIRA_API_SECRET), json=json
        )

        ticket_response_data = resp.json()["issues"]
        tickets.extend(ticket_response_data)
        count += page_size

        if len(ticket_response_data) < page_size:
            break

    return tickets
