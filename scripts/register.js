require("dotenv").config();
const { ethers } = require("ethers");
const artifact = require("../artifacts/contracts/ContentRegistry.sol/ContentRegistry.json");

async function main() {
  const [contentHash, uri = ""] = process.argv.slice(2);
  if (!contentHash || !process.env.REGISTRY_ADDRESS || !process.env.RPC_URL || !process.env.DEPLOYER_PRIVATE_KEY) {
    throw new Error("Usage: npm run register -- <0xSHA256> <uri>; set REGISTRY_ADDRESS, RPC_URL, DEPLOYER_PRIVATE_KEY");
  }
  const signer = new ethers.Wallet(process.env.DEPLOYER_PRIVATE_KEY, new ethers.JsonRpcProvider(process.env.RPC_URL));
  const registry = new ethers.Contract(process.env.REGISTRY_ADDRESS, artifact.abi, signer);
  const tx = await registry.anchor(contentHash, uri);
  const receipt = await tx.wait();
  console.log(JSON.stringify({ txHash: receipt.hash, blockNumber: receipt.blockNumber, contentHash, uri }));
}

main().catch((error) => { console.error(error.message || error); process.exitCode = 1; });

