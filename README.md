# Face -> Web -> Blockchain Verifier

CLI proof-of-concept for the HH Goa 2026 Task 3 pipeline:

```text
face scan -> ArcFace embedding -> local FAISS social-post search (or Google Lens)
          -> selectable face-confirmed post -> SHA-256 evidence fingerprint
          -> ContentRegistry anchor -> independent on-chain re-verification
```

The search is live. The code sends the provided image URL to Google Lens through SerpApi at runtime, takes returned `visual_matches`, filters for Instagram, Facebook, X/Twitter, and Reddit links, downloads candidate thumbnails, and only lists posts when their independently computed face-embedding distance is at or below the configured threshold. The operator chooses which returned post to anchor. No post URL or identity is embedded in the repository.

## Stack

- Python, ONNX Runtime ArcFace embeddings, FAISS vector search, optional SerpApi Google Lens, SHA-256
- Solidity `0.8.24`, Hardhat and ethers.js
- Polygon Amoy is supported. A local Hardhat network is the recommended recording fallback.

## Setup

Prerequisites: Node.js 18+ and Python 3.10+. No C++ compiler is required. On first face scan, the program downloads YuNet and the pre-trained Buffalo-L ArcFace ONNX model, then caches them under `data/models`. This is a one-time model download.

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

## Fast local social-post index (recommended)

This mode searches only a consented collection you create, but is substantially faster and repeatable. It needs no SerpApi key, no imgbb key, and no public upload.

1. Copy `examples/posts.example.json` to `data/posts.json`. Add each consented post image under `data/posts/` and fill its real post URL, title, platform, and image path.
2. Build the ArcFace/FAISS index:

   ```powershell
   python -m src.build_index --manifest .\data\posts.json
   ```

3. Scan and select a matching indexed post:

   ```powershell
   python -m src.pipeline --camera --local-index
   ```

The local index stores 512-dimensional normalized ArcFace embeddings and ranks candidates by cosine similarity. Re-run `build_index` whenever images are added or changed.

### Required APIs

Local mode does not need a face-search, image-hosting, Instagram, Facebook, X, or Reddit API. It requires only the local Hardhat RPC for recording; Polygon Amoy instead requires an Amoy RPC endpoint and funded test-wallet key. Google Lens remains optional and requires `SERPAPI_API_KEY`; camera Lens mode also requires `IMGBB_API_KEY`. Obtain social images only through user consent or platform access that you are authorized to use.

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
