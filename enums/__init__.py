from enum import Enum


class ParticipantType(str, Enum):
    NATURAL_PERSON = "NATURAL_PERSON"
    GOVERNMENT_ORGANISM = "GOVERNMENT_ORGANISM"
    COMPANY = "COMPANY"
    ACADEMIC = "ACADEMIC"


class IdentificationType(str, Enum):
    DNI = "DNI"
    CUIT = "CUIT"
    LE = "LE"


class AcademicType(str, Enum):
    SCHOOL = "SCHOOL"
    HIGHSCHOOL = "HIGHSCHOOL"
    UNIVERSITY = "UNIVERSITY"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class AccountControllerStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    TO_REVERIFIED = "TO_REVERIFIED"
    REJECTED = "REJECTED"


class RechargeStatus(str, Enum):
    REJECTED = "REJECTED"
    SATISFIED = "SATISFIED"
    WAITING = "WAITING"


class CarryPoolStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "DRAFT"