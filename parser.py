import requests
from datetime import datetime, timezone, timedelta

MSK = timezone(timedelta(hours=3))

GROUP = "12002605"

FROM = "2026-09-14"
TO = "2026-09-20"

URL = (
    f"https://beluni.ru/schedule/g/{GROUP}"
    f"?from={FROM}&to={TO}&qdist=1"
)


def get_schedule():
    response = requests.get(URL, timeout=15)
    response.raise_for_status()

    return response.json()


def format_lesson(lesson):
    start = datetime.fromtimestamp(
        lesson["timestart"],
        MSK
    )

    end = datetime.fromtimestamp(
        lesson["timeend"],
        MSK
    )

    teacher = lesson.get("teacher")
    room = lesson.get("room")

    return {
        "date": start.strftime("%Y-%m-%d"),
        "start": start.strftime("%H:%M"),
        "end": end.strftime("%H:%M"),

        "pair": lesson["pairnumber"],
        "type": lesson["edworkkind"],
        "subject": lesson["dis"],

        "subgroup": lesson.get("subgroup"),

        "teacher": (
            teacher["name"]
            if teacher
            else None
        ),

        "room": (
            room["name"]
            if room
            else None
        ),

        "building": (
            room["area"]
            if room
            else None
        ),

        "address": (
            room["address"]
            if room
            else None
        ),

        "online": lesson.get("online", False),

        "links": lesson.get("links") or [],
    }


def main():
    print(f"Получаем расписание группы {GROUP}...")
    print(f"Период: {FROM} - {TO}")
    print()

    lessons = get_schedule()

    print(f"Получено занятий: {len(lessons)}")
    print()

    for lesson in lessons:
        data = format_lesson(lesson)

        print(
            f'{data["date"]} '
            f'{data["start"]}-{data["end"]} | '
            f'Пара {data["pair"]} | '
            f'{data["type"]} | '
            f'{data["subject"]}'
        )

        if data["subgroup"]:
            print(f'  Подгруппа: {data["subgroup"]}')

        if data["teacher"]:
            print(f'  Преподаватель: {data["teacher"]}')

        if data["room"]:
            print(
                f'  Аудитория: {data["room"]} '
                f'({data["building"]})'
            )

        if data["online"]:
            print("  Онлайн")

        print()


if __name__ == "__main__":
    main()