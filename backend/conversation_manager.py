from models import Message
from config import settings

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

    def addUserTurn(self, content: str):
        self._history.append(Message(role="user", content=content))

    def addAssistantTurn(self, content: str):
        self._history.append(Message(role="assistant", content=content))

    def buildMessages(self) -> list[dict]:
        trimmed = self._trimHistory()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend({"role": m.role, "content": m.content} for m in trimmed)
        return messages

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