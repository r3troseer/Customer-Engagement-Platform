"""
Token economy models — owned by Omar (FR8).
Tables: wallets, wallet_transactions, token_rules, reward_rules,
        rewards_catalog, reward_vouchers
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    ApplicableToEnum,
    RewardTypeEnum,
    TokenRuleTypeEnum,
    TransactionDirEnum,
    TransactionTypeEnum,
    VoucherStatusEnum,
    WalletStatusEnum,
    WalletTypeEnum,
)


class Wallet(Base, TimestampMixin):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    wallet_type: Mapped[str] = mapped_column(WalletTypeEnum, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(WalletStatusEnum, nullable=False, default="active")
    # Seed: employee wallet (user 3, 100.00), customer wallet (user 4, 50.00)


class WalletTransaction(Base, TimestampMixin):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    wallet_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(TransactionTypeEnum, nullable=False)
    direction: Mapped[str] = mapped_column(TransactionDirEnum, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    token_rule_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("token_rules.id", ondelete="SET NULL"), nullable=True)
    reward_rule_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("reward_rules.id", ondelete="SET NULL"), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reversal_transaction_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("wallet_transactions.id", ondelete="SET NULL"), nullable=True)


class TokenRule(Base, TimestampMixin):
    __tablename__ = "token_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_type: Mapped[str] = mapped_column(TokenRuleTypeEnum, nullable=False)
    condition_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tokens_awarded: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class RewardRule(Base, TimestampMixin):
    __tablename__ = "reward_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    minimum_tokens_required: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    applicable_to: Mapped[str] = mapped_column(ApplicableToEnum, nullable=False)
    conditions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class RewardsCatalog(Base, TimestampMixin):
    __tablename__ = "rewards_catalog"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reward_type: Mapped[str] = mapped_column(RewardTypeEnum, nullable=False)
    token_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    monetary_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    applicable_to: Mapped[str] = mapped_column(ApplicableToEnum, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity_available: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # active | inactive | expired
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class RewardVoucher(Base, TimestampMixin):
    __tablename__ = "reward_vouchers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reward_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rewards_catalog.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    voucher_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(VoucherStatusEnum, nullable=False, default="issued")
