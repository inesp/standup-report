class StandupReportError(Exception):
    """Base exception class for PR Analytics application"""


class SettingsError(StandupReportError):
    """Raised when configuration/settings are invalid"""


class RemoteException(StandupReportError):
    def __init__(
        self,
        msg: str,
        gql_errors: list[dict] | None = None,
        query: str | None = None,
        variables: dict | None = None,
        url: str | None = None,
    ):
        self.gql_errors = gql_errors
        self.query = query
        self.variables = variables
        self.url = url

        if gql_errors:
            msg = f"{msg}: {gql_errors}"

        super().__init__(msg)

    def user_error_desc(self) -> str:
        if self.gql_errors:
            return ", ".join([str(e) for e in self.gql_errors])
        return str(self)
