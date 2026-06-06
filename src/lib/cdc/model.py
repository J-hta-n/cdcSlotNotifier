from dataclasses import dataclass
from typing import TypedDict


CDC_COURSE_LABELS = {
    "INDUCTION-PROGRAMME": "induction programme",
    "EV-ELITETEAM": "practical",
}


def format_course_label(course_code: str) -> str:
    """Convert CDC course code into a user-friendly label."""
    code = (course_code or "").strip().upper()
    if code in CDC_COURSE_LABELS:
        return CDC_COURSE_LABELS[code]
    if not code:
        return ""
    return code.replace("-", " ").lower()


CDCGetHeaders = TypedDict(
    "CDCGetHeaders",
    {
        "User-Agent": str,
        "Accept": str,
        "Accept-Language": str,
        "Referer": str,
    },
)


CDCPostHeaders = TypedDict(
    "CDCPostHeaders",
    {
        "User-Agent": str,
        "Accept": str,
        "Accept-Encoding": str,
        "Accept-Language": str,
        "Content-Type": str,
        "Origin": str,
        "Referer": str,
        "X-MicrosoftAjax": str,
    },
)


CDCPostPayload = TypedDict(
    "CDCPostPayload",
    {
        "ctl00$ContentPlaceHolder1$ScriptManager1": str,
        "ctl00_Menu1_TreeView1_ExpandState": str,
        "ctl00_Menu1_TreeView1_SelectedNode": str,
        "__EVENTTARGET": str,
        "__EVENTARGUMENT": str,
        "ctl00_Menu1_TreeView1_PopulateLog": str,
        "__LASTFOCUS": str,
        "__VIEWSTATE": str,
        "__VIEWSTATEGENERATOR": str,
        "__PREVIOUSPAGE": str,
        "__EVENTVALIDATION": str,
        "ctl00$ContentPlaceHolder1$txtVerificationCode": str,
        "ctl00$ContentPlaceHolder1$ddlCourse": str,
        "ctl00$ContentPlaceHolder1$hdReserveCnt": str,
        "ctl00$ContentPlaceHolder1$hdTicketEndDate": str,
        "ctl00$ContentPlaceHolder1$hdM1": str,
        "ctl00$ContentPlaceHolder1$hdM2": str,
        "ctl00$ContentPlaceHolder1$hdM3": str,
        "ctl00$ContentPlaceHolder1$hdCacheBackNav": str,
        "ctl00$ContentPlaceHolder1$hdCacheForNav": str,
        "ctl00$ContentPlaceHolder1$hdType": str,
        "ctl00$ContentPlaceHolder1$hdDate": str,
        "ctl00$ContentPlaceHolder1$hdSession": str,
        "ctl00$ContentPlaceHolder1$hdDays": str,
    },
    total=False,
)


@dataclass(frozen=True)
class CDCSlot:
    session_date: str
    day: str
    session_number: int
    time_range: str
    status: str
    image_name: str

    @property
    def is_available(self) -> bool:
        return self.status == "available"
