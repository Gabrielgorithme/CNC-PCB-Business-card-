# Notes for Claude

Carried over from the first card's repository (`Gabrielgorithme/CNC-Business-card-`) when the hybrid card moved here.

## Git
- Commit and push after each completed change, without waiting to be asked. Push to the session's working branch; never force-push and never push to `main` unless Gabriel asks.

## This repository
- It holds the hybrid card only (milled aluminium + PCB). The first card and the website stay in `Gabrielgorithme/CNC-Business-card-`.
- The URL in the card's QR code and NFC tag can never change: https://gabrielgorithme.github.io/CNC-Business-card-/ (GitHub Pages from the first repository).
- `lettering/` is a copy of the first card's ISOCP strokes (`site/isocp.py` and `docs/assets/data/isocp-card.json` there).
- `pcb/revA/out/order/` is the package sent to the fab. `pcb/revA/build.sh` rewrites its zip with new time stamps, so commit a new one only when the board itself changed, and say so.
- Client brands from Ambiance Lumière are never named (copy, alt text, file names): "a luxury fashion house". Notre-Dame de Paris may be named.
- Gabriel's phone number stays out of the repository.
