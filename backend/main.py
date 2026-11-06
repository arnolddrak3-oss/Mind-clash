"""API de Mind Clasher : contacts importés + superagent."""

import os
import sqlite3

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

import agent
import importer

DATABASE_PATH = os.environ.get("DATABASE_PATH", "/data/contacts.db")

app = FastAPI(title="Mind Clasher API")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _init_db() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                company TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


_init_db()


def _row_to_contact(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in ("id", "name", "email", "phone", "company", "tags")}


def _all_contacts() -> list:
    with _connect() as connection:
        rows = connection.execute("SELECT * FROM contacts ORDER BY name COLLATE NOCASE").fetchall()
    return [_row_to_contact(row) for row in rows]


class ChatIn(BaseModel):
    message: str


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/contacts")
def list_contacts() -> dict:
    contacts = _all_contacts()
    return {"contacts": contacts, "total": len(contacts)}


@app.post("/api/contacts/import")
async def import_contacts(file: UploadFile = File(...)) -> dict:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Le fichier est vide.")

    try:
        parsed = importer.parse_contacts(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Impossible de lire ce fichier de contacts.")

    if not parsed:
        raise HTTPException(
            status_code=400,
            detail="Aucun contact trouvé. Utilise un CSV avec une colonne nom (ou email) ou un fichier vCard.",
        )

    existing = {
        (row["email"].strip().lower(), row["name"].strip().lower(), row["phone"].strip())
        for row in _all_contacts()
    }

    imported = 0
    skipped = 0
    with _connect() as connection:
        for contact in parsed:
            key = (
                contact["email"].strip().lower(),
                contact["name"].strip().lower(),
                contact["phone"].strip(),
            )
            # Doublon : même email, ou même nom + même téléphone.
            is_duplicate = any(
                (key[0] and key[0] == stored[0]) or (key[1] and key[1] == stored[1] and key[2] and key[2] == stored[2])
                for stored in existing
            )
            if is_duplicate:
                skipped += 1
                continue
            connection.execute(
                "INSERT INTO contacts (name, email, phone, company, tags) VALUES (?, ?, ?, ?, ?)",
                (contact["name"], contact["email"], contact["phone"], contact["company"], contact["tags"]),
            )
            existing.add(key)
            imported += 1

    total = len(_all_contacts())
    return {"imported": imported, "skipped": skipped, "total": total}


@app.delete("/api/contacts/{contact_id}")
def delete_contact(contact_id: int) -> dict:
    with _connect() as connection:
        cursor = connection.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Contact introuvable.")
    return {"deleted": contact_id}


@app.post("/api/agent/chat")
def chat(payload: ChatIn) -> dict:
    question = payload.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Pose-moi une question sur tes contacts.")
    return agent.answer(question, _all_contacts())
