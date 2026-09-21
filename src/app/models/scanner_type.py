from enum import Enum


class ScannerType(str, Enum):
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"