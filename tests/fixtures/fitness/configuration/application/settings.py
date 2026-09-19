from os import environ


def setting() -> str:
    return environ["ALIENINTENT_EXAMPLE"]
