const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("ContentVerification", function () {
  let contract, owner, other;

  const FP = ethers.keccak256(ethers.toUtf8Bytes("evidence-v1"));
  const CID = ethers.keccak256(ethers.toUtf8Bytes("https://example.com/post/1"));
  const URLH = ethers.keccak256(ethers.toUtf8Bytes("https://example.com/post/1"));
  const PLATFORM = "Public Web";

  beforeEach(async function () {
    [owner, other] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("ContentVerification");
    contract = await Factory.deploy();
    await contract.waitForDeployment();
  });

  it("registers a record and emits an event", async function () {
    await expect(contract.registerRecord(FP, CID, PLATFORM, URLH))
      .to.emit(contract, "RecordRegistered")
      .withArgs(1, FP, CID, owner.address, anyUint());
    expect(await contract.recordCount()).to.equal(1);
  });

  it("retrieves the stored record", async function () {
    await contract.registerRecord(FP, CID, PLATFORM, URLH);
    const r = await contract.getRecord(1);
    expect(r[0]).to.equal(FP);
    expect(r[1]).to.equal(CID);
    expect(r[3]).to.equal(owner.address);
    expect(r[4]).to.equal(PLATFORM);
  });

  it("verifies a matching fingerprint", async function () {
    await contract.registerRecord(FP, CID, PLATFORM, URLH);
    expect(await contract.verifyRecord(1, FP)).to.equal(true);
  });

  it("rejects a modified (tampered) fingerprint", async function () {
    await contract.registerRecord(FP, CID, PLATFORM, URLH);
    const tampered = ethers.keccak256(ethers.toUtf8Bytes("evidence-tampered"));
    expect(await contract.verifyRecord(1, tampered)).to.equal(false);
  });

  it("reverts on empty fingerprint", async function () {
    await expect(
      contract.registerRecord(ethers.ZeroHash, CID, PLATFORM, URLH)
    ).to.be.revertedWithCustomError(contract, "EmptyFingerprint");
  });

  it("reverts reading an unknown record", async function () {
    await expect(contract.getRecord(99)).to.be.revertedWithCustomError(
      contract,
      "UnknownRecord"
    );
  });

  it("maps fingerprint -> recordId", async function () {
    await contract.registerRecord(FP, CID, PLATFORM, URLH);
    expect(await contract.recordIdForFingerprint(FP)).to.equal(1);
    expect(await contract.recordIdForFingerprint(ethers.ZeroHash)).to.equal(0);
  });
});

// Helper matcher for the dynamic block timestamp.
function anyUint() {
  const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");
  return anyValue;
}
