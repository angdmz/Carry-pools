import sqlalchemy as sa

from enums import IdentificationType, AcademicType, ParticipantType

identification_type = sa.Enum(IdentificationType, name="enum_identification_type")
academic_type = sa.Enum(AcademicType, name="enum_academic_type")
participant_type = sa.Enum(ParticipantType, name="enum_participant_type")