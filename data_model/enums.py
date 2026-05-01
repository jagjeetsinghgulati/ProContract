from enum import Enum


class ClauseCategory(str, Enum):
    COMMERCIAL = "Commercial"
    LEGAL = "Legal"
    OBLIGATORY = "Obligatory"
    CRITICAL = "Critical"
    INCONSEQUENTIAL = "Inconsequential"
    MALICIOUS = "Malicious"
    UNNECESSARY = "Unnecessary"
    OTHER = "Other"


class CriticalityLevel(int, Enum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5


class Negotiability(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class FavorabilityTarget(str, Enum):
    PARTY_1 = "Party1"
    PARTY_2 = "Party2"
    PARTY_3 = "Party3"
    NEUTRAL = "Neutral"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    SEVERE = "Severe"


class ModificationMode(str, Enum):
    BALANCED = "Balanced"
    FAVOR_PARTY = "FavorParty"
    AGGRESSIVE = "Aggressive"


class DocumentType(str, Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    TXT = "TXT"
