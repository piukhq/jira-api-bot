from jira.references import JiraSquadID
from projects.base import BaseProject


class BPLBase(BaseProject):
    jira_squad_id = JiraSquadID.BPL

    def is_ticket_refined(self, ticket: dict):
        ready_for_refinement_sprint = "bpl - ready for refinement '22"
        ticket_sprints = ticket["fields"]["sprint"] or []

        if not ticket_sprints:
            return False

        for sprint in ticket_sprints:
            if sprint["name"].lower() == ready_for_refinement_sprint:
                return False

        return True
