import sqlalchemy as sa

from enums import IdentificationType, AcademicType, AccountControllerStatus, ParticipantType, RechargeStatus

identification_type = sa.Enum(IdentificationType, name="enum_identification_type")
academic_type = sa.Enum(AcademicType, name="enum_academic_type")
account_controller_status = sa.Enum(AccountControllerStatus, name="enum_account_controller_status")
participant_type = sa.Enum(ParticipantType, name="enum_participant_type")
recharge_status = sa.Enum(RechargeStatus, name="enum_recharge_status_type")