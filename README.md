# Face to Web to Blockchain Verifier

A privacy-conscious proof of concept that combines face matching, reverse-image search, and tamper-evident blockchain records.

Given a consented face image, the CLI:

1. Detects a face with OpenCV YuNet.
2. Creates a face embedding with OpenCV SFace.
3. Searches Google Lens through SerpApi.
4. Independently face-checks returned image thumbnails.
5. Lets the operator select a result.
6. Hashes the selected evidence with SHA-256.
7. Anchors the hash in a Solidity smart contract.
8. Reads the record back for verification.

This project finds probable visual matches. It does not prove identity, ownership, or the truth of a social-media post.

## Demo flow

```text
camera or image
      -> YuNet face detection
      -> SFace embedding
      -> ImgBB public upload for camera mode
      -> Google Lens / SerpApi search
      -> SFace comparison of candidate thumbnails
      -> human selects a result
      -> SHA-256 evidence fingerprint
      -> ContentRegistry blockchain anchor
      -> on-chain verification
```

## Technology

- Python 3.10+, OpenCV YuNet and SFace, Pillow, Requests
- Google Lens results through SerpApi
- Solidity `0.8.24`, Hardhat, and ethers.js
- Local Hardhat network or Polygon Amoy testnet

## Requirements

- Node.js 18+
- Python 3.10+
- A webcam for `--camera`
- A SerpApi key for live search
- An ImgBB key for automatic camera-image upload

## Installation

```powershell
npm install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm run compile
```

Create a `.env` file in the project root. Never commit it:

```env
SERPAPI_API_KEY=your_serpapi_key
IMGBB_API_KEY=your_imgbb_key
RPC_URL=http://127.0.0.1:8545
REGISTRY_ADDRESS=deployed_contract_address
DEPLOYER_PRIVATE_KEY=local_hardhat_account_key
```

On the first run, the YuNet and SFace ONNX models are downloaded from OpenCV Zoo and cached in `data/models`.

## Run the live camera demo

Start the local blockchain in one terminal:

```powershell
npm run node
```

Deploy the registry in a second terminal:

```powershell
npm run deploy:local
```

Put the returned `contractAddress` in `.env`, then run:

```powershell
python -m src.pipeline --camera
```

Press `SPACE` to capture or `Q` to cancel. The image is uploaded to ImgBB, searched through Google Lens, and compared with returned thumbnails. Select a displayed result to save and anchor it.

Useful options:

```powershell
python -m src.pipeline --camera --select 1
python -m src.pipeline --camera --include-web
python -m src.pipeline --camera --camera-index 1
python -m src.pipeline --camera --threshold 0.50
```

Use `--include-web` to include non-social pages. A lower threshold is stricter.

## Use a local image

Google Lens must be able to fetch the same image from a public HTTPS URL:

```powershell
python -m src.pipeline --image .\sample.jpg --source-url "https://example.com/sample.jpg"
```

## Opt-in personal profile mode

Personal profile mode is a separate offline workflow. It compares the camera image only with enrollment images and displays records supplied in `data/personal_profile.json`; it does not call Google Lens or upload the camera frame.

```powershell
python -m src.pipeline --camera --personal-profile .\data\personal_profile.json
```

Use this mode only with your own images and authorized profile or post metadata. See [examples/personal_profile.example.json](examples/personal_profile.example.json).

## Evidence and verification

Selected metadata is appended to `data/evidence.json`. The stable metadata is serialized canonically and hashed with SHA-256. The hash, timestamp, submitting wallet, and optional URI are stored by `ContentRegistry`.

Re-verify the newest saved record:

```powershell
python -m src.pipeline --image .\unused.jpg --source-url "https://unused.invalid" --verify-only .\data\evidence.json
```

Change a field in a copy of the evidence file and run verification again. The changed content produces a different hash and is reported as unverified.

## Polygon Amoy

For the Polygon Amoy testnet, set `POLYGON_AMOY_RPC_URL` and a wallet funded with test MATIC, then deploy:

```powershell
npm run deploy:amoy
```

Set `RPC_URL` to the same RPC endpoint and `REGISTRY_ADDRESS` to the deployed address.

## Privacy and limitations

- Use only images of people who have explicitly consented.
- Normal camera mode uploads the captured image to ImgBB and sends its URL to SerpApi/Google Lens.
- Face matching is probabilistic and affected by lighting, pose, age, image quality, and thumbnails.
- A search result is not proof of identity or ownership.
- A blockchain anchor proves that a specific evidence fingerprint existed at a point in time; it does not validate the underlying post.
- Do not use this project for surveillance, private identification, or consequential decisions.
- Rotate API keys and wallet keys immediately if they are exposed. Keep `.env`, captures, candidates, and evidence files out of version control.
