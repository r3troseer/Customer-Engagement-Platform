"""
Blockchain verification models — owned by Omar (FR10).
Tables: blockchain_records, blockchain_hashes, blockchain_transactions
"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import BlockchainRecordTypeEnum, BlockchainStatusEnum, TxStatusEnum


class BlockchainTransaction(Base, TimestampMixin):
    __tablename__ = "blockchain_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    network_name: Mapped[str] = mapped_column(String(100), nullable=False)
    transaction_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    block_number: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    wallet_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(TxStatusEnum, nullable=False, default="pending")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class BlockchainRecord(Base, TimestampMixin):
    __tablename__ = "blockchain_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    record_type: Mapped[str] = mapped_column(BlockchainRecordTypeEnum, nullable=False)
    reference_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reference_type: Mapped[str] = mapped_column(String(100), nullable=False)
    blockchain_transaction_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("blockchain_transactions.id", ondelete="SET NULL"), nullable=True)
    anchored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(BlockchainStatusEnum, nullable=False, default="pending")
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # Absorbs public_verifications — FR-10.3 public verification without sensitive data
    public_reference_code: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    public_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    public_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    hashes: Mapped[list["BlockchainHash"]] = relationship("BlockchainHash", back_populates="record", lazy="selectin")


class BlockchainHash(Base, TimestampMixin):
    __tablename__ = "blockchain_hashes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    blockchain_record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("blockchain_records.id", ondelete="CASCADE"), nullable=False)
    hash_algorithm: Mapped[str] = mapped_column(String(50), default="SHA-256", nullable=False)
    hash_value: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    raw_data_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    record: Mapped["BlockchainRecord"] = relationship("BlockchainRecord", back_populates="hashes", lazy="selectin")
