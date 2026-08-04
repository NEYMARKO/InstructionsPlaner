from __future__ import annotations

from enum import Enum

from datastar_py.attributes import SignalValue

from .singleton import SingletonMeta


class NotifType(Enum):
    MESSAGE = 1
    RESPONSE = 2
    EMPTY= -1
    
class EventSystem(metaclass=SingletonMeta):
    _notification_queue: dict[str, list[tuple[NotifType, dict[str, dict[str, str | SignalValue]]]]] = {}
    _shutdown: bool = False
    
    def subscribe_session(self, subscription_id: str, notifications: list[tuple[NotifType, dict[str, dict[str, str | SignalValue]]]] = []) -> None:
        if subscription_id not in self._notification_queue:
            self._notification_queue[subscription_id] = notifications
        return 
    
    def add_notification_to_queue(self, subscription_id: str, notification: tuple[NotifType, dict[str, dict[str, str | SignalValue]]]) -> None:
        self.subscribe_session(subscription_id)
        self._notification_queue[subscription_id].append(notification)
        return
    
    async def get_session_notifications(self, subscription_id: str) -> list[tuple[NotifType, dict[str, dict[str, str | SignalValue]]]]:
        return self._notification_queue.get(subscription_id, [])
    
    def unsubscribe_session(self, subscription_id: str) -> None:
        self._notification_queue.pop(subscription_id, None)
        return

    def consume_notifications(self, subscription_id: str, processed_notifications: list[tuple[NotifType, dict[str, dict[str, str | SignalValue]]]]) -> None:
        session_notifications = self._notification_queue.get(subscription_id, [])
        for notif in processed_notifications:
            if notif in session_notifications:
                session_notifications.remove(notif)
            # if TERMINATE_SIGNAL_NAME in notif:
            #     raise CloseStreamException("Close stream")
        self._notification_queue[subscription_id] = session_notifications
        return

    async def consume_notification(self, subscription_id: str) -> tuple[NotifType, dict[str, dict[str, str | SignalValue]]]:
        session_notifications = self._notification_queue.get(subscription_id, [])
        if not session_notifications:
            return (NotifType.EMPTY, {})
        return session_notifications.pop()

    def combine_signals(self, notifications: list[dict[str, str]]) -> dict[str, SignalValue]:
        signals: dict[str, SignalValue] = {}
        for notif in notifications:
            for key in notif:
                signals[key] = notif[key]
        return signals

    def shutdown_streams(self) -> None:
        self._notification_queue.clear()
        self._shutdown = True

    def should_shutdown(self) -> bool:
        return self._shutdown

event_system = EventSystem()
