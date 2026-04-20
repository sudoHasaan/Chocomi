import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any


CRM_FILE_PATH = Path(__file__).parent / "crm_data.json"
_LOCK = threading.Lock()


def _utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _read_all() -> dict[str, Any]:
    if not CRM_FILE_PATH.exists():
        return {"users": {}}
    try:
        raw = CRM_FILE_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, dict) and isinstance(data.get("users"), dict):
            return data
    except Exception:
        pass
    return {"users": {}}


def _write_all(data: dict[str, Any]) -> None:
    CRM_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CRM_FILE_PATH.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def get_user_info(user_id: str) -> dict[str, Any]:
    uid = (user_id or "anonymous").strip() or "anonymous"
    with _LOCK:
        data = _read_all()
        users = data.get("users", {})
        user = users.get(uid)
        if not isinstance(user, dict):
            return {
                "user_id": uid,
                "profile": {
                    "name": "",
                    "email": "",
                    "phone": "",
                    "preferences": "",
                    "notes": "",
                },
                "history": [],
                "updated_at": "",
            }
        return {
            "user_id": uid,
            "profile": user.get("profile", {}),
            "history": user.get("history", [])[-10:],
            "updated_at": user.get("updated_at", ""),
        }


def store_user_info(
    user_id: str,
    name: str = "",
    email: str = "",
    phone: str = "",
    preferences: str = "",
    notes: str = "",
) -> dict[str, Any]:
    uid = (user_id or "anonymous").strip() or "anonymous"
    with _LOCK:
        data = _read_all()
        users = data.setdefault("users", {})
        user = users.setdefault(uid, {"profile": {}, "history": []})
        profile = user.setdefault("profile", {})

        if name:
            profile["name"] = name
        if email:
            profile["email"] = email
        if phone:
            profile["phone"] = phone
        if preferences:
            profile["preferences"] = preferences
        if notes:
            profile["notes"] = notes

        user.setdefault("history", []).append(
            {
                "ts": _utc_now(),
                "event": "store_user_info",
                "details": {"name": bool(name), "email": bool(email), "phone": bool(phone), "preferences": bool(preferences), "notes": bool(notes)},
            }
        )
        user["updated_at"] = _utc_now()
        _write_all(data)

        return {
            "status": "ok",
            "user_id": uid,
            "profile": profile,
            "updated_at": user["updated_at"],
        }


def update_user_info(user_id: str, field: str, value: str) -> dict[str, Any]:
    uid = (user_id or "anonymous").strip() or "anonymous"
    fld = (field or "").strip().lower()
    if fld not in {"name", "email", "phone", "preferences", "notes"}:
        return {"status": "error", "message": f"unsupported field '{field}'"}

    with _LOCK:
        data = _read_all()
        users = data.setdefault("users", {})
        user = users.setdefault(uid, {"profile": {}, "history": []})
        profile = user.setdefault("profile", {})

        profile[fld] = value
        user.setdefault("history", []).append(
            {
                "ts": _utc_now(),
                "event": "update_user_info",
                "details": {"field": fld},
            }
        )
        user["updated_at"] = _utc_now()
        _write_all(data)

        return {
            "status": "ok",
            "user_id": uid,
            "field": fld,
            "value": value,
            "updated_at": user["updated_at"],
        }


def add_interaction(user_id: str, interaction: str) -> None:
    uid = (user_id or "anonymous").strip() or "anonymous"
    text = (interaction or "").strip()
    if not text:
        return
    with _LOCK:
        data = _read_all()
        users = data.setdefault("users", {})
        user = users.setdefault(uid, {"profile": {}, "history": []})
        history = user.setdefault("history", [])
        history.append({"ts": _utc_now(), "event": "interaction", "details": text[:240]})
        if len(history) > 100:
            user["history"] = history[-100:]
        user["updated_at"] = _utc_now()
        _write_all(data)
