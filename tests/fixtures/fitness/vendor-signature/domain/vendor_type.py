from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from github import Github


def accepts_vendor(client: Github) -> Github:
    return client
