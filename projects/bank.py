import pendulum

from jira.references import JiraSquadID
from projects.base import BaseProject

AVG_SPRINT_CAPACITY_LINK = ""
AVG_SPRINT_CAPACITY = 123

IS_REFINED_CUSTOM_FIELD_REF = "customfield_10350"


class BankBase(BaseProject):
    jira_squad_id = JiraSquadID.BANK

    def is_ticket_refined(self, ticket):
        # For some reason the "is refined" field for Bank squad returns a list
        refined_list = ticket["fields"][IS_REFINED_CUSTOM_FIELD_REF] or []
        if type(refined_list) != list:
            raise ValueError("Bank refined custom label is no longer a list, please update!")

        for refined_label in refined_list:
            if refined_label["value"].lower() == "yes":
                return True

        return False


class API2BankingMVP(BankBase):
    name = "API 2.0 Banking Release"
    sprint_commitment_groups = [{"sta"}]
    start_date = pendulum.parse("2021-08-09").to_date_string()
    initial_story_point_estimate = 200

    def check_ticket_is_part_of_project(self, ticket_info: dict) -> bool:
        project_component_name = "API v2.0 Banking release"

        component_name_list = []
        components = ticket_info["fields"]["components"]
        if components:
            component_name_list = [component["name"].lower() for component in components]

        if project_component_name.lower() in component_name_list:
            return True

        return False


class API2ConsumerMVP(BankBase):
    name = "API 2.0 Consumer Release"
    sprint_commitment_groups = [{"sta"}]
    start_date = pendulum.parse("2021-08-09").to_date_string()
    initial_story_point_estimate = 150

    def check_ticket_is_part_of_project(self, ticket_info: dict) -> bool:
        project_component_name = "API v2.0 Consumer release"

        component_name_list = []
        components = ticket_info["fields"]["components"]
        if components:
            component_name_list = [component["name"].lower() for component in components]

        if project_component_name.lower() in component_name_list:
            return True

        return False
