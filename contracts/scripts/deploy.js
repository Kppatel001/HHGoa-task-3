// Deploys ContentVerification and writes the address + ABI where the backend
// expects them:
//   contracts/deployments/<chainId>.json   ({ address, abi, network, ... })
//   backend/app/abi/ContentVerification.json  (ABI fallback for the backend)
//
// Usage:
//   npx hardhat run scripts/deploy.js --network localhost
//   npx hardhat run scripts/deploy.js --network sepolia
const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function waitForNode(ethers, retries = 30) {
  for (let i = 0; i < retries; i++) {
    try {
      await ethers.provider.getBlockNumber();
      return;
    } catch (e) {
      console.log(`Waiting for RPC node... (${i + 1}/${retries})`);
      await new Promise((r) => setTimeout(r, 2000));
    }
  }
  throw new Error("RPC node did not become ready in time");
}

async function main() {
  const { ethers, artifacts, network } = hre;

  await waitForNode(ethers);
  const [deployer] = await ethers.getSigners();
  const chainId = Number((await ethers.provider.getNetwork()).chainId);
  console.log(`Deploying ContentVerification to '${network.name}' (chainId ${chainId})`);
  console.log(`Deployer: ${deployer.address}`);

  const Factory = await ethers.getContractFactory("ContentVerification");
  const contract = await Factory.deploy();
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  console.log(`Deployed at: ${address}`);

  const artifact = await artifacts.readArtifact("ContentVerification");

  // 1) deployments/<chainId>.json  (consumed by the backend blockchain_service)
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  fs.mkdirSync(deploymentsDir, { recursive: true });
  const deployment = {
    contract: "ContentVerification",
    network: network.name,
    chainId,
    address,
    deployer: deployer.address,
    deployedAt: new Date().toISOString(),
    abi: artifact.abi,
  };
  const deployPath = path.join(deploymentsDir, `${chainId}.json`);
  fs.writeFileSync(deployPath, JSON.stringify(deployment, null, 2));
  console.log(`Wrote ${deployPath}`);

  // 2) backend ABI fallback
  const backendAbiDir = path.join(__dirname, "..", "..", "backend", "app", "abi");
  fs.mkdirSync(backendAbiDir, { recursive: true });
  const abiPath = path.join(backendAbiDir, "ContentVerification.json");
  fs.writeFileSync(abiPath, JSON.stringify(artifact.abi, null, 2));
  console.log(`Wrote ${abiPath}`);

  console.log("\nAdd this to backend/.env (or leave blank to auto-load the deployment file):");
  console.log(`CONTRACT_ADDRESS=${address}`);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
