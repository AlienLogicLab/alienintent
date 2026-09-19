from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from github import Github


def connect(client: "Github") -> "Github":
    return client
