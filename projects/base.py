from jira.references import JiraSquadID


class BaseProject:
    name: str
    jira_squad_id: JiraSquadID
    sprint_commitment_groups: list
    start_date: str
    initial_story_point_estimate: int

    def __str__(self):
        return self.name

    def check_ticket_is_part_of_project(self, ticket_info: dict) -> bool:
        raise NotImplementedError
