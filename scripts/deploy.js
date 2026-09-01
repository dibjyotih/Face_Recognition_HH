const hre = require("hardhat");

async function main() {
  const Registry = await hre.ethers.getContractFactory("ContentRegistry");
  const registry = await Registry.deploy();
  await registry.waitForDeployment();
  console.log(JSON.stringify({ contractAddress: await registry.getAddress(), network: hre.network.name }));
}

main().catch((error) => { console.error(error); process.exitCode = 1; });

