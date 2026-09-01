// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Immutable, tamper-evident anchors for externally stored content fingerprints.
contract ContentRegistry {
    struct Record {
        uint256 timestamp;
        address submitter;
        string uri;
    }

    mapping(bytes32 => Record) private records;

    event ContentAnchored(bytes32 indexed contentHash, string uri, uint256 timestamp, address indexed submitter);

    function anchor(bytes32 contentHash, string calldata uri) external {
        require(records[contentHash].timestamp == 0, "Fingerprint already anchored");
        records[contentHash] = Record(block.timestamp, msg.sender, uri);
        emit ContentAnchored(contentHash, uri, block.timestamp, msg.sender);
    }

    function get(bytes32 contentHash) external view returns (Record memory) {
        return records[contentHash];
    }
}

