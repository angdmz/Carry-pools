import sqlalchemy as sa

from enums import IdentificationType, AcademicType

identification_type = sa.Enum(IdentificationType, name="enum_identification_type")
academic_type = sa.Enum(AcademicType, name="enum_academic_type")

#     op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public')