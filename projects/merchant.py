from jira.references import JiraSquadID
from projects.base import BaseProject


class MerchantBase(BaseProject):
    jira_squad_id = JiraSquadID.MERCHANT

    def is_ticket_refined(self, ticket: dict):
        ready_for_refinement_sprint = "mer ready for refinement"
        ticket_sprints = ticket["fields"]["sprint"] or []

        if not ticket_sprints:
            return False

        for sprint in ticket_sprints:
            if sprint["name"].lower() == ready_for_refinement_sprint:
                return False

        return True
