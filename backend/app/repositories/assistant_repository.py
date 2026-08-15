import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.assistant_conversation import AssistantConversation, AssistantMessage
from app.models.assistant_feedback import AssistantFeedback, AssistantPreference


def get_or_create_active_conversation(db: Session, farmer_id: uuid.UUID) -> AssistantConversation:
    conversation = db.execute(
        select(AssistantConversation).where(AssistantConversation.farmer_id == farmer_id, AssistantConversation.is_archived.is_(False)).order_by(AssistantConversation.created_at.desc())
    ).scalars().first()
    if conversation is not None:
        return conversation
    conversation = AssistantConversation(farmer_id=farmer_id)
    db.add(conversation)
    db.flush()
    return conversation


def get_conversation_owned(db: Session, conversation_id: uuid.UUID, farmer_id: uuid.UUID) -> AssistantConversation | None:
    return db.execute(
        select(AssistantConversation).where(AssistantConversation.id == conversation_id, AssistantConversation.farmer_id == farmer_id).options(joinedload(AssistantConversation.messages))
    ).unique().scalar_one_or_none()


def create_message(db: Session, message: AssistantMessage) -> AssistantMessage:
    db.add(message)
    return message


def get_message_by_id(db: Session, message_id: uuid.UUID) -> AssistantMessage | None:
    return db.get(AssistantMessage, message_id)


def get_message_owned(db: Session, message_id: uuid.UUID, farmer_id: uuid.UUID) -> AssistantMessage | None:
    return db.execute(
        select(AssistantMessage).join(AssistantConversation, AssistantMessage.conversation_id == AssistantConversation.id).where(AssistantMessage.id == message_id, AssistantConversation.farmer_id == farmer_id)
    ).scalar_one_or_none()


def create_feedback(db: Session, feedback: AssistantFeedback) -> AssistantFeedback:
    db.add(feedback)
    return feedback


def get_preferences(db: Session, farmer_id: uuid.UUID) -> AssistantPreference | None:
    return db.execute(select(AssistantPreference).where(AssistantPreference.farmer_id == farmer_id)).scalar_one_or_none()


def create_preferences(db: Session, preferences: AssistantPreference) -> AssistantPreference:
    db.add(preferences)
    return preferences


def delete_conversation(db: Session, conversation: AssistantConversation) -> None:
    """Farmer-initiated deletion of their own conversation history
    (Requirement 90). Mandatory transaction/audit records elsewhere in
    this app are never touched by this - only the assistant's own
    conversation/message rows."""
    from sqlalchemy import delete

    db.execute(delete(AssistantMessage).where(AssistantMessage.conversation_id == conversation.id))
    db.execute(delete(AssistantConversation).where(AssistantConversation.id == conversation.id))
