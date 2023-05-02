import pendulum

from jira_enums import Enum


class JiraSquadID(int, Enum):
    BANK = 126
    BPL = 168
    MERCHANT = 172
    MOBILE = 201


SQUAD_IDENTIFIERS = {
    JiraSquadID.BANK: [
        {
            "name": "API 2.0 Banking Release",
            "query_field": "components",
            "query_value": "API v2.0 Banking Release",
            "start_sprint": pendulum.parse("2001-01-20").to_date_string(),
            "project_capacity": 0.3,
        },
        {
            "name": "Data Warehouse",
            "query_field": "components",
            "query_value": "Data Warehouse",
            "start_sprint": pendulum.parse("2001-01-20").to_date_string(),
            "project_capacity": 0.3,
        },
    ],
    JiraSquadID.BPL: [],
    JiraSquadID.MERCHANT: [],
    JiraSquadID.MOBILE: [],
}


TECHNICAL_TICKET_LABEL_LIST = ["technical", "security", "secops", "devops", "msm"]


class SprintStatus(str, Enum):
    CLOSED = "closed"
    FUTURE = "future"
    ACTIVE = "active"


# CHECK ME
STORY_POINT_JIRA_FIELD = "customfield_10117"
SPRINT_JIRA_FIELD = "customfield_10115"
LOY_STORY_POINT_JIRA_FIELD = "customfield_10347"
