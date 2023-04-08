from uuid import UUID

from exceptions import ResourceNotFound


class ParticipantNotFound(ResourceNotFound):
    def __init__(self, participant_id: UUID):
        super().__init__(f"Participant not found. ID: {participant_id}")
