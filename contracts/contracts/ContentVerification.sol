// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ContentVerification
/// @notice Registers cryptographic fingerprints (SHA-256) of discovered public
///         content so their integrity can later be independently verified.
/// @dev Stores ONLY the proof/fingerprint and minimal metadata — never a face
///      image, embedding, or other biometric/personal data.
contract ContentVerification {
    struct VerificationRecord {
        bytes32 fingerprint;    // SHA-256 of the canonical evidence
        bytes32 contentId;      // e.g. SHA-256 of the source URL / content id
        uint256 timestamp;      // block timestamp at registration
        address submitter;      // who registered it
        string platform;        // source platform label (public)
        bytes32 sourceUrlHash;  // keccak256 of the source URL (no raw URL stored)
    }

    // recordId (1-based) => record
    mapping(uint256 => VerificationRecord) private _records;
    // fingerprint => recordId (first registration wins)
    mapping(bytes32 => uint256) private _byFingerprint;

    uint256 public recordCount;

    event RecordRegistered(
        uint256 indexed recordId,
        bytes32 indexed fingerprint,
        bytes32 contentId,
        address indexed submitter,
        uint256 timestamp
    );

    error EmptyFingerprint();
    error UnknownRecord(uint256 recordId);

    /// @notice Register a new content fingerprint.
    /// @return recordId The 1-based id assigned to this record.
    function registerRecord(
        bytes32 fingerprint,
        bytes32 contentId,
        string calldata platform,
        bytes32 sourceUrlHash
    ) external returns (uint256 recordId) {
        if (fingerprint == bytes32(0)) revert EmptyFingerprint();

        recordCount += 1;
        recordId = recordCount;

        _records[recordId] = VerificationRecord({
            fingerprint: fingerprint,
            contentId: contentId,
            timestamp: block.timestamp,
            submitter: msg.sender,
            platform: platform,
            sourceUrlHash: sourceUrlHash
        });

        if (_byFingerprint[fingerprint] == 0) {
            _byFingerprint[fingerprint] = recordId;
        }

        emit RecordRegistered(recordId, fingerprint, contentId, msg.sender, block.timestamp);
    }

    /// @notice Read a stored record.
    function getRecord(uint256 recordId)
        external
        view
        returns (
            bytes32 fingerprint,
            bytes32 contentId,
            uint256 timestamp,
            address submitter,
            string memory platform,
            bytes32 sourceUrlHash
        )
    {
        if (recordId == 0 || recordId > recordCount) revert UnknownRecord(recordId);
        VerificationRecord storage r = _records[recordId];
        return (r.fingerprint, r.contentId, r.timestamp, r.submitter, r.platform, r.sourceUrlHash);
    }

    /// @notice Verify that a given fingerprint matches the stored record.
    /// @return True iff the record exists and its fingerprint equals `fingerprint`.
    function verifyRecord(uint256 recordId, bytes32 fingerprint) external view returns (bool) {
        if (recordId == 0 || recordId > recordCount) return false;
        return _records[recordId].fingerprint == fingerprint;
    }

    /// @notice Look up the first recordId registered for a fingerprint (0 if none).
    function recordIdForFingerprint(bytes32 fingerprint) external view returns (uint256) {
        return _byFingerprint[fingerprint];
    }
}
