"""Superagent de Mind Clasher : répond aux questions à partir des contacts importés."""

import os

import httpx

SYSTEM_PROMPT = (
    "Tu es le superagent de Mind Clasher. Tu réponds en français, de façon concise, "
    "en t'appuyant uniquement sur les contacts fournis ci-dessous. "
    "Si l'information n'est pas dans les contacts, dis-le clairement.\n\n"
    "Contacts :\n{contacts}"
)


def _norm(text: str) -> str:
    """Minuscule sans accents, pour comparer les intentions des questions."""
    import unicodedata

    text = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _line(contact: dict) -> str:
    details = [
        contact.get(key)
        for key in ("email", "phone", "company", "tags")
        if contact.get(key)
    ]
    name = contact.get("name") or "(sans nom)"
    return f"- {name}" + (f" — {', '.join(details)}" if details else "")


def _listing(contacts: list) -> str:
    return "\n".join(_line(c) for c in contacts)


def _matches(question: str, contacts: list) -> tuple:
    """Mots utiles de la question, et les contacts qui en contiennent un."""
    stopwords = {
        "les", "des", "mes", "mon", "mes", "qui", "que", "quoi", "quel", "quelle",
        "dans", "chez", "pour", "avec", "sont", "est", "the", "and", "list",
        "liste", "trouve", "cherche", "contact", "contacts", "travaille", "quelqu",
    }
    words = [w for w in _norm(question).replace("?", " ").split() if len(w) > 2 and w not in stopwords]
    found = []
    for contact in contacts:
        haystack = _norm(" ".join(str(contact.get(k) or "") for k in ("name", "email", "phone", "company", "tags")))
        if any(word in haystack for word in words):
            found.append(contact)
    return words, found


def local_answer(question: str, contacts: list) -> str:
    """Réponse calculée localement, sans appel à un modèle externe."""
    if not contacts:
        return (
            "Je n'ai encore aucun contact. Importe un fichier CSV ou vCard "
            "dans le panneau de gauche et je pourrai travailler dessus."
        )

    q = _norm(question)

    if any(word in q for word in ("combien", "nombre", "total", "count")):
        total = len(contacts)
        suffix = "" if total <= 1 else "s"
        return f"Tu as {total} contact{suffix} enregistré{suffix}."

    if any(word in q for word in ("doublon", "doublons", "duplicat")):
        groups = {}
        for contact in contacts:
            key = _norm(contact.get("email") or contact.get("name") or "")
            if key:
                groups.setdefault(key, []).append(contact)
        duplicates = {k: v for k, v in groups.items() if len(v) > 1}
        if not duplicates:
            return "Aucun doublon détecté : chaque contact a un email ou un nom unique."
        lines = [f"{len(duplicates)} doublon(s) détecté(s) :"]
        for group in duplicates.values():
            lines.append(f"- {group[0].get('name')} ({len(group)} entrées identiques)")
        return "\n".join(lines)

    if "sans" in q or "manque" in q or "incomplet" in q:
        field = None
        if any(word in q for word in ("email", "mail", "courriel")):
            field = "email"
        elif any(word in q for word in ("telephone", "tel", "phone", "numero", "mobile")):
            field = "phone"
        if field:
            missing = [c for c in contacts if not c.get(field)]
            label = "email" if field == "email" else "téléphone"
            if not missing:
                return f"Tous tes contacts ont un {label}. Rien à compléter."
            return f"{len(missing)} contact(s) sans {label} :\n" + "\n".join(_line(c) for c in missing)

    if any(word in q for word in ("entreprise", "societe", "company", "boite")):
        counts = {}
        for contact in contacts:
            company = contact.get("company") or "Sans entreprise"
            counts[company] = counts.get(company, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        body = "\n".join(f"- {company} : {count} contact(s)" for company, count in ranked)
        return f"Répartition par entreprise ({len(contacts)} contacts) :\n{body}"

    words, found = _matches(question, contacts)
    if words and found:
        return f"{len(found)} contact(s) correspondent :\n" + _listing(found)
    if words:
        return (
            f"Aucun contact ne correspond à « {question.strip()} ». "
            f"Tes {len(contacts)} contacts sont là, mais rien ne remonte sur ces mots."
        )

    companies = {c.get("company") for c in contacts if c.get("company")}
    return (
        f"J'ai bien {len(contacts)} contacts connectés, répartis sur {len(companies) or 1} entreprise(s). "
        "Demande-moi par exemple « combien de contacts », « les doublons », "
        "« qui travaille chez X » ou « les contacts sans email »."
    )


def _llm_answer(question: str, contacts: list) -> str | None:
    """Utilise un modèle externe si une clé est configurée, sinon None."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT.format(contacts=_listing(contacts[:300]))},
            {"role": "user", "content": question},
        ],
    }
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def answer(question: str, contacts: list) -> dict:
    reply = _llm_answer(question, contacts)
    if reply:
        return {"answer": reply, "mode": "llm"}
    return {"answer": local_answer(question, contacts), "mode": "local"}
