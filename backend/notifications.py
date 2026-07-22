from __future__ import annotations
from datastar_py.attributes import SignalValue
from typing import Any, TypeVar
from threading import Lock

T = TypeVar("T")

class SingletonMeta(type):
    _instances: dict[type, Any] = {}
    _lock: Lock = Lock()

    def __call__(cls: type[T], *args: Any, **kwargs: Any) -> T:
        """
        Creates dictionary, whose keys are classes that are using SingletonMeta class as blueprint (that have
        `metaclass=SingletonMeta` in their definition), and it's values are instances of those classes.

        For example, if we define
        ```python
        class Foo(metaclass=SingletonMeta):
            def __init__(self, x):
                self.x = x

        class Dog(metaclass=SingletonMeta):
            def __init__(self, name):
                self.name = name

        class Car(metaclass=SingletonMeta):
            def __init__(self, name):
                self.name = name
        ```

        and instantiate Foo, Dog and Car in any file in the project, `_instances` would contain this:
        ```
        _instances = {
            Foo: <the one Foo instance>,
            Dog: <the one Dog instance>,
            Car: <the one Car instance>,
        }
        ```

        which means that every time we try to instantiate one of those objects, function will check whether
        that object has already been instantiated, and if so, it's instance will get returned to the user, so that
        only 1 instance of each object type exists (singleton).
        """
        with SingletonMeta._lock:
            if cls not in SingletonMeta._instances:
                instance = super().__call__(*args, **kwargs) # cache instance and calls original __call__ method to actually construct object
                SingletonMeta._instances[cls] = instance
        return SingletonMeta._instances[cls]

class EventSystem(metaclass=SingletonMeta):
    _notification_queue: dict[str, list[dict[str, str]]] = {}
    
    def subscribe_session(self, session_id: str, notifications: list[dict[str, str]] = []) -> None:
        if session_id not in self._notification_queue:
            self._notification_queue[session_id] = notifications
        return
    
    def add_notification_to_queue(self, session_id: str, notification: dict[str, str]) -> None:
        self._notification_queue[session_id].append(notification)
        return
    
    async def get_session_notifications(self, session_id: str) -> list[dict[str, str]]:
        return self._notification_queue.get(session_id, [])
    
    def unsubscribe_session(self, session_id: str) -> None:
        self._notification_queue.pop(session_id, None)
        return

    def consume_notifications(self, session_id: str, processed_notifications: list[dict[str, str]]) -> None:
        session_notifications = self._notification_queue.get(session_id, [])
        for notif in processed_notifications:
            if notif in session_notifications:
                session_notifications.remove(notif)
        self._notification_queue[session_id] = session_notifications
        return

    def combine_signals(self, notifications: list[dict[str, str]]) -> dict[str, SignalValue]:
        signals: dict[str, SignalValue] = {}
        for notif in notifications:
            for key in notif:
                signals[key] = notif[key]
        return signals

event_system = EventSystem()
