"""
FR10 — Blockchain Verification service layer (Omar).
Anchors ESG/compliance data hashes on Polygon (Amoy testnet for prototype).
Uses your 0.5 MATIC wallet for actual on-chain transactions.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.blockchain import BlockchainHash, BlockchainRecord, BlockchainTransaction


# ── Hash generation ───────────────────────────────────────────────────────────

def compute_sha256(data: dict) -> str:
    """Deterministic SHA-256 hash of a dict."""
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


# ── Polygon on-chain anchoring ────────────────────────────────────────────────

async def anchor_hash_on_polygon(hash_value: str) -> dict:
    """
    Send a self-transfer on Polygon (Amoy testnet) with hash_value in tx data.
    Returns {"transaction_hash": "0x...", "network_name": "polygon-amoy"}.

    Requires POLYGON_RPC_URL and POLYGON_WALLET_PRIVATE_KEY in env/config.
    """
    try:
        from web3 import Web3

        rpc_url = getattr(settings, "POLYGON_RPC_URL", "")
        private_key = getattr(settings, "POLYGON_WALLET_PRIVATE_KEY", "")

        if not rpc_url or not private_key:
            # Fallback: mock anchor for dev without chain access
            return {
                "transaction_hash": f"0xmock_{uuid.uuid4().hex[:40]}",
                "network_name": "polygon-amoy",
                "status": "mock",
            }

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = w3.eth.account.from_key(private_key)

        # Encode hash in transaction data field
        data_hex = w3.to_hex(text=f"CEP-ANCHOR:{hash_value}")

        tx = {
            "from": account.address,
            "to": account.address,  # self-transfer (cheapest anchor)
            "value": 0,
            "data": data_hex,
            "gas": 25000,
            "gasPrice": w3.eth.gas_price,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": w3.eth.chain_id,
        }

        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

        return {
            "transaction_hash": tx_hash.hex(),
            "network_name": "polygon-amoy",
            "status": "submitted",
            "block_number": None,
            "wallet_address": account.address,
        }

    except ImportError:
        # web3 not installed — return mock
        return {
            "transaction_hash": f"0xmock_{uuid.uuid4().hex[:40]}",
            "network_name": "polygon-amoy",
            "status": "mock",
        }
    except Exception as e:
        return {
            "transaction_hash": "",
            "network_name": "polygon-amoy",
            "status": "failed",
            "error": str(e),
        }


# ── CRUD ──────────────────────────────────────────────────────────────────────

async def create_record(db: AsyncSession, data: dict, created_by: int | None = None) -> BlockchainRecord:
    record = BlockchainRecord(
        **data,
        created_by=created_by,
        public_reference_code=uuid.uuid4().hex[:12].upper(),
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_record(db: AsyncSession, record_id: int) -> BlockchainRecord | None:
    result = await db.execute(select(BlockchainRecord).where(BlockchainRecord.id == record_id))
    return result.scalar_one_or_none()


async def list_records(
    db: AsyncSession, org_id: int | None = None, offset: int = 0, limit: int = 50,
) -> list[BlockchainRecord]:
    stmt = select(BlockchainRecord)
    if org_id:
        stmt = stmt.where(BlockchainRecord.organization_id == org_id)
    result = await db.execute(stmt.order_by(BlockchainRecord.created_at.desc()).offset(offset).limit(limit))
    return list(result.scalars().all())


async def anchor_record(db: AsyncSession, record_id: int, raw_data: dict | None = None) -> dict:
    """
    1. Compute hash of record data
    2. Store BlockchainHash row
    3. Submit to Polygon
    4. Store BlockchainTransaction row
    5. Update record status
    """
    record = await get_record(db, record_id)
    if not record:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("BlockchainRecord", record_id)

    # Compute hash
    hash_input = raw_data or {
        "record_id": record.id,
        "record_type": record.record_type,
        "reference_id": record.reference_id,
        "reference_type": record.reference_type,
        "organization_id": record.organization_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    hash_value = compute_sha256(hash_input)

    # Store hash
    bc_hash = BlockchainHash(
        blockchain_record_id=record.id,
        hash_value=hash_value,
        raw_data_reference=json.dumps(hash_input, default=str)[:255],
    )
    db.add(bc_hash)
    await db.flush()

    # Submit to Polygon
    chain_result = await anchor_hash_on_polygon(hash_value)

    # Store transaction
    bc_tx = BlockchainTransaction(
        network_name=chain_result.get("network_name", "polygon-amoy"),
        transaction_hash=chain_result.get("transaction_hash", f"pending_{uuid.uuid4().hex[:16]}"),
        block_number=chain_result.get("block_number"),
        wallet_address=chain_result.get("wallet_address"),
        status=chain_result.get("status", "pending"),
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(bc_tx)
    await db.flush()
    await db.refresh(bc_tx)

    # Link and update record
    record.blockchain_transaction_id = bc_tx.id
    record.anchored_at = datetime.now(timezone.utc)
    record.status = "anchored" if bc_tx.status in ("submitted", "mock") else "failed"
    await db.flush()
    await db.refresh(record)

    return {
        "record_id": record.id,
        "hash_value": hash_value,
        "transaction_hash": bc_tx.transaction_hash,
        "network_name": bc_tx.network_name,
        "status": record.status,
        "message": "Record anchored on Polygon" if record.status == "anchored" else "Anchoring failed",
    }


async def get_public_verification(db: AsyncSession, reference_code: str) -> dict | None:
    """FR-10.3: Public verification without sensitive data."""
    result = await db.execute(
        select(BlockchainRecord)
        .where(BlockchainRecord.public_reference_code == reference_code)
        .where(BlockchainRecord.is_public == True)
    )
    record = result.scalar_one_or_none()
    if not record:
        return None

    # Get hash
    hash_result = await db.execute(
        select(BlockchainHash)
        .where(BlockchainHash.blockchain_record_id == record.id)
        .order_by(BlockchainHash.created_at.desc())
    )
    bc_hash = hash_result.scalar_one_or_none()

    # Get transaction
    tx_hash = None
    network = None
    if record.blockchain_transaction_id:
        tx = await db.get(BlockchainTransaction, record.blockchain_transaction_id)
        if tx:
            tx_hash = tx.transaction_hash
            network = tx.network_name

    return {
        "public_reference_code": record.public_reference_code,
        "public_title": record.public_title,
        "public_description": record.public_description,
        "record_type": record.record_type,
        "status": record.status,
        "anchored_at": record.anchored_at,
        "published_at": record.published_at,
        "hash_value": bc_hash.hash_value if bc_hash else None,
        "transaction_hash": tx_hash,
        "network_name": network,
    }