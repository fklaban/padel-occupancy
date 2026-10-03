"""The Prague padel venues we track and how to reach their booking systems.

A venue with `disabled` set is listed in the report but never fetched.
`where="home"` venues refuse cloud/datacenter IPs and are fetched by
scripts/home-scrape.sh from a home connection instead of GitHub Actions.
"""

from .core import Venue


def isport(id, name, host, sport, **kw):
    return Venue(id, name, "isportsystem", {"host": host, "sport": sport, **kw})


VENUES = [
    # --- rogeronline.cz --------------------------------------------------
    Venue("hagibor", "Hagibor Padel Bohemians", "rogeronline", {"klub": 173, "set": 4}, shows_past=True),
    Venue("satalice", "Padel Satalice", "rogeronline", {"klub": 197, "set": 3}, shows_past=True),
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
    # --- CourtyONE (public Next.js server action) ------------------------
    Venue("onepadel", "One Padel Zličín", "courtyone",
          {"host": "onepadel.cz", "tenant": "onepadel", "venue": "praha-zlicin", "hours": ("07:00", "24:00")},
          shows_past=True),
    # --- bookaball (public guest booking wizard) -------------------------
    Venue("dzus", "Padel Džus", "bookaball", {"host": "padeldzus.bookaball.com", "location": 90}),
    # --- iSportSystem (public /api/get-times.php; HTML pages are behind Cloudflare)
    isport("cpa", "CPA Arena (Czech Padel Academy)", "padelautomat", 1),
    isport("forpadel", "For Padel Zdiměřice", "forpadel", 1),
    isport("modrany", "LTC Modřany 2005", "tenismodrany", 8),
    isport("radotin", "Padel Radotín", "padelradotin", 1),
    isport("plechovka", "PLECHOVKA Dubeč", "plechovka", 20, exclude=["náhradník"]),
    isport("vestec", "Tenis Centrum HEAD Vestec", "teniscentrum", 13),
    isport("thecourt", "The Court", "thecourt", 1),
    # --- home connection only: these refuse GitHub Actions IPs ------------
    Venue("spoje", "Padel Club Spoje", "playtomic",
          {"slug": "padel-club-spoje", "tenant_id": "61e73f55-98c6-405f-ac6b-e2677af5905f"}, where="home"),
    Venue("pisecna", "Tenis & Padel klub Písečná", "playtomic",
          {"slug": "tenis-a-padel-klub-pisecna", "tenant_id": "33257960-acca-4aa4-9f77-b6e5ab56f3e5"}, where="home"),
    Venue("wilson", "Wilson Tenis Centrum", "jdemenato", {"slug": "wilson-tenis-centrum"},
          shows_past=True, where="home"),
    # Padel is booked on jdemenato, not on the club's rogeronline grid.
    Venue("sparta", "TK Sparta Praha", "jdemenato", {"slug": "tk-sparta-praha"}, shows_past=True, where="home"),
    # --- not available without the club's help ----------------------------
    Venue("slavia", "PADEL Slavia Praha", "slavia", {"exclude": "Dětský"},
          disabled="WEDOS bot protection blocks automated requests; needs the club to allowlist us or share data"),
    Venue("hector", "HECTOR Sport Centre & Restaurant", "r2s", {},
          disabled="R2S calendar is visible only after login; needs the club to share data"),
]
