"""[DAWUD] Avions en direct depuis OpenSky.

API : GET https://opensky-network.org/api/states/all?lamin=..&lamax=..&lomin=..&lomax=..
Doc : https://openskynetwork.github.io/opensky-api/rest.html

Authentification : OAuth2 "client credentials" si OPENSKY_CLIENT_ID / OPENSKY_CLIENT_SECRET
sont dans .env (compte gratuit = beaucoup plus de crédits), sinon accès anonyme.
Coût : notre boîte (~96 degrés carrés) = 2 crédits par appel.
"""
from __future__ import annotations

import logging
import os
import time

import httpx
from dotenv import load_dotenv

from backend import config
from backend.models import Aircraft

load_dotenv()
log = logging.getLogger(__name__)

STATES_URL = "https://opensky-network.org/api/states/all"
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

M_TO_FT = 3.28084
MS_TO_KT = 1.943844

# Index des champs d'un "state vector" OpenSky
I_ICAO24, I_CALLSIGN, I_LAST_CONTACT = 0, 1, 4
I_LON, I_LAT, I_BARO_ALT, I_ON_GROUND = 5, 6, 7, 8
I_VELOCITY, I_TRACK, I_VRATE = 9, 10, 11

_token: dict = {"value": None, "expires_at": 0.0}
# Rempli après un 429 : on n'appelle plus avant cette date (epoch s)
_blocked_until: float = 0.0


def _get_token(client: httpx.Client) -> str | None:
    """Jeton OAuth2 (valide ~30 min), mis en cache. None si pas d'identifiants."""
    cid, secret = os.getenv("OPENSKY_CLIENT_ID"), os.getenv("OPENSKY_CLIENT_SECRET")
    if not cid or not secret:
        return None
    if _token["value"] and time.time() < _token["expires_at"] - 60:
        return _token["value"]
    r = client.post(TOKEN_URL, data={"grant_type": "client_credentials",
                                     "client_id": cid, "client_secret": secret})
    r.raise_for_status()
    body = r.json()
    _token["value"] = body["access_token"]
    _token["expires_at"] = time.time() + body.get("expires_in", 1800)
    return _token["value"]


def to_flight_level(baro_alt_m: float) -> int:
    """Altitude barométrique (m) -> niveau de vol arrondi aux 1 000 ft (niveaux RVSM)."""
    return int(round(baro_alt_m * M_TO_FT / 1000.0) * 10)


def parse_state(s: list, ts: int) -> Aircraft | None:
    """Convertit un state vector en Aircraft, ou None s'il n'est pas en croisière."""
    if s[I_ON_GROUND] or s[I_LAT] is None or s[I_LON] is None or s[I_BARO_ALT] is None:
        return None
    if abs(s[I_VRATE] or 0.0) > config.MAX_VERTICAL_RATE_MS:
        return None  # en montée ou en descente : pas en croisière, pas d'avis
    fl = to_flight_level(s[I_BARO_ALT])
    if not (config.MIN_FLIGHT_LEVEL <= fl <= config.MAX_FLIGHT_LEVEL):
        return None
    return Aircraft(
        icao24=s[I_ICAO24],
        callsign=(s[I_CALLSIGN] or "").strip() or s[I_ICAO24],
        lat=s[I_LAT],
        lon=s[I_LON],
        altitude_ft=round(s[I_BARO_ALT] * M_TO_FT),
        flight_level=fl,
        heading_deg=s[I_TRACK] or 0.0,
        speed_kt=round((s[I_VELOCITY] or 0.0) * MS_TO_KT),
        timestamp=s[I_LAST_CONTACT] or ts,
    )


def fetch_aircraft(bbox: dict | None = None) -> list[Aircraft]:
    """Avions en croisière (FL290-410, en vol, palier stable) dans la boîte. Liste vide en cas d'erreur ou de 429."""
    global _blocked_until
    bbox = bbox or config.BBOX
    if time.time() < _blocked_until:
        log.warning("OpenSky : quota épuisé, prochain essai dans %.0f s", _blocked_until - time.time())
        return []
    try:
        with httpx.Client(timeout=15) as client:
            token = _get_token(client)
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            r = client.get(STATES_URL, params=bbox, headers=headers)
            if r.status_code == 429:
                wait = float(r.headers.get("X-Rate-Limit-Retry-After-Seconds", 600))
                _blocked_until = time.time() + wait
                log.warning("OpenSky 429 : quota épuisé, pause de %.0f s", wait)
                return []
            r.raise_for_status()
            log.info("OpenSky : %s crédits restants", r.headers.get("X-Rate-Limit-Remaining", "?"))
            body = r.json()
    except httpx.HTTPError as e:
        log.error("OpenSky : %s", e)
        return []
    ts = body.get("time", int(time.time()))
    out = [a for s in (body.get("states") or []) if (a := parse_state(s, ts))]
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    planes = fetch_aircraft()
    print(f"{len(planes)} avions en croisière")
    for a in planes[:15]:
        print(f"  {a.callsign:8} FL{a.flight_level} cap {a.heading_deg:5.0f}°  {a.lat:.2f},{a.lon:.2f}")
