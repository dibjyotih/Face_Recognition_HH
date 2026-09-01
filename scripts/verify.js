require("dotenv").config();
const { ethers } = require("ethers");
const artifact = require("../artifacts/contracts/ContentRegistry.sol/ContentRegistry.json");

async function main() {
  const [contentHash] = process.argv.slice(2);
  if (!contentHash || !process.env.REGISTRY_ADDRESS || !process.env.RPC_URL) {
    throw new Error("Usage: npm run verify-content -- <0xSHA256>; set REGISTRY_ADDRESS and RPC_URL");
  }
  const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
  const registry = new ethers.Contract(process.env.REGISTRY_ADDRESS, artifact.abi, provider);
  const record = await registry.get(contentHash);
  const found = record.timestamp !== 0n;
  console.log(JSON.stringify({ found, contentHash, timestamp: record.timestamp.toString(), submitter: record.submitter, uri: record.uri }));
}

main().catch((error) => { console.error(error.message || error); process.exitCode = 1; });

