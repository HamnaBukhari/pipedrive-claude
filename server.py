import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pipedrive import PipedriveClient

load_dotenv()

mcp = FastMCP("pipedrive")
client = PipedriveClient()


# ── Formatters ─────────────────────────────────────────────────────────────────

def _str(val) -> str:
    return str(val) if val is not None else "—"


def _email(p: dict) -> str:
    emails = p.get("email") or []
    if isinstance(emails, list) and emails:
        return emails[0].get("value", "—")
    return str(emails) if emails else "—"


def _phone(p: dict) -> str:
    phones = p.get("phone") or []
    if isinstance(phones, list) and phones:
        return phones[0].get("value", "—")
    return str(phones) if phones else "—"


def _org_name(d: dict) -> str:
    org = d.get("org_id") or d.get("org_name") or d.get("organization")
    if isinstance(org, dict):
        return org.get("name", "—")
    return str(org) if org else "—"


def _person_name(d: dict) -> str:
    p = d.get("person_id") or d.get("person_name") or d.get("person")
    if isinstance(p, dict):
        return p.get("name", "—")
    return str(p) if p else "—"


def format_deal(d: dict) -> str:
    value = d.get("value")
    currency = d.get("currency", "")
    value_str = f"{value:,.0f} {currency}" if value is not None else "—"

    stage = d.get("stage_id")
    stage_name = "—"
    if isinstance(d.get("stage_id"), dict):
        stage_name = d["stage_id"].get("name", "—")
    elif d.get("stage_name"):
        stage_name = d["stage_name"]

    lines = [
        f"Deal #{d.get('id')}: {d.get('title', '—')}",
        f"  Value: {value_str} | Stage: {stage_name} | Status: {d.get('status', '—')}",
        f"  Contact: {_person_name(d)} | Org: {_org_name(d)}",
        f"  Created: {_str(d.get('add_time', '—')[:10] if d.get('add_time') else '—')}",
    ]
    return "\n".join(lines)


def format_person(p: dict) -> str:
    lines = [
        f"Person #{p.get('id')}: {p.get('name', '—')}",
        f"  Email: {_email(p)} | Phone: {_phone(p)}",
        f"  Org: {_org_name(p)}",
    ]
    return "\n".join(lines)


def format_organization(o: dict) -> str:
    lines = [
        f"Organization #{o.get('id')}: {o.get('name', '—')}",
        f"  Address: {_str(o.get('address') or '—')}",
        f"  People: {_str(o.get('people_count', '—'))} | Open deals: {_str(o.get('open_deals_count', '—'))}",
    ]
    return "\n".join(lines)


def format_activity(a: dict) -> str:
    done = "Done" if a.get("done") else "Pending"
    lines = [
        f"Activity #{a.get('id')}: {a.get('subject', '—')}",
        f"  Type: {a.get('type', '—')} | Status: {done}",
        f"  Due: {a.get('due_date', '—')} {a.get('due_time', '') or ''}".rstrip(),
        f"  Deal: {_str(a.get('deal_id') or '—')} | Contact: {_str(a.get('person_id') or '—')}",
    ]
    if a.get("note"):
        lines.append(f"  Note: {a['note']}")
    return "\n".join(lines)


def format_note(n: dict) -> str:
    content = n.get("content", "—")
    lines = [
        f"Note #{n.get('id')} — {n.get('add_time', '—')[:10] if n.get('add_time') else '—'}",
        f"  {content}",
    ]
    return "\n".join(lines)


def format_lead(l: dict) -> str:
    lines = [
        f"Lead #{l.get('id')}: {l.get('title', '—')}",
        f"  Contact: {_str(l.get('person_id') or '—')} | Org: {_str(l.get('organization_id') or '—')}",
    ]
    return "\n".join(lines)


def format_pipeline(p: dict) -> str:
    return f"Pipeline #{p.get('id')}: {p.get('name', '—')} | Active: {p.get('active', '—')}"


def format_stage(s: dict) -> str:
    return (
        f"Stage #{s.get('id')}: {s.get('name', '—')} "
        f"| Pipeline: {s.get('pipeline_id', '—')} | Order: {s.get('order_nr', '—')}"
    )


def _join(items: list, fmt_fn) -> str:
    if not items:
        return "No results found."
    return "\n\n".join(fmt_fn(i) for i in items)


# ── Deal tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
async def list_deals(status: str = "open", limit: int = 20) -> str:
    """List deals from Pipedrive. Status can be: open, won, lost, all."""
    try:
        deals = await client.get_deals(status=status, limit=limit)
        return _join(deals, format_deal)
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def get_deal(deal_id: int) -> str:
    """Get full details of a specific deal by ID."""
    try:
        deal = await client.get_deal(deal_id)
        return format_deal(deal)
    except LookupError:
        return f"Not found: deal #{deal_id} does not exist in Pipedrive."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def create_deal(
    title: str,
    value: float = None,
    currency: str = "DKK",
    person_id: int = None,
    org_id: int = None,
    stage_id: int = None,
) -> str:
    """Create a new deal in Pipedrive."""
    try:
        deal = await client.create_deal(
            title=title,
            value=value,
            currency=currency,
            person_id=person_id,
            org_id=org_id,
            stage_id=stage_id,
        )
        return f"Deal created successfully.\n\n{format_deal(deal)}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def update_deal(
    deal_id: int,
    title: str = None,
    value: float = None,
    status: str = None,
    stage_id: int = None,
) -> str:
    """Update an existing deal. Only pass the fields you want to change."""
    try:
        fields = {}
        if title is not None:
            fields["title"] = title
        if value is not None:
            fields["value"] = value
        if status is not None:
            fields["status"] = status
        if stage_id is not None:
            fields["stage_id"] = stage_id
        deal = await client.update_deal(deal_id, **fields)
        return f"Deal updated successfully.\n\n{format_deal(deal)}"
    except LookupError:
        return f"Not found: deal #{deal_id} does not exist in Pipedrive."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def search_deals(term: str) -> str:
    """Search for deals by name or keyword."""
    try:
        results = await client.search_deals(term)
        if not results:
            return f"No deals found matching '{term}'."
        items = [r.get("item", r) for r in results]
        return _join(items, format_deal)
    except Exception as e:
        return f"Error: {e}"


# ── Contact (Person) tools ──────────────────────────────────────────────────────

@mcp.tool()
async def list_contacts(limit: int = 20) -> str:
    """List persons/contacts in Pipedrive."""
    try:
        persons = await client.get_persons(limit=limit)
        return _join(persons, format_person)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def get_contact(person_id: int) -> str:
    """Get full details of a specific contact/person."""
    try:
        person = await client.get_person(person_id)
        return format_person(person)
    except LookupError:
        return f"Not found: person #{person_id} does not exist in Pipedrive."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def create_contact(
    name: str, email: str = None, phone: str = None, org_id: int = None
) -> str:
    """Create a new contact/person in Pipedrive."""
    try:
        person = await client.create_person(
            name=name, email=email, phone=phone, org_id=org_id
        )
        return f"Contact created successfully.\n\n{format_person(person)}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def search_contacts(term: str) -> str:
    """Search for a contact by name, email, or phone."""
    try:
        results = await client.search_persons(term)
        if not results:
            return f"No contacts found matching '{term}'."
        items = [r.get("item", r) for r in results]
        return _join(items, format_person)
    except Exception as e:
        return f"Error: {e}"


# ── Organization tools ─────────────────────────────────────────────────────────

@mcp.tool()
async def list_organizations(limit: int = 20) -> str:
    """List organizations in Pipedrive."""
    try:
        orgs = await client.get_organizations(limit=limit)
        return _join(orgs, format_organization)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def create_organization(name: str, address: str = None) -> str:
    """Create a new organization in Pipedrive."""
    try:
        org = await client.create_organization(name=name, address=address)
        return f"Organization created successfully.\n\n{format_organization(org)}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def search_organizations(term: str) -> str:
    """Search for an organization by name."""
    try:
        results = await client.search_organizations(term)
        if not results:
            return f"No organizations found matching '{term}'."
        items = [r.get("item", r) for r in results]
        return _join(items, format_organization)
    except Exception as e:
        return f"Error: {e}"


# ── Activity tools ─────────────────────────────────────────────────────────────

@mcp.tool()
async def list_activities(done: int = 0) -> str:
    """List activities. done=0 for pending, done=1 for completed."""
    try:
        activities = await client.get_activities(done=done)
        return _join(activities, format_activity)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def create_activity(
    subject: str,
    type: str,
    due_date: str = None,
    due_time: str = None,
    deal_id: int = None,
    person_id: int = None,
    note: str = None,
) -> str:
    """
    Create an activity (task, call, meeting, email, etc.).
    type must be one of: call, meeting, task, deadline, email, lunch.
    due_date format: YYYY-MM-DD. due_time format: HH:MM.
    """
    try:
        activity = await client.create_activity(
            subject=subject,
            type=type,
            due_date=due_date,
            due_time=due_time,
            deal_id=deal_id,
            person_id=person_id,
            note=note,
        )
        return f"Activity created successfully.\n\n{format_activity(activity)}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def complete_activity(activity_id: int) -> str:
    """Mark an activity as done/completed."""
    try:
        activity = await client.mark_activity_done(activity_id)
        return f"Activity marked as done.\n\n{format_activity(activity)}"
    except LookupError:
        return f"Not found: activity #{activity_id} does not exist in Pipedrive."
    except Exception as e:
        return f"Error: {e}"


# ── Note tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
async def add_note(
    content: str,
    deal_id: int = None,
    person_id: int = None,
    org_id: int = None,
) -> str:
    """Add a note to a deal, contact, or organization."""
    try:
        note = await client.create_note(
            content=content, deal_id=deal_id, person_id=person_id, org_id=org_id
        )
        return f"Note added successfully.\n\n{format_note(note)}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def get_notes(deal_id: int = None, person_id: int = None) -> str:
    """Get notes for a deal or contact."""
    try:
        notes = await client.get_notes(deal_id=deal_id, person_id=person_id)
        return _join(notes, format_note)
    except Exception as e:
        return f"Error: {e}"


# ── Lead tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
async def list_leads(limit: int = 20) -> str:
    """List leads in Pipedrive."""
    try:
        leads = await client.get_leads(limit=limit)
        return _join(leads, format_lead)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def create_lead(
    title: str, person_id: int = None, org_id: int = None
) -> str:
    """Create a new lead in Pipedrive."""
    try:
        lead = await client.create_lead(
            title=title, person_id=person_id, org_id=org_id
        )
        return f"Lead created successfully.\n\n{format_lead(lead)}"
    except Exception as e:
        return f"Error: {e}"


# ── Pipeline & Stage tools ──────────────────────────────────────────────────────

@mcp.tool()
async def list_pipelines() -> str:
    """List all sales pipelines."""
    try:
        pipelines = await client.get_pipelines()
        return _join(pipelines, format_pipeline)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def list_stages(pipeline_id: int = None) -> str:
    """List stages. Optionally filter by pipeline_id."""
    try:
        stages = await client.get_stages(pipeline_id=pipeline_id)
        return _join(stages, format_stage)
    except Exception as e:
        return f"Error: {e}"


# ── Global search ───────────────────────────────────────────────────────────────

@mcp.tool()
async def search_pipedrive(
    term: str, types: str = "deal,person,organization"
) -> str:
    """
    Search across Pipedrive for any entity.
    types is a comma-separated list of: deal, person, organization, lead, product.
    """
    try:
        item_types = [t.strip() for t in types.split(",") if t.strip()]
        results = await client.search(term, item_types=item_types)
        if not results:
            return f"No results found for '{term}'."

        lines = []
        for r in results:
            item = r.get("item", r)
            result_type = item.get("type", r.get("result_type", "unknown"))
            if result_type == "deal":
                lines.append(format_deal(item))
            elif result_type == "person":
                lines.append(format_person(item))
            elif result_type == "organization":
                lines.append(format_organization(item))
            else:
                lines.append(f"{result_type.title()} #{item.get('id')}: {item.get('title') or item.get('name', '—')}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
