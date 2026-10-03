"""The Prague padel venues we track and how to reach their booking systems.

A venue with `disabled` set is listed in the report but never fetched.
"""

from .core import Venue

CLOUDFLARE = "iSportSystem sits behind a Cloudflare bot challenge; not scraped on purpose"

VENUES = [
    # --- Playtomic -------------------------------------------------------
    Venue("spoje", "Padel Club Spoje", "playtomic",
          {"slug": "padel-club-spoje", "tenant_id": "61e73f55-98c6-405f-ac6b-e2677af5905f"}),
    Venue("pisecna", "Tenis & Padel klub Písečná", "playtomic",
          {"slug": "tenis-a-padel-klub-pisecna", "tenant_id": "33257960-acca-4aa4-9f77-b6e5ab56f3e5"}),
    # --- rogeronline.cz --------------------------------------------------
    Venue("hagibor", "Hagibor Padel Bohemians", "rogeronline", {"klub": 173, "set": 4}, shows_past=True),
    Venue("satalice", "Padel Satalice", "rogeronline", {"klub": 197, "set": 3}, shows_past=True),
    # The "Padel 1,2" set lists no padel-named courts; "Olymp Plechovka 1/2" are a
    # guess and had zero reservations over five days, so it's off until verified.
    Venue("sparta", "TK Sparta Praha", "rogeronline", {"klub": 21, "set": 5, "court_filter": "plechovka"},
          shows_past=True, disabled="padel courts not identifiable in the rogeronline grid (unverified)"),
    # --- padelos.co ------------------------------------------------------
    Venue("powers", "Padel Powers Smíchov", "padelos", {
        "company": 217, "club": 216927, "hours": ("06:00", "24:00"),
        "courts": {str(i): f"Court {i - 60029}" for i in range(60030, 60038)},
    }),
    # --- Sportelo --------------------------------------------------------
    Venue("neride", "TK Neridé", "sportelo", {
        "subdomain": "neride", "field_group": "3435e961-8ca6-4c14-94ef-a0a4e3fe4ca2",
        # Bookable 24/7 (night rates); count the same 06–24 window as Powers.
        "hours": ("06:00", "24:00"),
        "courts": {"ab4a2ce9-72c3-4bb8-ad09-75fc8ece75b4": "Kurt 1",
                   "f005eac0-48e5-439b-a757-8ce5d21b4a03": "Kurt 2",
                   "35f4bb2d-95cb-4d3c-8936-9923f909277c": "Kurt 3"},
    }, shows_past=True),
    # --- Reenio ----------------------------------------------------------
    Venue("cisarska", "Areál Císařská louka", "reenio",
          {"slug": "areal-cisarska-louka", "service": "padel", "hours": ("09:00", "21:00")}, shows_past=True),
    # --- Clubspire -------------------------------------------------------
    Venue("skysport", "Sky Sport City Prosek", "clubspire", {"host": "rezervace.skysportcity.cz", "tab": 0}),
    # --- jdemenato.cz ----------------------------------------------------
    Venue("wilson", "Wilson Tenis Centrum", "jdemenato", {"slug": "wilson-tenis-centrum"}, shows_past=True),
    # --- own system (bot-protected) --------------------------------------
    Venue("slavia", "PADEL Slavia Praha", "slavia", {"exclude": "Dětský"},
          disabled="WEDOS bot protection answers automated requests with a verification page"),
    # --- iSportSystem (Cloudflare-protected) -----------------------------
    Venue("cpa", "CPA Arena (Czech Padel Academy)", "isportsystem", {"host": "padelautomat"}, disabled=CLOUDFLARE),
    Venue("forpadel", "For Padel Zdiměřice", "isportsystem", {"host": "forpadel"}, disabled=CLOUDFLARE),
    Venue("modrany", "LTC Modřany 2005", "isportsystem", {"host": "tenismodrany"}, disabled=CLOUDFLARE),
    Venue("radotin", "Padel Radotín", "isportsystem", {"host": "padelradotin"}, disabled=CLOUDFLARE),
    Venue("plechovka", "PLECHOVKA Dubeč", "isportsystem", {"host": "plechovka"}, disabled=CLOUDFLARE),
    Venue("vestec", "Tenis Centrum HEAD Vestec", "isportsystem", {"host": "teniscentrum"}, disabled=CLOUDFLARE),
    Venue("thecourt", "The Court", "isportsystem", {"host": "thecourt"}, disabled=CLOUDFLARE),
    # --- login required / no stable public endpoint -----------------------
    Venue("dzus", "Padel Džus", "bookaball", {}, disabled="bookaball requires login to see the calendar"),
    Venue("hector", "HECTOR Sport Centre & Restaurant", "r2s", {}, disabled="R2S web requires login to see the calendar"),
    Venue("onepadel", "One Padel Zličín", "courtyone", {},
          disabled="CourtyONE loads slots via Next.js server actions (IDs change per deploy); partner API needs a key"),
]
