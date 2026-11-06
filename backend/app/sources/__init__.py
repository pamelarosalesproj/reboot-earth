"""Fuentes externas distintas de MapBiomas (feature 003): INPE y SINAFLOR."""


class SourceUnavailable(Exception):
    """La fuente no respondió o respondió algo no interpretable."""
