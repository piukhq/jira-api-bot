from enum import Enum


class JiraProjectID(int, Enum):
    BANK = 126
    BPL = 168
    MERCHANT = 172
    MOBILE = 201


SPREADSHEET_BASE_DIR = "spreadsheets"

PROJECT_SPREADSHEETS = {
    JiraProjectID.BANK: "bank.xlsx",
    JiraProjectID.BPL: "bpl.xlsx",
    JiraProjectID.MERCHANT: "merchant.xlsx",
    JiraProjectID.MOBILE: "mobile.xlsx",
}


class Worksheets(str, Enum):
    sprint = "sprint"
    backlog = "backlog"
    trusted_channels = "trusted_channels"
