import enum
from enum import Enum
from typing import List, Set


class JobState(Enum):
    PENDING = enum.auto()
    RUNNING = enum.auto()
    REQUEUED = enum.auto()
    RESIZING = enum.auto()
    SUSPENDED = enum.auto()
    COMPLETED = enum.auto()
    CANCELLED = enum.auto()
    FAILED = enum.auto()
    TIMEOUT = enum.auto()
    PREEMPTED = enum.auto()
    NODE_FAIL = enum.auto()
    BOOT_FAIL = enum.auto()
    DEADLINE = enum.auto()
    OUT_OF_MEMORY = enum.auto()
    UNKNOWN = enum.auto()

    @classmethod
    def from_str(cls, state: str):
        if state in cls.__members__:
            return cls[state]
        else:
            return cls.UNKNOWN

    def __str__(self):
        return self.name
    def __repr__(self):
        return self.__str__()


FINISHED_STATES = [
    JobState.COMPLETED,
    JobState.CANCELLED,
]

UNFINISHED_STATES = [
    JobState.PENDING,
    JobState.RUNNING,
    JobState.REQUEUED,
    JobState.RESIZING,
    JobState.SUSPENDED,
]


class Job:
    def __init__(self, jobid: str):
        self.id = jobid
        self.states: List[JobState] = [JobState.PENDING]
        self.success = False

    @property
    def unique_states(self) -> Set[JobState]:
        return set(self.states)

    def __repr__(self):
        return f"Job(id={self.id}, states={self.unique_states}, finished={self.is_finished}, success={self.success})"

    @property
    def is_finished(self):
        """Returns True if all states are finished states"""
        return all([s in FINISHED_STATES for s in self.unique_states])

    @property
    def successful_completion(self):
        """Returns True if unique_states == {COMPLETED}"""
        return self.unique_states == {JobState.COMPLETED}
