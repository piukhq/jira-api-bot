from db.session import Session
from jira.references import JiraSquadID
from models.ticket import Project
from projects.bank import API2BankingMVP, API2ConsumerMVP, BankBase
from projects.bpl import BPLBase
from projects.merchant import MerchantBase
from projects.mobile import MobileBase

PROJECT_LIST = {
    JiraSquadID.BANK: [
        API2BankingMVP(),
        API2ConsumerMVP(),
    ],
    JiraSquadID.BPL: [],
    JiraSquadID.MERCHANT: [],
    JiraSquadID.MOBILE: [],
}

SQUAD_BASE = {
    JiraSquadID.BANK: BankBase,
    JiraSquadID.BPL: BPLBase,
    JiraSquadID.MERCHANT: MerchantBase,
    JiraSquadID.MOBILE: MobileBase,
}


def setup_projects_in_db() -> None:
    projects_to_save = []
    for squad_id, project_list in PROJECT_LIST.items():
        for project in project_list:
            project_to_save = Project(jira_squad_id=squad_id, name=project.name)
            projects_to_save.append(project_to_save)

    with Session() as session:
        session.add_all(projects_to_save)
        session.commit()
