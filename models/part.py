from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)

from core.database import Base


class Part(Base):
    __tablename__ = "parts"
    __table_args__ = (
        UniqueConstraint("user_id", "part", name="uq_user_part"),
        Index(
            "uq_default_part",
            "part",
            unique=True,
            postgresql_where=text("user_id IS NULL"),
            sqlite_where=text("user_id IS NULL"),
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String,
        ForeignKey("accounts.user_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    part = Column(String, nullable=False)
    km_life = Column(Integer, nullable=False)
    month_life = Column(Integer, nullable=False)
    km_limit = Column(Integer, nullable=False)
    day_limit = Column(Integer, nullable=False)

    @property
    def is_default(self) -> bool:
        return self.user_id is None
