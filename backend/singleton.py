from threading import Lock
from typing import Any, TypeVar

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