from typing import Iterable


# Идея простая, расширять особо нечего :D


class LessonSession:
    STATUS_ENTER = "enter"
    STATUS_LEAVE = "leave"

    @staticmethod
    def extract_timeline(data: dict[str, list[int]]):
        timeline = [
            (time, (member, LessonSession.STATUS_ENTER if i % 2 == 0 else LessonSession.STATUS_LEAVE))
            for member, times in data.items()
            for i, time in enumerate(times)
        ]
        if len(timeline) % 2 != 0:
            raise ValueError("Invalid timeline")
        return sorted(timeline, key=lambda x: x[0])

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
        member, act = action
        if act == LessonSession.STATUS_ENTER:
            session.enter(member, timestamp)
        else:
            session.leave(member, timestamp)

    return session.counter

data = {
    'lesson': [1594663200, 1594666800],
    'pupil': [1594663340, 1594663389, 1594663390, 1594663395, 1594663396, 1594666472],
    'tutor': [1594663290, 1594663430, 1594663443, 1594666473]
}

print(appearance(data))