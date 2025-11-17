"""Database models for conversation persistence."""
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import TypeDecorator, DateTime as SA_DateTime
from datetime import datetime, timezone
from pathlib import Path

# Database setup
DB_PATH = Path(__file__).parent.parent / 'data-sources' / 'conversations.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Use URI format with explicit mode to ensure writability
DATABASE_URL = f"sqlite:///{DB_PATH}?mode=rwc"
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False, "uri": True},
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TZDateTime(TypeDecorator):
    """DateTime type that ensures all timestamps are UTC-aware."""
    impl = SA_DateTime
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """Called when saving to DB - normalize to UTC-aware."""
        if value is None:
            return None
        if isinstance(value, str):
            # Try to parse ISO string
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value
    
    def process_result_value(self, value, dialect):
        """Called when loading from DB - normalize to UTC-aware."""
        if value is None:
            return None
        if isinstance(value, str):
            # SQLite might hand this back as string if stored that way
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


class Conversation(Base):
    """Conversation model - represents a chat session."""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(TZDateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(TZDateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model - individual messages within a conversation."""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(TZDateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    sources = Column(Text, nullable=True)  # JSON string of sources
    
    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database on import
init_db()
