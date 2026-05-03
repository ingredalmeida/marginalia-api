"""Report export query parameters."""

from enum import Enum


class ReportFormat(str, Enum):
    csv = "csv"
    pdf = "pdf"
