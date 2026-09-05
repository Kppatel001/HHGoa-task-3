"""Blockchain service — registers & verifies evidence fingerprints on an
EVM chain via Web3.py.

Local Hardhat is the default target (chainId 31337). The same code works against
a public testnet by changing the RPC / chain id / key / explorer in .env.

The contract address + ABI are loaded from the deploy artifact written by the
Hardhat deploy script: contracts/deployments/<chainId>.json ({address, abi}).
CONTRACT_ADDRESS in .env overrides the address if set.

Security: the private key is read from the environment, never logged, and never
returned through the API.
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.hashing import to_bytes32

log = get_logger("faceproof.chain")

# backend/app/services/blockchain_service.py -> repo root is 3 levels up.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_DEPLOYMENTS_DIR = os.path.join(_REPO_ROOT, "contracts", "deployments")
# ABI fallback bundled with the backend (kept in sync by deploy script).
_ABI_FALLBACK = os.path.join(
    os.path.dirname(__file__), "..", "abi", "ContentVerification.json"
)
# Precompiled {abi, bytecode} for the in-process (memory) chain — no solc/node needed.
_COMPILED = os.path.join(
    os.path.dirname(__file__), "..", "abi", "ContentVerification.compiled.json"
)


@dataclass
class ChainRecord:
    record_id: int
    fingerprint: str        # hex, no 0x
    content_id: str         # hex, no 0x
    timestamp: int
    submitter: str
    platform: str
    source_url_hash: str    # hex, no 0x


@dataclass
class RegisterResult:
    success: bool
    record_id: Optional[int]
    transaction_hash: Optional[str]
    block_number: Optional[int]
    fingerprint: str
    timestamp: Optional[int]
    gas_used: Optional[int]
    error: Optional[str] = None


class BlockchainService:
    _instance: "BlockchainService | None" = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._w3 = None
        self._contract = None
        self._account = None
        self._address: Optional[str] = None
        self._error: Optional[str] = None
        self._memory = False
        self._init_lock = threading.Lock()

    @classmethod
    def instance(cls) -> "BlockchainService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = BlockchainService()
        return cls._instance

    # ---- setup ----
    def _load_deployment(self) -> tuple[str, list]:
        deployments_dir = settings.deployments_dir or _DEPLOYMENTS_DIR
        deploy_path = os.path.join(deployments_dir, f"{settings.blockchain_chain_id}.json")
        address = settings.contract_address or None
        abi = None
        if os.path.exists(deploy_path):
            with open(deploy_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            address = address or data.get("address")
            abi = data.get("abi")
        if abi is None and os.path.exists(_ABI_FALLBACK):
            with open(_ABI_FALLBACK, "r", encoding="utf-8") as fh:
                abi = json.load(fh)
        if not address:
            raise RuntimeError(
                f"No contract address. Deploy the contract first "
                f"(expected {deploy_path}) or set CONTRACT_ADDRESS in .env."
            )
        if abi is None:
            raise RuntimeError("Contract ABI not found. Deploy the contract first.")
        return address, abi

    def _load_compiled(self) -> tuple[list, str]:
        with open(_COMPILED, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data["abi"], data["bytecode"]

    def _setup_memory(self):
        """Deploy the contract to a real EVM running in-process (eth-tester).
        No external node, private key, or Node.js required."""
        from web3 import Web3, EthereumTesterProvider

        w3 = Web3(EthereumTesterProvider())
        w3.eth.default_account = w3.eth.accounts[0]
        abi, bytecode = self._load_compiled()
        factory = w3.eth.contract(abi=abi, bytecode=bytecode)
        receipt = w3.eth.wait_for_transaction_receipt(factory.constructor().transact())
        contract = w3.eth.contract(address=receipt.contractAddress, abi=abi)
        self._w3, self._contract, self._address = w3, contract, receipt.contractAddress
        self._account = None  # tester accounts are unlocked; no manual signing
        self._memory = True
        self._error = None
        log.info("[CHAIN] in-process EVM ready contract=%s", receipt.contractAddress)

    def _setup_rpc(self):
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(settings.blockchain_rpc_url, request_kwargs={"timeout": 20}))
        if not w3.is_connected():
            raise RuntimeError(f"Cannot reach RPC at {settings.blockchain_rpc_url}")
        address, abi = self._load_deployment()
        account = None
        if settings.blockchain_private_key:
            account = w3.eth.account.from_key(settings.blockchain_private_key)
        contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
        self._w3, self._contract, self._account, self._address = (w3, contract, account, address)
        self._memory = False
        self._error = None
        log.info("[CHAIN] connected chain_id=%s contract=%s", settings.blockchain_chain_id, address)

    def _ensure(self):
        if self._contract is not None:
            return
        with self._init_lock:
            if self._contract is not None:
                return
            try:
                if settings.blockchain_mode.lower() == "memory":
                    self._setup_memory()
                else:
                    self._setup_rpc()
            except Exception as exc:  # noqa: BLE001
                self._error = str(exc)
                log.error("[CHAIN] init failed: %s", exc)
                raise

    # ---- status ----
    def status(self) -> dict[str, Any]:
        try:
            self._ensure()
            block = self._w3.eth.block_number
            return {
                "connected": True,
                "mode": "memory" if self._memory else "rpc",
                "chain_id": settings.blockchain_chain_id,
                "contract_address": self._address,
                "rpc_url": "in-process (eth-tester)" if self._memory else settings.blockchain_rpc_url,
                "latest_block": int(block),
                "wallet": self._account.address if self._account else (self._w3.eth.accounts[0] if self._memory else None),
                "explorer": settings.block_explorer_url or None,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "connected": False,
                "chain_id": settings.blockchain_chain_id,
                "rpc_url": settings.blockchain_rpc_url,
                "error": str(exc),
            }

    @property
    def ready(self) -> bool:
        try:
            self._ensure()
            return True
        except Exception:  # noqa: BLE001
            return False

    def explorer_tx_url(self, tx_hash: str) -> Optional[str]:
        base = settings.block_explorer_url.rstrip("/")
        return f"{base}/tx/{tx_hash}" if base else None

    # ---- write ----
    def register(
        self, *, fingerprint_hex: str, content_id_hex: str, platform: str, source_url: str
    ) -> RegisterResult:
        from web3 import Web3

        try:
            self._ensure()

            fp32 = to_bytes32(fingerprint_hex)
            cid32 = to_bytes32(content_id_hex)
            url_hash32 = Web3.keccak(text=source_url or "")
            fn = self._contract.functions.registerRecord(fp32, cid32, platform, url_hash32)

            log.info("[CHAIN] transaction submitted")
            if self._memory:
                # In-process EVM: the tester account is unlocked, submit directly.
                tx_hash = fn.transact({"from": self._w3.eth.accounts[0], "gas": 400000})
            else:
                if self._account is None:
                    raise RuntimeError("No signer configured (BLOCKCHAIN_PRIVATE_KEY unset).")
                tx = fn.build_transaction(
                    {
                        "from": self._account.address,
                        "nonce": self._w3.eth.get_transaction_count(self._account.address),
                        "chainId": settings.blockchain_chain_id,
                        "gas": 300000,
                        "gasPrice": self._w3.eth.gas_price,
                    }
                )
                signed = self._account.sign_transaction(tx)
                tx_hash = self._w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            # Extract recordId from the emitted event.
            record_id = None
            try:
                logs = self._contract.events.RecordRegistered().process_receipt(receipt)
                if logs:
                    record_id = int(logs[0]["args"]["recordId"])
            except Exception:  # noqa: BLE001
                pass

            log.info("[CHAIN] transaction confirmed block=%s record_id=%s", receipt.blockNumber, record_id)
            return RegisterResult(
                success=True,
                record_id=record_id,
                transaction_hash=tx_hash.hex(),
                block_number=int(receipt.blockNumber),
                fingerprint=fingerprint_hex,
                timestamp=int(time.time()),
                gas_used=int(receipt.gasUsed),
            )
        except Exception as exc:  # noqa: BLE001
            log.error("[CHAIN] registration failed: %s", exc)
            return RegisterResult(
                success=False,
                record_id=None,
                transaction_hash=None,
                block_number=None,
                fingerprint=fingerprint_hex,
                timestamp=None,
                gas_used=None,
                error=str(exc),
            )

    # ---- read ----
    def get_record(self, record_id: int) -> ChainRecord:
        self._ensure()
        r = self._contract.functions.getRecord(record_id).call()
        # (fingerprint, contentId, timestamp, submitter, platform, sourceUrlHash)
        return ChainRecord(
            record_id=record_id,
            fingerprint=r[0].hex(),
            content_id=r[1].hex(),
            timestamp=int(r[2]),
            submitter=r[3],
            platform=r[4],
            source_url_hash=r[5].hex(),
        )

    def verify_onchain(self, record_id: int, fingerprint_hex: str) -> bool:
        """Ask the contract itself whether a fingerprint matches a record."""
        self._ensure()
        return bool(
            self._contract.functions.verifyRecord(record_id, to_bytes32(fingerprint_hex)).call()
        )


def get_blockchain_service() -> BlockchainService:
    return BlockchainService.instance()
