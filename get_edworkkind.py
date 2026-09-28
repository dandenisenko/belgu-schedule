import requests
from datetime import datetime, timedelta, timezone


GROUP = "12002605"
WEEKS_AHEAD = 20

API_URL = "https://beluni.ru/schedule/g"

MSK = timezone(timedelta(hours=3))


def get_monday(date):
    return date - timedelta(days=date.weekday())


def get_week_schedule(monday):
    sunday = monday + timedelta(days=6)

    date_from = monday.strftime("%Y-%m-%d")
    date_to = sunday.strftime("%Y-%m-%d")

    url = (
        f"{API_URL}/{GROUP}"
        f"?from={date_from}"
        f"&to={date_to}"
        f"&qdist=1"
    )

    print(f"Загрузка: {date_from} - {date_to}")

    response = requests.get(
        url,
        timeout=20,
        headers={
            "User-Agent": "BelGU Schedule Parser/3.1"
        }
    )

    response.raise_for_status()

    return response.json()


def main():

    today = datetime.now(MSK).date()
    first_monday = get_monday(today)

    all_lessons = []

    for week in range(WEEKS_AHEAD):

        monday = (
            first_monday
            + timedelta(weeks=week)
        )

        lessons = get_week_schedule(monday)

        all_lessons.extend(lessons)

    # Собираем уникальные edworkkind
    edworkkinds = {}

    for lesson in all_lessons:
        if lesson.get("edworkkind") is None:
            print()
            print("Дисциплина:", lesson.get("dis"))
            print("Место:", (lesson.get("room") or {}).get("name"))
            print("Онлайн:", lesson.get("online"))
            print("Подгруппа:", lesson.get("subgroup"))
            print("Преподаватель:", (lesson.get("teacher") or {}).get("name"))  

    print()
    print("=" * 60)
    print("ВСЕ EDWORKKIND")
    print("=" * 60)

    for value, count in sorted(
        edworkkinds.items(),
        key=lambda item: str(item[0])
    ):
        print(
            f"{value!r} → {count} записей"
        )

    print()
    print(
        f"Всего записей: {len(all_lessons)}"
    )

    print(
        f"Уникальных edworkkind: "
        f"{len(edworkkinds)}"
    )


if __name__ == "__main__":
    main()