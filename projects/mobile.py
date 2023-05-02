from jira.references import JiraSquadID
from projects.base import BaseProject


class MobileBase(BaseProject):
    jira_squad_id = JiraSquadID.MOBILE

    def is_ticket_refined(self, ticket):
        ready_for_refinement_sprint = "mobile - ready for refinement"
        ticket_sprints = ticket["fields"]["sprint"] or []

        if not ticket_sprints:
            return False

        for sprint in ticket_sprints:
            if sprint["name"].lower() == ready_for_refinement_sprint:
                return False

        return True
