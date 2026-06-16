import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.pipedrive.com/v1"


class PipedriveClient:
    def __init__(self):
        self.token = os.environ.get("PIPEDRIVE_API_TOKEN")
        if not self.token:
            raise ValueError(
                "PIPEDRIVE_API_TOKEN environment variable is not set. See .env.example."
            )

    def _params(self, **extra) -> dict:
        return {"api_token": self.token, **extra}

    async def _get(self, path: str, **params) -> dict | list:
        async with httpx.AsyncClient() as http:
            r = await http.get(
                f"{BASE_URL}{path}", params=self._params(**params), timeout=30
            )
            return self._handle(r)

    async def _post(self, path: str, body: dict) -> dict:
        async with httpx.AsyncClient() as http:
            r = await http.post(
                f"{BASE_URL}{path}",
                params=self._params(),
                json={k: v for k, v in body.items() if v is not None},
                timeout=30,
            )
            return self._handle(r)

    async def _put(self, path: str, body: dict) -> dict:
        async with httpx.AsyncClient() as http:
            r = await http.put(
                f"{BASE_URL}{path}",
                params=self._params(),
                json={k: v for k, v in body.items() if v is not None},
                timeout=30,
            )
            return self._handle(r)

    def _handle(self, r: httpx.Response) -> dict | list:
        if r.status_code == 401:
            raise ValueError("Authentication failed. Check your PIPEDRIVE_API_TOKEN.")
        if r.status_code == 404:
            raise LookupError(f"Resource not found (404): {r.url}")
        if r.status_code == 429:
            raise RuntimeError("Rate limited (429)")
        if r.status_code >= 400:
            try:
                msg = r.json().get("error", r.text)
            except Exception:
                msg = r.text
            raise RuntimeError(f"Pipedrive API error {r.status_code}: {msg}")
        data = r.json()
        if not data.get("success"):
            raise ValueError(f"Pipedrive returned success=false: {data.get('error', data)}")
        return data.get("data") or []

    async def _get_with_retry(self, path: str, **params):
        try:
            return await self._get(path, **params)
        except RuntimeError as e:
            if "429" in str(e):
                await asyncio.sleep(1)
                return await self._get(path, **params)
            raise

    # ── Deals ──────────────────────────────────────────────────────────────

    async def get_deals(self, status="open", limit=20, start=0) -> list[dict]:
        return await self._get_with_retry("/deals", status=status, limit=limit, start=start)

    async def get_deal(self, deal_id: int) -> dict:
        return await self._get(f"/deals/{deal_id}")

    async def create_deal(
        self,
        title: str,
        value: float = None,
        currency: str = "DKK",
        person_id: int = None,
        org_id: int = None,
        stage_id: int = None,
        status: str = "open",
    ) -> dict:
        return await self._post(
            "/deals",
            {
                "title": title,
                "value": value,
                "currency": currency,
                "person_id": person_id,
                "org_id": org_id,
                "stage_id": stage_id,
                "status": status,
            },
        )

    async def update_deal(self, deal_id: int, **fields) -> dict:
        return await self._put(f"/deals/{deal_id}", fields)

    async def search_deals(self, term: str, limit=10) -> list[dict]:
        data = await self._get(
            "/deals/search", term=term, limit=limit, fields="title"
        )
        if isinstance(data, dict):
            return data.get("items", [])
        return data or []

    # ── Persons ────────────────────────────────────────────────────────────

    async def get_persons(self, limit=20, start=0) -> list[dict]:
        return await self._get_with_retry("/persons", limit=limit, start=start)

    async def get_person(self, person_id: int) -> dict:
        return await self._get(f"/persons/{person_id}")

    async def create_person(
        self,
        name: str,
        email: str = None,
        phone: str = None,
        org_id: int = None,
    ) -> dict:
        body: dict = {"name": name}
        if email:
            body["email"] = [{"value": email, "primary": True}]
        if phone:
            body["phone"] = [{"value": phone, "primary": True}]
        if org_id:
            body["org_id"] = org_id
        return await self._post("/persons", body)

    async def search_persons(self, term: str, limit=10) -> list[dict]:
        data = await self._get(
            "/persons/search", term=term, limit=limit, fields="name,email,phone"
        )
        if isinstance(data, dict):
            return data.get("items", [])
        return data or []

    # ── Organizations ──────────────────────────────────────────────────────

    async def get_organizations(self, limit=20, start=0) -> list[dict]:
        return await self._get_with_retry("/organizations", limit=limit, start=start)

    async def get_organization(self, org_id: int) -> dict:
        return await self._get(f"/organizations/{org_id}")

    async def create_organization(self, name: str, address: str = None) -> dict:
        return await self._post("/organizations", {"name": name, "address": address})

    async def search_organizations(self, term: str, limit=10) -> list[dict]:
        data = await self._get(
            "/organizations/search", term=term, limit=limit, fields="name"
        )
        if isinstance(data, dict):
            return data.get("items", [])
        return data or []

    # ── Activities ─────────────────────────────────────────────────────────

    async def get_activities(self, done=0, limit=20) -> list[dict]:
        return await self._get_with_retry("/activities", done=done, limit=limit)

    async def create_activity(
        self,
        subject: str,
        type: str,
        due_date: str = None,
        due_time: str = None,
        duration: str = None,
        deal_id: int = None,
        person_id: int = None,
        note: str = None,
    ) -> dict:
        return await self._post(
            "/activities",
            {
                "subject": subject,
                "type": type,
                "due_date": due_date,
                "due_time": due_time,
                "duration": duration,
                "deal_id": deal_id,
                "person_id": person_id,
                "note": note,
            },
        )

    async def mark_activity_done(self, activity_id: int) -> dict:
        return await self._put(f"/activities/{activity_id}", {"done": 1})

    # ── Notes ──────────────────────────────────────────────────────────────

    async def create_note(
        self,
        content: str,
        deal_id: int = None,
        person_id: int = None,
        org_id: int = None,
    ) -> dict:
        return await self._post(
            "/notes",
            {
                "content": content,
                "deal_id": deal_id,
                "person_id": person_id,
                "org_id": org_id,
            },
        )

    async def get_notes(
        self, deal_id: int = None, person_id: int = None
    ) -> list[dict]:
        params: dict = {}
        if deal_id:
            params["deal_id"] = deal_id
        if person_id:
            params["person_id"] = person_id
        return await self._get("/notes", **params)

    # ── Leads ──────────────────────────────────────────────────────────────

    async def get_leads(self, limit=20, start=0) -> list[dict]:
        data = await self._get("/leads", limit=limit, start=start)
        if isinstance(data, dict):
            return data.get("items", data.get("data", []))
        return data or []

    async def create_lead(
        self,
        title: str,
        person_id: int = None,
        org_id: int = None,
        value: dict = None,
    ) -> dict:
        return await self._post(
            "/leads",
            {
                "title": title,
                "person_id": person_id,
                "organization_id": org_id,
                "value": value,
            },
        )

    # ── Pipelines & Stages ─────────────────────────────────────────────────

    async def get_pipelines(self) -> list[dict]:
        return await self._get("/pipelines")

    async def get_stages(self, pipeline_id: int = None) -> list[dict]:
        params = {}
        if pipeline_id:
            params["pipeline_id"] = pipeline_id
        return await self._get("/stages", **params)

    # ── Global search ──────────────────────────────────────────────────────

    async def search(
        self, term: str, item_types: list[str] = None, limit=10
    ) -> list[dict]:
        params: dict = {"term": term, "limit": limit}
        if item_types:
            params["item_types"] = ",".join(item_types)
        data = await self._get("/itemSearch", **params)
        if isinstance(data, dict):
            return data.get("items", [])
        return data or []
