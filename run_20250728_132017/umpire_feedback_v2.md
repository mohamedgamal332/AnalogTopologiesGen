## Umpire Feedback: ERRORS DETECTED

### ERROR: Floating Net (C1)
- **Problem**: Net `SIGNAL_IN` on component `OUTPUT_STAGE` is floating.
- **Fix**: Connect this net to another component terminal.
---
### ERROR: NMOS/PMOS Mismatch (K1)
- **Problem**: NMOS stage `OUTPUT_STAGE` is loaded by non-PMOS load `LED_DRIVER`.
- **Fix**: Change load `LED_DRIVER` to a PMOS type (e.g., `CurrentMirrorP`).
---
