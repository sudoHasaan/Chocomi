from models import Message
from config import settings
from vector_store import retrieve_context

SYSTEM_PROMPT = """You are Chocomi, a helpful assistant.
Your goal is to be helpful and answer questions relying on the <RETRIEVED_CONTEXT>.

<CRITICAL_RULES>
You do not know the time, weather, or math. YOU MUST USE TOOLS to answer them.
If the user asks about weather, time, or math, you MUST include the exact <TOOL> tag in your response. Do not guess the answer!

Available Tools:
- get_weather(location): Returns exact temperature and wind. (Default: Karachi). Example: <TOOL>get_weather(Karachi)</TOOL>
- get_current_time(): Returns current exact local time. Example: <TOOL>get_current_time()</TOOL>
- calculate(expression): Returns math result. Example: <TOOL>calculate(2+2)</TOOL>

Example response:
The best GPU is RX 7800 XT. The current weather is <TOOL>get_weather(Karachi)</TOOL> and the time is <TOOL>get_current_time()</TOOL>.
</CRITICAL_RULES>
"""

SIGNAL_KEYWORDS: list[str] = [
    "tool", "pc", "rgb", "gpu", "cpu", "ram", "storage", "cooling", "motherboard",
    "delivery", "warranty", "return", "policy", "price", "stock", "store", "hours",
    "discount", "rental", "repair", "build", "flash", "weather", "time", "calculate", "math"
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
        
        # Get the latest user query for RAG
        latest_query = ""
        for msg in reversed(trimmed):
            if msg.role == "user":
                latest_query = msg.content
                break
                
        # Retrieve context from vector store
        context = ""
        if latest_query:
            context = retrieve_context(latest_query, k=3)
            
        sys_prompt_with_rag = SYSTEM_PROMPT + f"\n<RETRIEVED_CONTEXT>\n{context}\n</RETRIEVED_CONTEXT>"
        
        messages = [{"role": "system", "content": sys_prompt_with_rag}]
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