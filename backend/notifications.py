from __future__ import annotations
from threading import Lock
from typing import Any, TypeVar

T = TypeVar("T")

class SingletonMeta(type):
    _instances: dict[type, Any] = {}
    _lock: Lock = Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> T:
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
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs) # cache instance and calls original __call__ method to actually construct object
                cls._instances[cls] = instance
        return cls._instances[cls]

class EventSystem(metaclass=SingletonMeta):
    _notification_queue: dict[str, list] = {}
    
    def subscribe_session(self, session_id: str, notifications: list = []) -> None:
        self._notification_queue[session_id] = notifications
        return
    
    def add_notification_to_queue(self, session_id: str, notifications: dict[str, str]) -> None:
        self._notification_queue[session_id].append(notifications)
        return
    
    def get_session_notifications(self, session_id: str) -> list:
        return self._notification_queue.get(session_id, [])
    
    def unsubscribe_session(self, session_id: str) -> None:
        self._notification_queue.pop(session_id, None)
        return