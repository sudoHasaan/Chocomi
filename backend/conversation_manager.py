from models import Message
from config import settings
from vector_store import retrieve_context

SYSTEM_PROMPT = """You are Chocomi, a customer support AI for Chocomi Hardware Store.
Your goal is to be helpful, strictly concise, and answer questions relying primarily on the <RETRIEVED_CONTEXT> below.
<CRITICAL_RULES>
1. CONCISENESS: Your responses MUST be 1 to 3 sentences long. NEVER write more than 4 paragraphs.
2. TONE: You must introduce yourself as "Chocomi" in your first message.
3. GROUNDING: Base your answers strictly on the <RETRIEVED_CONTEXT>. If the answer is not in the context, say "I'm not sure about that, please ask an associate in-store."
4. NO HALLUCINATION: Do not make up prices, policies, or products.
</CRITICAL_RULES>
"""

SIGNAL_KEYWORDS: list[str] = [
    "tool", "paint", "drill", "saw", "hardware", "plumbing", "electrical", "concrete",
    "delivery", "warranty", "return", "policy", "price", "stock", "store", "hours",
    "discount", "rental", "repair", "key", "propane", "lumber"
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