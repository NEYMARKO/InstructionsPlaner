from collections import deque
from collections.abc import Callable
from typing import Any

from ..backend.singleton import SingletonMeta


class Task:
    def __init__(self, fn: Callable[[], Any]):
        self.fn = fn
        return

    def execute(self) -> None:
        self.fn()

class TaskQueue(metaclass=SingletonMeta):
    queue: deque[Task] = deque()

    def add(self, task: Task) -> None:
        self.queue.append(task)

    def run_next(self) -> None:
        """
        Runs 1st task in queue and consumes it. 
        If task returns callable, it is automatically appended to the end of the queue.
        """

        if not self.queue:
            return None
        
        active_task = self.queue.popleft()
        result = active_task.execute()

        if callable(result):
            self.add(Task(result))
            return None

task_queue = TaskQueue()
