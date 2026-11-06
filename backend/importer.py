"""Lecture des fichiers de contacts importés (CSV et vCard)."""

import csv
import io
import re
import unicodedata

HEADER_ALIASES = {
    "name": {"name", "nom", "full name", "fullname", "nom complet", "contact", "display name"},
    "first_name": {"first name", "firstname", "prenom", "given name"},
    "last_name": {"last name", "lastname", "nom de famille", "surname", "family name"},
    "email": {"email", "e-mail", "mail", "courriel", "adresse email", "email address"},
    "phone": {"phone", "tel", "telephone", "mobile", "portable", "phone number", "numero"},
    "company": {"company", "organisation", "organization", "entreprise", "societe", "société"},
    "tags": {"tags", "tag", "labels", "notes", "categorie", "catégorie"},
}


def _clean(value) -> str:
    return str(value or "").strip().strip('"').strip()


def _normalize_header(value: str) -> str:
    """Minuscule, sans accents : « Téléphone » et « telephone » se rejoignent."""
    text = unicodedata.normalize("NFD", _clean(value).lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn").replace("_", " ").strip()


_ALIAS_INDEX = {_normalize_header(alias): field for field, aliases in HEADER_ALIASES.items() for alias in aliases}


def _map_headers(row: list) -> dict:
    """Associe chaque colonne du fichier à un champ contact (ou None)."""
    mapping = {}
    for index, cell in enumerate(row):
        field = _ALIAS_INDEX.get(_normalize_header(cell))
        if field:
            mapping[index] = field
    return mapping


def _contact(name="", email="", phone="", company="", tags="") -> dict:
    return {
        "name": _clean(name),
        "email": _clean(email),
        "phone": _clean(phone),
        "company": _clean(company),
        "tags": _clean(tags),
    }


def _parse_vcards(text: str) -> list:
    contacts = []
    for block in re.split(r"BEGIN:VCARD", text, flags=re.IGNORECASE)[1:]:
        block = re.split(r"END:VCARD", block, flags=re.IGNORECASE)[0]
        fields = {}
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line or ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.split(";")[0].split(".")[-1].upper()
            value = _clean(value)
            if key == "FN":
                fields["name"] = value
            elif key == "N" and not fields.get("name"):
                parts = [p for p in value.split(";") if p]
                fields["name"] = " ".join(reversed(parts[:2]))
            elif key == "EMAIL" and not fields.get("email"):
                fields["email"] = value
            elif key == "TEL" and not fields.get("phone"):
                fields["phone"] = value
            elif key == "ORG" and not fields.get("company"):
                fields["company"] = value.replace(";", " ").strip()
        contact = _contact(**{k: v for k, v in fields.items() if k in _contact()})
        if contact["name"] or contact["email"] or contact["phone"]:
            contacts.append(contact)
    return contacts


def _parse_csv(text: str) -> list:
    sample = text[:2000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    rows = [row for row in csv.reader(io.StringIO(text), delimiter=delimiter) if any(_clean(c) for c in row)]
    if not rows:
        return []

    mapping = _map_headers(rows[0])
    has_header = bool(mapping)
    if has_header:
        rows = rows[1:]
    else:
        # Pas d'en-tête reconnu : on suppose nom, email, téléphone, entreprise.
        positional = ["name", "email", "phone", "company", "tags"]
        mapping = {i: field for i, field in enumerate(positional)}

    contacts = []
    for row in rows:
        values = {field: row[i] if i < len(row) else "" for i, field in mapping.items()}
        if "first_name" in values or "last_name" in values:
            full = f"{values.pop('first_name', '')} {values.pop('last_name', '')}".strip()
            values["name"] = values.get("name") or full
        contact = _contact(**{k: v for k, v in values.items() if k in _contact()})
        if contact["name"] or contact["email"] or contact["phone"]:
            contacts.append(contact)
    return contacts


def parse_contacts(raw: bytes) -> list:
    """Retourne la liste des contacts trouvés dans un fichier CSV ou vCard."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    if "BEGIN:VCARD" in text.upper():
        return _parse_vcards(text)
    return _parse_csv(text)
