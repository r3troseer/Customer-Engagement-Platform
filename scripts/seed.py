"""
Seed script for GreenPlate Restaurant Group.

Calls real API endpoints via httpx — acts as a full integration smoke test.
All steps are idempotent: safe to run twice.

Run:
    uv run python -m scripts.seed

Target server is read from SEED_BASE_URL env var (default: http://localhost:8000).
"""
import asyncio
import io
import logging
import os
from datetime import date, timedelta

import httpx

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

BASE_URL = os.getenv("SEED_BASE_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE_URL}/api/v1"
PASSWORD = "GreenPlate2026!"

USERS = [
    {"first_name": "Alex",   "last_name": "Morgan",  "email": "admin@greenplate.co.uk",             "role": "platform_admin"},
    {"first_name": "Sam",    "last_name": "Clarke",   "email": "restaurant.admin@greenplate.co.uk",  "role": "restaurant_admin"},
    {"first_name": "Jordan", "last_name": "Lee",      "email": "auditor@greenplate.co.uk",           "role": "compliance_auditor"},
    {"first_name": "Priya",  "last_name": "Patel",    "email": "manager.london@greenplate.co.uk",    "role": "restaurant_manager"},
    {"first_name": "Tom",    "last_name": "Walsh",    "email": "manager.manchester@greenplate.co.uk","role": "restaurant_manager"},
    {"first_name": "Aisha",  "last_name": "Osei",     "email": "emp1@greenplate.co.uk",              "role": "employee"},
    {"first_name": "Ben",    "last_name": "Carter",   "email": "emp2@greenplate.co.uk",              "role": "employee"},
    {"first_name": "Chloe",  "last_name": "Wright",   "email": "emp3@greenplate.co.uk",              "role": "employee"},
    {"first_name": "Daniel", "last_name": "Kim",      "email": "emp4@greenplate.co.uk",              "role": "employee"},
    {"first_name": "Emma",   "last_name": "Singh",    "email": "emp5@greenplate.co.uk",              "role": "employee"},
    {"first_name": "Felix",  "last_name": "Brown",    "email": "emp6@greenplate.co.uk",              "role": "employee"},
    {"first_name": "Grace",  "last_name": "Liu",      "email": "supplier@freshfields.co.uk",         "role": "supplier_representative"},
]

SUPPLIERS = [
    {
        "supplier_name": "FreshFields Produce Ltd", "supplier_code": "SUP001",
        "contact_name": "Grace Liu", "contact_email": "supplier@freshfields.co.uk",
        "supplier_type": "Produce", "is_public": True,
        "public_summary": "UK-grown seasonal produce, delivered direct to restaurant kitchens.",
        "esg_highlights": "100% pesticide-free farming; zero-miles pledge for London deliveries.",
    },
    {
        "supplier_name": "EcoPack Packaging Ltd", "supplier_code": "SUP002",
        "contact_name": "Marcus Reid", "contact_email": "marcus@ecopack.co.uk",
        "supplier_type": "Packaging", "is_public": True,
        "public_summary": "Compostable and recycled-content packaging for food service.",
        "esg_highlights": "100% recyclable or compostable product range; B-Corp certified.",
    },
    {
        "supplier_name": "CleanGreen Solutions Ltd", "supplier_code": "SUP003",
        "contact_name": "Sarah Okonkwo", "contact_email": "s.okonkwo@cleangreen.co.uk",
        "supplier_type": "Cleaning", "is_public": True,
        "public_summary": "Eco-certified cleaning products and waste management services.",
        "esg_highlights": "Biodegradable formulations; water-positive manufacturing facility.",
    },
    {
        "supplier_name": "BrightWatts Energy Ltd", "supplier_code": "SUP004",
        "contact_name": "David Chen", "contact_email": "d.chen@brightwatts.co.uk",
        "supplier_type": "Energy", "is_public": True,
        "public_summary": "100% renewable electricity tariffs for commercial kitchens.",
        "esg_highlights": "Backed by REGO-certified wind and solar; carbon-neutral since 2022.",
    },
]

ESG_OBJECTIVES = [
    {
        "category": "environmental", "title": "Carbon Emissions Reduction",
        "target_value": "500", "target_unit": "tCO2e",
        "start_date": "2026-01-01", "end_date": "2026-12-31",
        "status": "active", "sdg_goal_numbers": [13],
        "metric_code": "CARBON_MONTHLY", "metric_name": "Monthly Carbon tCO2e",
        "base_value": 48.0, "delta": -1.2,
    },
    {
        "category": "environmental", "title": "Water Consumption Reduction",
        "target_value": "10000", "target_unit": "litres",
        "start_date": "2026-01-01", "end_date": "2026-12-31",
        "status": "active", "sdg_goal_numbers": [6],
        "metric_code": "WATER_MONTHLY", "metric_name": "Monthly Water Usage (litres)",
        "base_value": 9800.0, "delta": -120.0,
    },
    {
        "category": "environmental", "title": "Waste Diversion Rate",
        "target_value": "80", "target_unit": "%",
        "start_date": "2026-01-01", "end_date": "2026-12-31",
        "status": "active", "sdg_goal_numbers": [12],
        "metric_code": "WASTE_DIVERSION", "metric_name": "Monthly Waste Diversion %",
        "base_value": 58.0, "delta": 3.5,
    },
    {
        "category": "environmental", "title": "Renewable Energy Usage",
        "target_value": "100", "target_unit": "%",
        "start_date": "2026-01-01", "end_date": "2026-12-31",
        "status": "active", "sdg_goal_numbers": [7],
        "metric_code": "RENEWABLE_PCT", "metric_name": "Renewable Energy %",
        "base_value": 62.0, "delta": 5.0,
    },
]


def _make_cert_pdf(supplier_name: str, doc_type: str, issue_date: str, expiry_date: str) -> bytes:
    """
    Generate a real openable PDF using reportlab.
    GreenPlate letterhead, supplier details, issue/expiry dates, certified footer.
    Returns raw PDF bytes.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    green = colors.HexColor("#2d6a4f")
    light_green = colors.HexColor("#52b788")

    story.append(Paragraph("GreenPlate Restaurant Group", styles["Title"]))
    story.append(Paragraph("10 Sustainability Street, London EC1A 2BP", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        f"{doc_type.title()} — {supplier_name}",
        styles["Heading1"],
    ))
    story.append(Spacer(1, 0.4 * cm))

    data = [
        ["Field", "Value"],
        ["Supplier", supplier_name],
        ["Document Type", doc_type.title()],
        ["Issue Date", issue_date],
        ["Expiry Date", expiry_date],
        ["Status", "Active"],
    ]
    t = Table(data, colWidths=[6 * cm, 11 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), green),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f0")]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph(
        "This document has been verified and certified by the GreenPlate Compliance Team.",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        f"Certified by GreenPlate Compliance Team | {issue_date}",
        styles["Normal"],
    ))

    doc.build(story)
    return buf.getvalue()


class Seeder:
    def __init__(self):
        self.client: httpx.AsyncClient = None  # type: ignore[assignment]
        self.admin_token: str = ""
        self.users: dict[str, dict] = {}   # email -> {id, token}
        self.org_id: int = 0
        self.locations: list[dict] = []    # [{id, name}]
        self.departments: list[dict] = []
        self.employees: list[dict] = []    # [{id, user_id, emp_email}]
        self.suppliers: list[dict] = []    # [{id, name}]
        self.esg_objectives: list[dict] = []
        self.fw_iso: int = 0
        self.fw_food: int = 0
        self.reward_meal_id: int = 0

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _auth_headers(self, token: str | None) -> dict:
        t = token if token is not None else self.admin_token
        return {"Authorization": f"Bearer {t}"} if t else {}

    async def _post(self, path: str, body: dict, token: str | None = None) -> dict:
        r = await self.client.post(f"{API}{path}", json=body, headers=self._auth_headers(token))
        r.raise_for_status()
        return r.json()

    async def _post_multipart(self, path: str, fields: dict, files: dict, token: str | None = None) -> dict:
        r = await self.client.post(f"{API}{path}", data=fields, files=files, headers=self._auth_headers(token))
        r.raise_for_status()
        return r.json()

    async def _get(self, path: str, token: str | None = None, params: dict | None = None) -> dict | list:
        r = await self.client.get(f"{API}{path}", headers=self._auth_headers(token), params=params)
        r.raise_for_status()
        return r.json()

    async def _login(self, email: str) -> str:
        r = await self.client.post(f"{API}/auth/login", json={"email": email, "password": PASSWORD})
        r.raise_for_status()
        return r.json()["access_token"]

    # ── Step 1: Register users ────────────────────────────────────────────────

    async def seed_users(self):
        """
        The restaurant admin opens the platform for the first time and registers every
        team member before their first shift. Each person gets a work-email account —
        the two managers, six kitchen and floor staff, the sustainability auditor,
        and the contact at FreshFields Produce who'll upload their compliance docs.
        Role assignments aren't done through the registration form; the platform admin
        does that separately in the admin panel (here: a dedicated seed_roles step).
        """
        for u in USERS:
            try:
                r = await self.client.post(f"{API}/auth/register", json={
                    "first_name": u["first_name"],
                    "last_name": u["last_name"],
                    "email": u["email"],
                    "password": PASSWORD,
                })
                r.raise_for_status()
                data = r.json()
                user_id = data["id"]
                log.info("  ✓ registered %s (id=%s)", u["email"], user_id)
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    # Already exists — get ID via login
                    tok = await self._login(u["email"])
                    me = await self._get("/auth/me", token=tok)
                    user_id = me["id"]  # type: ignore[index]
                    log.info("  ~ already exists %s (id=%s)", u["email"], user_id)
                else:
                    raise
            self.users[u["email"]] = {"id": user_id, "token": "", "role": u["role"]}

        # Admin login needed for subsequent steps
        self.admin_token = await self._login("admin@greenplate.co.uk")
        self.users["admin@greenplate.co.uk"]["token"] = self.admin_token
        log.info("✓ seed_users done (%d users)", len(USERS))

    # ── Step 2: Assign roles ──────────────────────────────────────────────────

    async def seed_roles(self):
        """
        With all twelve accounts registered, the platform admin works through the user
        list and assigns each person their role — platform admin, restaurant admin,
        compliance auditor, managers, employees, and the supplier rep from FreshFields.
        This is done through the role-assignment endpoint rather than at registration time,
        which mirrors how a real admin would promote or reconfigure users later on.
        """
        for u in USERS:
            user_id = self.users[u["email"]]["id"]
            try:
                await self._post(f"/auth/users/{user_id}/roles", {"role_name": u["role"]})
                log.info("  ✓ assigned %s → %s", u["email"], u["role"])
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    log.info("  ~ role already assigned %s", u["email"])
                else:
                    raise
        log.info("✓ seed_roles done")

    # ── Step 3: Organisation ──────────────────────────────────────────────────

    async def seed_org(self):
        """
        With accounts ready, the platform admin registers GreenPlate Restaurant Group
        as the organisation and adds the three restaurant sites — London HQ, Manchester,
        and Birmingham. Each site gets a unique location code so that work logs,
        leaderboards, and ESG metrics can be filtered by branch.
        """
        # Organisation
        try:
            data = await self._post("/org/organizations", {
                "name": "GreenPlate Restaurant Group",
                "legal_name": "GreenPlate Holdings Ltd",
                "registration_number": "GP20240001",
                "tax_number": "GB123456789",
                "contact_email": "contact@greenplate.co.uk",
                "contact_phone": "+442071234567",
                "website": "https://greenplate.co.uk",
                "address_line_1": "10 Sustainability Street",
                "city": "London",
                "state_region": "England",
                "postcode": "EC1A 2BP",
                "country": "GB",
                "status": "active",
            })
            self.org_id = data["id"]
            log.info("  ✓ created org (id=%s)", self.org_id)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (400, 409):
                orgs = await self._get("/org/organizations")
                self.org_id = orgs[0]["id"]  # type: ignore[index]
                log.info("  ~ org already exists (id=%s)", self.org_id)
            else:
                raise

        # Locations
        loc_defs = [
            {"name": "London HQ",    "location_code": "LOC001", "city": "London",      "postcode": "EC1A 2BP", "address_line_1": "10 Sustainability Street"},
            {"name": "Manchester",   "location_code": "LOC002", "city": "Manchester",  "postcode": "M1 1AA",   "address_line_1": "5 Green Quarter"},
            {"name": "Birmingham",   "location_code": "LOC003", "city": "Birmingham",  "postcode": "B1 1AA",   "address_line_1": "22 Eco Park Way"},
        ]
        for ld in loc_defs:
            try:
                loc = await self._post("/org/locations", {
                    "organization_id": self.org_id,
                    "name": ld["name"],
                    "location_code": ld["location_code"],
                    "address_line_1": ld["address_line_1"],
                    "city": ld["city"],
                    "postcode": ld["postcode"],
                    "country": "GB",
                    "timezone": "Europe/London",
                })
                self.locations.append({"id": loc["id"], "name": ld["name"]})
                log.info("  ✓ created location %s (id=%s)", ld["name"], loc["id"])
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    locs = await self._get("/org/locations", params={"organization_id": self.org_id})
                    for existing in locs:  # type: ignore[union-attr]
                        if existing["location_code"] == ld["location_code"]:
                            self.locations.append({"id": existing["id"], "name": ld["name"]})
                    log.info("  ~ location already exists %s", ld["name"])
                else:
                    raise

        log.info("✓ seed_org done (org_id=%s, %d locations)", self.org_id, len(self.locations))

    # ── Step 4: Departments ───────────────────────────────────────────────────

    async def seed_departments(self):
        """
        The restaurant admin creates the three departments that reflect how GreenPlate
        is structured on the floor: Kitchen, Front of House, and Operations. Departments
        are org-wide (not per-location) so the same names appear across all three sites.
        """
        dept_names = ["Kitchen", "Front of House", "Operations"]
        for name in dept_names:
            try:
                dept = await self._post("/org/departments", {
                    "organization_id": self.org_id,
                    "name": name,
                })
                self.departments.append({"id": dept["id"], "name": name})
                log.info("  ✓ created department %s (id=%s)", name, dept["id"])
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    depts = await self._get("/org/departments", params={"organization_id": self.org_id})
                    for existing in depts:  # type: ignore[union-attr]
                        if existing["name"] == name:
                            self.departments.append({"id": existing["id"], "name": name})
                    log.info("  ~ department already exists %s", name)
                else:
                    raise
        log.info("✓ seed_departments done")

    # ── Step 5: Employees ─────────────────────────────────────────────────────

    async def seed_employees(self):
        """
        Each team member's account is now linked to their role within GreenPlate.
        The restaurant admin creates an employee record for every manager and staff
        member — assigning them to a department and their home location. From this point
        on, their work logs and token earnings are tied to their employee profile.
        """
        # 8 employees: 2 managers + 6 staff (skip admin, auditor, supplier rep)
        emp_defs = [
            {"email": "manager.london@greenplate.co.uk",    "code": "EMP001", "title": "Head Chef",            "dept": "Kitchen",        "loc": "London HQ"},
            {"email": "manager.manchester@greenplate.co.uk","code": "EMP002", "title": "Restaurant Manager",    "dept": "Operations",     "loc": "Manchester"},
            {"email": "emp1@greenplate.co.uk",              "code": "EMP003", "title": "Sous Chef",             "dept": "Kitchen",        "loc": "London HQ"},
            {"email": "emp2@greenplate.co.uk",              "code": "EMP004", "title": "Chef de Partie",        "dept": "Kitchen",        "loc": "London HQ"},
            {"email": "emp3@greenplate.co.uk",              "code": "EMP005", "title": "Front of House Lead",   "dept": "Front of House", "loc": "London HQ"},
            {"email": "emp4@greenplate.co.uk",              "code": "EMP006", "title": "Waiting Staff",         "dept": "Front of House", "loc": "Manchester"},
            {"email": "emp5@greenplate.co.uk",              "code": "EMP007", "title": "Operations Coordinator","dept": "Operations",     "loc": "Birmingham"},
            {"email": "emp6@greenplate.co.uk",              "code": "EMP008", "title": "Kitchen Porter",        "dept": "Kitchen",        "loc": "Birmingham"},
        ]

        dept_by_name = {d["name"]: d["id"] for d in self.departments}
        loc_by_name  = {l["name"]: l["id"] for l in self.locations}

        for ed in emp_defs:
            user_id = self.users[ed["email"]]["id"]
            dept_id = dept_by_name[ed["dept"]]
            loc_id  = loc_by_name[ed["loc"]]
            try:
                emp = await self._post("/org/employees", {
                    "user_id": user_id,
                    "organization_id": self.org_id,
                    "department_id": dept_id,
                    "employee_code": ed["code"],
                    "job_title": ed["title"],
                    "hire_date": "2024-01-15",
                    "employment_status": "active",
                    "primary_location_id": loc_id,
                })
                self.employees.append({"id": emp["id"], "user_id": user_id, "email": ed["email"], "loc_id": loc_id})
                log.info("  ✓ created employee %s (id=%s)", ed["email"], emp["id"])
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    emps = await self._get("/org/employees", params={"organization_id": self.org_id})
                    for existing in emps:  # type: ignore[union-attr]
                        if existing["user_id"] == user_id:
                            self.employees.append({"id": existing["id"], "user_id": user_id, "email": ed["email"], "loc_id": loc_id})
                    log.info("  ~ employee already exists %s", ed["email"])
                else:
                    raise

        log.info("✓ seed_employees done (%d employees)", len(self.employees))

    # ── Step 6: Suppliers ─────────────────────────────────────────────────────

    async def seed_suppliers(self):
        """
        The compliance team registers GreenPlate's four key suppliers in the platform
        and links each one to the London HQ location so they appear on location-filtered
        reports. For each supplier, they upload two compliance documents: the current
        certification (a real PDF with the supplier's details and expiry date) and a
        pending licence renewal that's awaiting the next audit. The admin then reviews
        and approves the current certs so the supplier transparency report shows them
        as certified.
        """
        london_loc_id = next(l["id"] for l in self.locations if l["name"] == "London HQ")

        for sup_def in SUPPLIERS:
            # Create supplier
            try:
                sup = await self._post("/suppliers/", sup_def)
                sup_id = sup["id"]
                log.info("  ✓ created supplier %s (id=%s)", sup_def["supplier_name"], sup_id)
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    sups = await self._get("/suppliers/")
                    items = sups.get("items", sups) if isinstance(sups, dict) else sups  # type: ignore[union-attr]
                    for existing in items:  # type: ignore[union-attr]
                        if existing["supplier_code"] == sup_def["supplier_code"]:
                            sup_id = existing["id"]
                    log.info("  ~ supplier already exists %s", sup_def["supplier_name"])
                else:
                    raise

            self.suppliers.append({"id": sup_id, "name": sup_def["supplier_name"]})

            # Link supplier to London HQ
            try:
                await self._post(f"/suppliers/{sup_id}/locations", {
                    "organization_id": self.org_id,
                    "location_id": london_loc_id,
                    "service_type": sup_def["supplier_type"],
                    "relationship_type": "primary",
                })
                log.info("    ✓ linked to London HQ")
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    log.info("    ~ location link already exists")
                else:
                    raise

            # Upload certificate (will be approved) + licence (stays pending)
            today = date.today()
            docs_to_upload = [
                {"doc_type": "certificate", "title": f"{sup_def['supplier_name']} — Sustainability Certificate",
                 "issue": str(today - timedelta(days=180)), "expiry": str(today + timedelta(days=185)), "approve": True},
                {"doc_type": "license",     "title": f"{sup_def['supplier_name']} — Operating Licence",
                 "issue": str(today - timedelta(days=90)),  "expiry": str(today + timedelta(days=275)), "approve": False},
            ]
            for dd in docs_to_upload:
                pdf_bytes = _make_cert_pdf(sup_def["supplier_name"], dd["doc_type"], dd["issue"], dd["expiry"])
                file_name = f"{sup_def['supplier_code']}_{dd['doc_type']}.pdf"
                try:
                    doc = await self._post_multipart(
                        f"/suppliers/{sup_id}/documents",
                        fields={
                            "title": dd["title"],
                            "document_type": dd["doc_type"],
                            "issue_date": dd["issue"],
                            "expiry_date": dd["expiry"],
                        },
                        files={"file": (file_name, pdf_bytes, "application/pdf")},
                    )
                    doc_id = doc["id"]
                    log.info("    ✓ uploaded %s (id=%s)", dd["doc_type"], doc_id)

                    if dd["approve"]:
                        await self._post(
                            f"/suppliers/{sup_id}/documents/{doc_id}/review",
                            {"action": "approved", "feedback": None},
                        )
                        log.info("    ✓ approved certificate")
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (400, 409):
                        log.info("    ~ document already uploaded %s", dd["doc_type"])
                    else:
                        raise

        log.info("✓ seed_suppliers done (%d suppliers)", len(self.suppliers))

    # ── Step 7: ESG ───────────────────────────────────────────────────────────

    async def seed_esg(self):
        """
        The sustainability manager sets the four ESG objectives GreenPlate is tracking
        against its 2026 targets — cutting carbon emissions, reducing water consumption,
        hitting an 80% waste diversion rate, and reaching 100% renewable energy.
        They then enter six months of historical monthly readings for each objective
        so the ESG report has a realistic trend line rather than starting from zero.
        """
        admin_id = self.users["admin@greenplate.co.uk"]["id"]

        for obj_def in ESG_OBJECTIVES:
            try:
                obj = await self._post("/esg/objectives", {
                    "organization_id": self.org_id,
                    "category": obj_def["category"],
                    "title": obj_def["title"],
                    "target_value": obj_def["target_value"],
                    "target_unit": obj_def["target_unit"],
                    "start_date": obj_def["start_date"],
                    "end_date": obj_def["end_date"],
                    "status": obj_def["status"],
                    "sdg_goal_numbers": obj_def["sdg_goal_numbers"],
                    "created_by": admin_id,
                })
                obj_id = obj["id"]
                log.info("  ✓ created ESG objective: %s (id=%s)", obj_def["title"], obj_id)
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    objs = await self._get("/esg/objectives", params={"organization_id": self.org_id})
                    items = objs.get("items", objs) if isinstance(objs, dict) else objs  # type: ignore[union-attr]
                    obj_id = next(o["id"] for o in items if o["title"] == obj_def["title"])  # type: ignore[union-attr]
                    log.info("  ~ ESG objective already exists: %s", obj_def["title"])
                else:
                    raise

            self.esg_objectives.append({"id": obj_id, **obj_def})

            # 5 monthly metric readings — last 5 months, improving trend
            today = date.today()
            for i in range(5):
                value_date = (today.replace(day=1) - timedelta(days=30 * (4 - i))).replace(day=1)
                metric_val = obj_def["base_value"] + obj_def["delta"] * i
                try:
                    await self._post("/esg/metric-values", {
                        "organization_id": self.org_id,
                        "esg_objective_id": obj_id,
                        "metric_name": obj_def["metric_name"],
                        "metric_code": obj_def["metric_code"],
                        "category": obj_def["category"],
                        "unit": obj_def["target_unit"],
                        "metric_value": str(round(metric_val, 2)),
                        "value_date": str(value_date),
                        "source_type": "manual",
                        "recorded_by": admin_id,
                    })
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (400, 409):
                        log.info("    ~ metric already exists for %s", value_date)
                    else:
                        raise

            log.info("    ✓ seeded 5 metric readings for %s", obj_def["title"])

        log.info("✓ seed_esg done (%d objectives)", len(ESG_OBJECTIVES))

    # ── Step 8: Compliance ────────────────────────────────────────────────────

    async def seed_compliance(self):
        """
        The compliance auditor registers the two frameworks GreenPlate operates under:
        ISO 14001 for environmental management and the UK Food Safety Act.
        They add three requirements under each and record the organisation's current
        position — most requirements are met (compliant), two are still being worked on
        (in_progress), and one hasn't been started yet (not_started).
        This gives the compliance report a realistic, mixed-status picture.
        """
        admin_id = self.users["admin@greenplate.co.uk"]["id"]

        frameworks = [
            {
                "name": "ISO 14001 Environmental Management",
                "framework_code": "ISO14001",
                "framework_type": "esg",
                "version": "2015",
                "requirements": [
                    {"code": "ISO14001-4.1", "title": "Environmental Policy",            "status": "compliant"},
                    {"code": "ISO14001-9.2", "title": "Legal Compliance Monitoring",     "status": "compliant"},
                    {"code": "ISO14001-9.3", "title": "Internal Audit",                  "status": "in_progress"},
                ],
            },
            {
                "name": "UK Food Safety Act 2006",
                "framework_code": "UKFSA2006",
                "framework_type": "operational",
                "version": "2006",
                "requirements": [
                    {"code": "UKFSA-3.1", "title": "HACCP Implementation",              "status": "compliant"},
                    {"code": "UKFSA-3.2", "title": "Temperature Control Records",       "status": "in_progress"},
                    {"code": "UKFSA-4.1", "title": "Staff Training & Certification",    "status": "not_started"},
                ],
            },
        ]

        for fw_def in frameworks:
            try:
                fw = await self._post("/compliance/frameworks", {
                    "name": fw_def["name"],
                    "framework_code": fw_def["framework_code"],
                    "framework_type": fw_def["framework_type"],
                    "version": fw_def["version"],
                    "created_by": admin_id,
                })
                fw_id = fw["id"]
                log.info("  ✓ created framework: %s (id=%s)", fw_def["name"], fw_id)
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    fws = await self._get("/compliance/frameworks")
                    items = fws.get("items", fws) if isinstance(fws, dict) else fws  # type: ignore[union-attr]
                    fw_id = next(f["id"] for f in items if f["framework_code"] == fw_def["framework_code"])  # type: ignore[union-attr]
                    log.info("  ~ framework already exists: %s", fw_def["name"])
                else:
                    raise

            if fw_def["framework_code"] == "ISO14001":
                self.fw_iso = fw_id
            else:
                self.fw_food = fw_id

            for req_def in fw_def["requirements"]:
                try:
                    req = await self._post("/compliance/requirements", {
                        "framework_id": fw_id,
                        "requirement_code": req_def["code"],
                        "title": req_def["title"],
                        "is_mandatory": True,
                        "created_by": admin_id,
                    })
                    req_id = req["id"]
                    log.info("    ✓ created requirement: %s", req_def["title"])
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (400, 409):
                        reqs = await self._get(f"/compliance/requirements", params={"framework_id": fw_id})
                        items = reqs.get("items", reqs) if isinstance(reqs, dict) else reqs  # type: ignore[union-attr]
                        req_id = next(r["id"] for r in items if r["requirement_code"] == req_def["code"])  # type: ignore[union-attr]
                        log.info("    ~ requirement already exists: %s", req_def["title"])
                    else:
                        raise

                try:
                    await self._post("/compliance/organization-compliance", {
                        "organization_id": self.org_id,
                        "requirement_id": req_id,
                        "status": req_def["status"],
                    })
                    log.info("    ✓ org compliance record: %s → %s", req_def["code"], req_def["status"])
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (400, 409):
                        log.info("    ~ compliance record already exists: %s", req_def["code"])
                    else:
                        raise

        log.info("✓ seed_compliance done")

    # ── Step 9: Token economy ─────────────────────────────────────────────────

    async def seed_tokens(self):
        """
        The platform admin configures how employees earn GreenTokens: 10 tokens for
        every work log, 25 bonus tokens for shifts marked as a sustainability initiative,
        and 50 tokens for finishing in the top 3 on the weekly leaderboard.
        Three rewards go into the catalogue — a Free Meal Voucher, an Extra Day Off,
        and a GreenPlate branded hoodie — so employees have something to spend their
        tokens on from day one.
        """
        # Wallets — one per employee (including managers)
        for emp in self.employees:
            try:
                await self._post("/tokens/wallets", {
                    "user_id": emp["user_id"],
                    "wallet_type": "employee",
                })
                log.info("  ✓ created wallet for user_id=%s", emp["user_id"])
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    log.info("  ~ wallet already exists for user_id=%s", emp["user_id"])
                else:
                    raise

        # Token rules
        rules = [
            {
                "organization_id": self.org_id,
                "rule_name": "Work Log Earn",
                "rule_type": "employee_activity",
                "tokens_awarded": "10",
                "is_active": True,
                "condition_details": {"activity_type": "work_log", "min_count": 1, "period": "daily"},
            },
            {
                "organization_id": self.org_id,
                "rule_name": "Sustainability Initiative Bonus",
                "rule_type": "employee_activity",
                "tokens_awarded": "25",
                "is_active": True,
                "condition_details": {"activity_type": "sustainability_initiative", "min_count": 1, "period": "daily"},
            },
            {
                "organization_id": self.org_id,
                "rule_name": "Leaderboard Top 3 Bonus",
                "rule_type": "leaderboard_bonus",
                "tokens_awarded": "50",
                "is_active": True,
                "condition_details": {"top_n": 3, "period": "weekly"},
            },
        ]
        for rule in rules:
            try:
                await self._post("/tokens/rules", rule)
                log.info("  ✓ created token rule: %s", rule["rule_name"])
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    log.info("  ~ token rule already exists: %s", rule["rule_name"])
                else:
                    raise

        # Rewards catalogue
        catalog = [
            {"title": "Free Meal Voucher",  "reward_type": "voucher",  "token_cost": "100", "applicable_to": "employee"},
            {"title": "Extra Day Off",       "reward_type": "voucher",  "token_cost": "500", "applicable_to": "employee"},
            {"title": "GreenPlate Hoodie",   "reward_type": "offer",    "token_cost": "200", "applicable_to": "employee"},
        ]
        for item in catalog:
            try:
                reward = await self._post("/tokens/catalog", {**item, "organization_id": self.org_id})
                log.info("  ✓ created catalog item: %s (id=%s)", item["title"], reward["id"])
                if item["title"] == "Free Meal Voucher":
                    self.reward_meal_id = reward["id"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    log.info("  ~ catalog item already exists: %s", item["title"])
                    if item["title"] == "Free Meal Voucher" and not self.reward_meal_id:
                        rewards = await self._get("/tokens/catalog")
                        items = rewards.get("items", rewards) if isinstance(rewards, dict) else rewards  # type: ignore[union-attr]
                        for r in items:  # type: ignore[union-attr]
                            if r["title"] == "Free Meal Voucher":
                                self.reward_meal_id = r["id"]
                else:
                    raise

        log.info("✓ seed_tokens done (meal reward id=%s)", self.reward_meal_id)

    # ── Step 10: Work logs ────────────────────────────────────────────────────

    async def seed_work_logs(self):
        """
        Each employee logs their shifts for the past three weeks. Regular shifts earn
        the standard 10-token work log award. Shifts marked as sustainability initiatives
        — like running a food-waste audit or a composting programme — earn an extra
        25 tokens on top. The first two employees (Aisha and Ben) log enough shifts
        to accumulate over 100 tokens so they can redeem a Free Meal Voucher next.
        """
        today = date.today()

        # High-engagement pair: Aisha (emp1) + Ben (emp2) — 3 sustain + 3 regular = 105 tokens
        high_engagement_emails = {"emp1@greenplate.co.uk", "emp2@greenplate.co.uk"}

        sustainability_notes = [
            ("Food waste audit — pre-consumer waste down 12% vs last week",        "Weekly kitchen food waste audit"),
            ("Composting pilot — 8kg organic waste diverted from landfill",         "Staff composting programme"),
            ("Energy walk — identified 3 kitchen appliances left on overnight",     "Energy audit initiative"),
        ]
        regular_notes = [
            "Morning kitchen prep shift",
            "Lunch service — full cover",
            "Evening close-down and clean",
        ]

        for emp in self.employees:
            email = emp["email"]
            emp_id = emp["id"]
            loc_id = emp["loc_id"]

            # Login as this employee
            token = self.users[email].get("token") or await self._login(email)
            self.users[email]["token"] = token

            if email in high_engagement_emails:
                logs = (
                    [(True, sustainability_notes[i][0], sustainability_notes[i][1]) for i in range(3)]
                    + [(False, regular_notes[i], None) for i in range(3)]
                )
            elif email in {"manager.london@greenplate.co.uk", "manager.manchester@greenplate.co.uk"}:
                logs = [(False, regular_notes[i], None) for i in range(2)]
            else:
                # Casual: 1 sustainability + 2 regular = 45 tokens
                logs = (
                    [(True, sustainability_notes[0][0], sustainability_notes[0][1])]
                    + [(False, regular_notes[i], None) for i in range(2)]
                )

            for idx, (is_sustain, notes, details) in enumerate(logs):
                work_date = today - timedelta(days=idx * 3 + 1)
                body = {
                    "employee_id": emp_id,
                    "location_id": loc_id,
                    "work_date": str(work_date),
                    "hours_worked": "8.0",
                    "activity_notes": notes,
                    "sustainability_initiative": is_sustain,
                }
                if is_sustain and details:
                    body["initiative_details"] = details
                try:
                    await self._post("/workforce/work-logs", body, token=token)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (400, 409):
                        log.info("    ~ work log already exists for %s on %s", email, work_date)
                    else:
                        raise

            log.info("  ✓ seeded %d logs for %s", len(logs), email)

        log.info("✓ seed_work_logs done")

    # ── Step 11: Redemptions ──────────────────────────────────────────────────

    async def seed_redemptions(self):
        """
        Two employees who've earned enough GreenTokens cash them in for a Free Meal
        Voucher — 100 tokens each. The platform deducts the tokens, generates a voucher
        code, and sends them a notification. This exercises the full redemption flow
        including wallet debit and the rewards catalogue.
        """
        redeemers = ["emp1@greenplate.co.uk", "emp2@greenplate.co.uk"]
        for email in redeemers:
            token = self.users[email]["token"]
            try:
                result = await self._post("/workforce/redemptions", {"reward_id": self.reward_meal_id}, token=token)
                log.info("  ✓ redeemed Free Meal Voucher for %s (redemption id=%s)", email, result["id"])
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409, 422):
                    log.info("  ~ already redeemed or insufficient tokens for %s (%s)", email, e.response.text[:80])
                else:
                    raise

        log.info("✓ seed_redemptions done")

    # ── Step 12: Report templates ─────────────────────────────────────────────

    async def seed_templates(self):
        """
        The restaurant admin sets up two report templates. The first is a monthly ESG
        performance report that the scheduler will run automatically each month and
        notify the sustainability team when it's ready. The second is a quarterly
        compliance review that the auditor triggers manually before board meetings.
        """
        templates = [
            {
                "template_name": "Monthly ESG Performance Report",
                "report_type": "esg",
                "schedule_enabled": True,
                "notify_on_complete": True,
                "template_config": {"start_date": "2026-01-01"},
            },
            {
                "template_name": "Quarterly Compliance Review",
                "report_type": "compliance",
                "schedule_enabled": False,
                "notify_on_complete": True,
                "template_config": {},
            },
        ]
        for tmpl in templates:
            try:
                result = await self._post("/reports/templates", tmpl)
                log.info("  ✓ created template: %s (id=%s)", tmpl["template_name"], result["id"])
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 409):
                    log.info("  ~ template already exists: %s", tmpl["template_name"])
                else:
                    raise

        log.info("✓ seed_templates done")

    # ── Entry point ───────────────────────────────────────────────────────────

    async def run(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            self.client = client
            log.info("=== GreenPlate seed starting (server: %s) ===", BASE_URL)
            await self.seed_users()
            await self.seed_roles()
            await self.seed_org()
            await self.seed_departments()
            await self.seed_employees()
            await self.seed_suppliers()
            await self.seed_esg()
            await self.seed_compliance()
            await self.seed_tokens()
            await self.seed_work_logs()
            await self.seed_redemptions()
            await self.seed_templates()
            log.info("=== GreenPlate seed complete ===")


if __name__ == "__main__":
    asyncio.run(Seeder().run())
