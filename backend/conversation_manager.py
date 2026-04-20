import json
import logging
from typing import Any

import httpx

from models import Message
from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Chocomi, a customer support AI for ByteBodega.
                Your goal is to be helpful, strictly concise, and only answer questions about the provided inventory and polices.
                <CRITICAL_RULES>
                1. CONCISENESS: Your responses MUST be 1 to 3 sentences long. NEVER write more than 4 paragraphs.
                2. TONE: You must introduce yourself as "Chocomi" in your first message.
                3. DOMAIN RESTRICTION: You are NOT a general AI. If a user asks about anything other than PC hardware, you MUST reply EXACTLY with: "I can only assist with PC hardware and ByteBodega services."
                4. MISSING ITEMS: If a user asks for a product NOT listed in the <INVENTORY> section below, you MUST reply EXACTLY with: "I'd recommend calling us at +1 (555) 010-4090 or visiting the store to check availability."
                5. NO HALLUCINATION: Only quote prices and stock from the <INVENTORY> section.
                </CRITICAL_RULES>
                <STORE_INFO>
                Location: 127 Byte Street, Downtown Tech District
                Contact: +1 (555) 010-4090
                Hours: Mon-Sat 10AM-8PM | Sun 11AM-5PM
                </STORE_INFO>
                <POLICIES>
                Returns: Unopened items returnable within 14 days with receipt.
                Warranty: Final approval requires in-store diagnostics.
                </POLICIES>
                <INVENTORY>
                [GPUs]
                NVIDIA RTX 4060 8GB: $329 (12 in stock)
                NVIDIA RTX 4070 Super: $589 (6 in stock)
                AMD RX 7700 XT 12GB: $419 (9 in stock)
                [CPUs]
                Intel Core i5-14400F: $209 (19 in stock)
                AMD Ryzen 7 7700: $299 (11 in stock)
                [Motherboards]
                MSI B650 Tomahawk WiFi: $219 (7 in stock)
                [RAM]
                Corsair Vengeance DDR5 32GB: $109 (16 in stock)
                [Storage]
                WD Black SN850X 1TB: $99 (26 in stock)
                Samsung 990 Pro 2TB: $169 (8 in stock)
                [PSU]
                Corsair RM750e: $109 (5 in stock)
                [Cooling]
                DeepCool AK620 Cooler: $59 (14 in stock)
                Arctic P12 Fan 5-Pack: $34 (22 in stock)
                </INVENTORY>
                <EXAMPLES>
                User: Hello there! I need help with my PC.
                Assistant: Hello! I am Chocomi, your ByteBodega assistant. How can I help you regarding PC hardware today?

                User: Do you have the Corsair Vengeance DDR5 32GB in stock? How much?
                Assistant: Yes, we have the Corsair Vengeance DDR5 32GB in stock! The price is $109, and we currently have 16 in stock.

                User: Do you sell the Intel Arc A770 GPU?
                Assistant: I'd recommend calling us at +1 (555) 010-4090 or visiting the store to check availability.

                User: How do I bake a chocolate cake?
                Assistant: I can only assist with PC hardware and ByteBodega services.
                </EXAMPLES>
                """

SIGNAL_KEYWORDS: list[str] = [
    "gpu", "cpu", "ram", "ssd", "psu", "motherboard", "case", "cooling",
    "budget", "build", "warranty", "return", "rma", "broken", "faulty",
    "price", "stock", "compatible", "install", "error", "boot", "post",
    "driver", "monitor", "keyboard", "mouse", "peripheral", "upgrade"
]

class ConversationSession:
    def __init__(self):
        self._history: list[Message] = []
        self._turnCounter = 0
        # In-memory only: no files, no persistence across server restarts.
        self._memory: dict[str, Any] = {
            "summary": "",
            "facts": [],
        }

    async def ingestUserTurn(self, content: str):
        """
        Add the raw user message and update in-memory structured memory.
        This is intentionally in-memory only (no CRM persistence).
        """
        self.addUserTurn(content)
        self._turnCounter += 1
        await self._updateMemoryFromUserTurn(content)

    def addUserTurn(self, content: str):
        self._history.append(Message(role="user", content=content))

    def addAssistantTurn(self, content: str):
        self._history.append(Message(role="assistant", content=content))

    def buildMessages(self) -> list[dict]:
        trimmed = self._trimHistory()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        memoryContext = self._buildMemoryContext()
        if memoryContext:
            messages.append({"role": "system", "content": memoryContext})
        messages.extend({"role": m.role, "content": m.content} for m in trimmed)
        return messages

    # Backward compatibility for older call sites/tests.
    def build_messages(self) -> list[dict]:
        return self.buildMessages()

    async def _updateMemoryFromUserTurn(self, userText: str):
        """
        Update memory using LLM-assisted extraction with conflict/version handling.
        If extraction fails, keep the previous memory unchanged.
        """
        currentMemoryJson = json.dumps(self._memory, ensure_ascii=True)
        prompt = f"""You are a strict JSON memory updater.
                Update the in-memory conversation facts using the NEW user message.

                Rules:
                - Return ONLY valid JSON, no markdown.
                - Keep schema exactly:
                {{
                    "summary": "short running summary (max 80 words)",
                    "facts": [
                    {{
                        "id": "stable-short-id",
                        "type": "product|constraint|preference|issue|decision|contact|other",
                        "key": "short-key",
                        "value": "fact value",
                        "priority": "high|medium|low",
                        "status": "active|superseded|rejected|uncertain",
                        "updated_turn": {self._turnCounter}
                    }}
                    ]
                }}
                - If new message conflicts with existing active fact of same key/type, mark older one as "superseded" and keep new one "active".
                - If user explicitly rejects a previous preference/decision, mark old fact "rejected".
                - Keep only useful support-domain facts.

                Current memory JSON:
                {currentMemoryJson}

                New user message:
                {userText}
                """

        url = f"{settings.ollamaBaseUrl}/api/chat"
        payload = {
            "model": settings.ollamaModel,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0},
        }

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                content = res.json().get("message", {}).get("content", "")

            parsed = self._parseMemoryJson(content)
            if parsed is not None:
                self._memory = self._normalizeMemory(parsed)
        except Exception as exc:
            logger.warning("Memory extraction failed; retaining previous memory: %s", exc)

    def _parseMemoryJson(self, rawContent: str) -> dict[str, Any] | None:
        # Handle plain JSON or JSON wrapped in markdown fences.
        text = rawContent.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            value = json.loads(text)
            if isinstance(value, dict):
                return value
        except Exception:
            return None
        return None

    def _normalizeMemory(self, memoryObj: dict[str, Any]) -> dict[str, Any]:
        summary = memoryObj.get("summary", "")
        facts = memoryObj.get("facts", [])

        if not isinstance(summary, str):
            summary = ""
        if not isinstance(facts, list):
            facts = []

        normalized: list[dict[str, Any]] = []
        for idx, fact in enumerate(facts):
            if not isinstance(fact, dict):
                continue
            normalized.append(
                {
                    "id": str(fact.get("id", f"fact-{idx}")),
                    "type": str(fact.get("type", "other")),
                    "key": str(fact.get("key", "unknown")),
                    "value": str(fact.get("value", "")),
                    "priority": str(fact.get("priority", "medium")),
                    "status": str(fact.get("status", "active")),
                    "updated_turn": int(fact.get("updated_turn", self._turnCounter)),
                }
            )

        # Keep top facts compactly: active first, then by priority and recency.
        priorityOrder = {"high": 3, "medium": 2, "low": 1}
        statusOrder = {"active": 3, "uncertain": 2, "superseded": 1, "rejected": 0}
        normalized.sort(
            key=lambda f: (
                statusOrder.get(f["status"], 0),
                priorityOrder.get(f["priority"], 1),
                f["updated_turn"],
            ),
            reverse=True,
        )

        # Hard cap memory facts to avoid context bloat.
        return {
            "summary": summary[:800],
            "facts": normalized[:24],
        }

    def _buildMemoryContext(self) -> str:
        summary = self._memory.get("summary", "")
        facts = self._memory.get("facts", [])
        if not summary and not facts:
            return ""

        activeFacts = [f for f in facts if f.get("status") in {"active", "uncertain"}]
        activeFacts = activeFacts[:12]

        lines: list[str] = [
            "<RUNNING_MEMORY>",
            f"Summary: {summary}" if summary else "Summary:",
            "Active Facts:",
        ]
        for fact in activeFacts:
            lines.append(
                f"- [{fact.get('type')}] {fact.get('key')}: {fact.get('value')}"
                f" (priority={fact.get('priority')}, status={fact.get('status')})"
            )
        lines.append("</RUNNING_MEMORY>")
        return "\n".join(lines)

    def _isHighSignal(self, msg: Message) -> bool:
        lowerContent = msg.content.lower()
        return any(keyword in lowerContent for keyword in SIGNAL_KEYWORDS)

    def _trimHistory(self) -> list[Message]:
        if not self._history:
            return []

        # split into pairs (user + assistant)
        pairs: list[tuple[Message, Message | None]] = []
        i = 0
        while i < len(self._history):
            userMsg = self._history[i]
            assistantMsg = self._history[i + 1] if i + 1 < len(self._history) else None
            pairs.append((userMsg, assistantMsg))
            i += 2

        # always keep last N pairs
        recentPairs = pairs[-settings.maxRecentPairs:]
        middlePairs = pairs[:-settings.maxRecentPairs]

        # from middle, only keep high signal pairs
        highSignalPairs = [
            p for p in middlePairs
            if self._isHighSignal(p[0]) or (p[1] and self._isHighSignal(p[1]))
        ][-settings.maxMiddlePairs:]

        # flatten back to messages
        keptMessages: list[Message] = []
        for userMsg, assistantMsg in (highSignalPairs + recentPairs):
            keptMessages.append(userMsg)
            if assistantMsg:
                keptMessages.append(assistantMsg)

        # hard char cap as final safety net
        result: list[Message] = []
        totalChars = 0
        for msg in reversed(keptMessages):
            totalChars += len(msg.content)
            if totalChars > settings.maxTotalChars:
                break
            result.insert(0, msg)

        return result