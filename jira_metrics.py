import shutil

import click

from db.cache import CacheIDs, is_cache_outdated, update_cache
from excel import write_data_to_spreadsheet
from jira.backlog import catagorise_backlog_tickets, fetch_backlog_tickets
from jira.references import JiraSquadID
from jira.sprint import catagorise_sprint_tickets, fetch_sprints_and_sprint_tickets
from jira_enums import PROJECT_SPREADSHEETS, SPREADSHEET_BASE_DIR, JiraProjectID, Worksheets
from projects import setup_projects_in_db
from projects.custom_projects.trusted_channel import fetch_trusted_channel_information


@click.command()
def fetch_all_data():
    try:
        shutil.rmtree(SPREADSHEET_BASE_DIR)
    except FileNotFoundError:
        pass

    if is_cache_outdated(CacheIDs.SPRINT_REPORT):
        print("Cache outdated... re-fetching data from Jira...")
        setup_projects_in_db()
        for project in JiraSquadID:
            print(f"fetching {project} sprint info...")
            fetch_sprints_and_sprint_tickets(project)
            print(f"fetching {project} backlog info...")
            fetch_backlog_tickets(project)

        print("Refreshing cache update date...")
        update_cache(CacheIDs.SPRINT_REPORT)

    print("Starting ticket organisation...")
    for project in JiraSquadID:
        print(f"Organising {project} sprint info...")
        squad_data = catagorise_sprint_tickets(project)
        print("Data organised, writing to excel file...")
        write_data_to_spreadsheet(squad_data, PROJECT_SPREADSHEETS[project], Worksheets.sprint)
        print("Completed!")

        print(f"Organising {project} backlog info...")
        backlog_data = catagorise_backlog_tickets(project)
        print("Data organised, writing to excel file...")
        write_data_to_spreadsheet(backlog_data, PROJECT_SPREADSHEETS[project], Worksheets.backlog)
        print("Completed!")

    # Custom work
    print("Starting custom scripts")
    trusted_channel_data = fetch_trusted_channel_information()
    write_data_to_spreadsheet(
        trusted_channel_data, PROJECT_SPREADSHEETS[JiraProjectID.BANK], Worksheets.trusted_channels
    )


if __name__ == "__main__":
    fetch_all_data()
