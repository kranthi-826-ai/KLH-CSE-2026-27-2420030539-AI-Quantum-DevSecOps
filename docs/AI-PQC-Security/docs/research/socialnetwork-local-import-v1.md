# SocialNetwork project-local import

On 2026-10-20 the training, validation and attack ZIP archives plus publisher
README were copied from Downloads into
`ml/data/raw/microservice-ids-2024/socialnetwork/`. Originals were preserved;
archives were not extracted and remain excluded from Git.

Each source matched the known publisher MD5 and the destination matched the
source SHA-256. Local audit record:
`ml/artifacts/socialnetwork-import-a50fce4a40a049b1aa95ead114fe6f8f.json`.

| File | Bytes | SHA-256 |
|---|---:|---|
| SocialNetwork-training-data.zip | 15783168409 | 51cd52ac6674f5ec27ef33d74dc554596a89624635da9a1bd3c913b8c8801354 |
| SocialNetwork-validation-data.zip | 940281110 | 94b6b37622f99d275021651eabb6d179c0ea2d17140d9c9485bf7c52961b9ba3 |
| SocialNetwork-attack-data.zip | 8715733448 | 9d816230e88dc75441a09f8b1ce2874b4588f9ca023c76868a99496d9ce356f8 |
| README.md | 2089 | 0e1a397f14677cef919e16278726adb577ef4a8bcc325e2402e456fbd3aca95b |

New entry points: `scripts/import-socialnetwork-dataset.ps1` and
`scripts/inspect-socialnetwork-local.ps1`. The latter produced the local
`socialnetwork-local-inspection-v1.json` artifact. Old frozen plans and source
paths remain unchanged. This is a provenance/location change, not a new model
or improved detection result. No additional independent scenario was scored.
