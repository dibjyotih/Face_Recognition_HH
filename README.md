# Face -> Web -> Blockchain Verifier

CLI proof-of-concept for the HH Goa 2026 Task 3 pipeline:

```text
face scan -> face encoding -> live Google Lens reverse-image search
          -> face-confirm a returned post -> SHA-256 evidence fingerprint
          -> ContentRegistry anchor -> independent on-chain re-verification
```

The search is live. The code sends the provided image URL to Google Lens through SerpApi at runtime, takes returned `visual_matches`, filters for Instagram, Facebook, X/Twitter, and Reddit links, downloads candidate thumbnails, and only lists posts when their independently computed face-embedding distance is at or below the configured threshold. The operator chooses which returned post to anchor. No post URL or identity is embedded in the repository.

## Stack

- Python, OpenCV YuNet/SFace face detection and embeddings, SerpApi Google Lens, SHA-256
- Solidity `0.8.24`, Hardhat and ethers.js
- Polygon Amoy is supported. A local Hardhat network is the recommended recording fallback.

## Setup

Prerequisites: Node.js 18+ and Python 3.10+. The OpenCV Python wheel is prebuilt, so no C++ build environment is required. On first face scan, the script downloads small YuNet and SFace ONNX models from the OpenCV Zoo and caches them under `data/models`.

```powershell
npm install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
npm run compile
```

Fill `.env` with a [SerpApi key](https://serpapi.com/) and a public HTTPS image URL for a consented demo image. This URL must point to the same file used with `--image`, as Google Lens fetches it remotely.

## Local end-to-end demo

1. In terminal 1 start the local blockchain:

   ```powershell
   npm run node
   ```

2. Copy one displayed Hardhat account private key into `DEPLOYER_PRIVATE_KEY` in `.env`, leaving `RPC_URL=http://127.0.0.1:8545`. In terminal 2:

   ```powershell
   npm run deploy:local
   ```

3. Copy the returned `contractAddress` into `REGISTRY_ADDRESS` in `.env`, then run the pipeline:

   ```powershell
   python -m src.pipeline --image .\sample.jpg --source-url "https://public.example/sample.jpg" --uri "ipfs://optional-cid"
   ```

The command prints the detected face box, confirmed candidate distance and post URL, SHA-256 fingerprint, anchor transaction hash, and the re-read contract record. Evidence metadata is appended to `data/evidence.json` as a JSON array, preserving every run.

## Webcam scan and social-post selection

Set `IMGBB_API_KEY` in `.env` (a free imgbb.com API key). This is needed because Google Lens needs a public URL for a camera frame. With the Hardhat node running and the registry deployed, run:

```powershell
python -m src.pipeline --camera
```

A camera window opens. Press `SPACE` to capture or `Q` to cancel. The command uploads the captured image, searches Google Lens, prints face-confirmed Instagram/Facebook/X/Reddit candidates, and asks you to select one before anchoring it. Use `--camera-index 1` for another camera, `--select 1` for scripted selection, or `--include-web` to include normal web pages in the choices.

## Verify and tamper demo

Run the saved evidence through the exact canonical SHA-256 process again:

```powershell
python -m src.pipeline --image .\unused.jpg --source-url "https://unused.invalid" --verify-only .\data\evidence.json
```

By default this verifies the newest evidence record. Add `--evidence-index 0` to verify the first saved record (the command output prints each new record's index).

To demonstrate tamper detection, edit a field in a copy of `data/evidence.json` (such as `title`) and rerun the command. Its recomputed fingerprint does not exist in `ContentRegistry`, returning `"verified": false`.

## Polygon Amoy

Set `POLYGON_AMOY_RPC_URL`, `DEPLOYER_PRIVATE_KEY` (funded with Amoy MATIC), then deploy:

```powershell
npm run deploy:amoy
```

Set `RPC_URL` to the same Amoy RPC endpoint and `REGISTRY_ADDRESS` to the returned address. The Python command is unchanged.

## Privacy, ethics, and limitations

Use only images of people who have consented to this demonstration. Camera captures are uploaded to imgbb when using `--camera`; do not use this mode for sensitive images. Do not use this project to identify people in private contexts or to make consequential decisions. Face recognition is probabilistic: image quality, pose, age, and provider thumbnails affect results. Google Lens/SerpApi coverage is not a guarantee that a social post can be found, and provider terms/rate limits apply. An on-chain anchor proves that a particular canonical evidence record existed at a point in time; it does not prove the original post was truthful or establish identity. `uri` is an optional IPFS reference only; this project does not pin data itself.
