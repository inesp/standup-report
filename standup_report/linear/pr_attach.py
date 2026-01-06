from standup_report.date_utils import parse_str_to_date
from standup_report.dict_utils import safe_traverse
from standup_report.issue_type import IssueAttachment


def extract_pr_attachments(raw_issue: dict) -> list[IssueAttachment]:
    raw_attachments: list[dict] = safe_traverse(raw_issue, "attachments.nodes", [])
    return [
        IssueAttachment(
            url=pr["url"],
            title=pr["title"],
            last_updated=parse_str_to_date(pr["updatedAt"]),
        )
        for pr in raw_attachments
    ]
