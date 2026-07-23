# rema-backend-python (deprecated prototype)

**Status:** Deprecated / unused prototype. Not for production.

Hardcoded secrets were rotated to obvious placeholders (`CHANGE_ME`) and must be supplied via environment variables only (`.env` is gitignored).

- `SECRET_KEY` — JWT signing (see `app/oauth2.py`, `app/core/config.py`)
- `ADMIN_RESET_KEY` — dangerous DB reset endpoint in `main.py`

Do not deploy this repo. Prefer the Elixir backend (`rema-backend`).

---

Previous note:

MISE À JOUR CRITIQUE : V1 (Sync & Ack)

Backend (Python) : Intégration du système d'accusé de réception (ACK) après synchronisation pour éviter les doublons.
