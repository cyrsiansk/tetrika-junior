from typing import Iterable


# Идея простая, расширять особо нечего :D


def get_enter_timestamps(timestamps: list[int]) -> list[int]:
    return [timestamps[i] for i in range(0, len(timestamps), 2)]


def get_leave_timestamps(timestamps: list[int]) -> list[int]:
    return [timestamps[i + 1] for i in range(0, len(timestamps), 2)]


class LessonSession:
    STATUS_ENTER = "enter"
    STATUS_LEAVE = "leave"

    @staticmethod
    def extract_timeline(data: dict[str, list[int]]):
        timeline = []
        members = data.keys()
        for member in members:
            timeline.extend((t, (member, LessonSession.STATUS_ENTER)) for t in get_enter_timestamps(data[member]))
            timeline.extend((t, (member, LessonSession.STATUS_LEAVE)) for t in get_leave_timestamps(data[member]))

        timeline.sort(key=lambda x: x[0])
        return timeline

    def __init__(self, members: Iterable[str]):
        self.statuses = {member: 0 for member in members}
        self.active_since = 0
        self.last_status = False
        self.counter = 0

    def update(self, timestamp: int):
        status = all(self.statuses.values())
        if status and not self.last_status:
            self.active_since = timestamp
        elif not status and self.last_status:
            self.counter += timestamp - self.active_since
        self.last_status = status

    def enter(self, member: str, timestamp: int):
        self.statuses[member] += 1
        self.update(timestamp)

    def leave(self, member: str, timestamp: int):
        self.statuses[member] -= 1
        self.update(timestamp)


def appearance(data: dict[str, list[int]]) -> int:
    members = data.keys()
    timeline = LessonSession.extract_timeline(data)
    session = LessonSession(members)

    for timestamp, action in timeline:
        member, act = action.split()
        if act == LessonSession.STATUS_ENTER:
            session.enter(member, timestamp)
        else:
            session.leave(member, timestamp)

    return session.counter
