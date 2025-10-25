from typing import Dict, List, Callable
import asyncio

class SSEBroker:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, key: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(key, []).append(q)
        return q

    def unsubscribe(self, key: str, q: asyncio.Queue) -> None:
        if key in self._subscribers:
            self._subscribers[key] = [x for x in self._subscribers[key] if x is not q]
            if not self._subscribers[key]:
                self._subscribers.pop(key, None)

    async def publish(self, key: str, data: dict) -> None:
        for q in self._subscribers.get(key, []):
            await q.put(data)

broker = SSEBroker()
