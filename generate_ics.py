import requests
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from icalendar import Calendar, Event

GROUP = "12002605"
WEEKS_AHEAD = 20
API_URL = "https://beluni.ru/schedule/g"
MSK = timezone(timedelta(hours=3))
OUTPUT_DIR = Path("schedule")

CALENDARS = {
    "lectures": ("БелГУ - Лекции", "Лекции группы 12002605"),
    "practical": ("БелГУ - Практические", "Практические занятия группы 12002605"),
    "laboratory": ("БелГУ - Лабораторные", "Лабораторные занятия группы 12002605"),
    "tests": ("БелГУ - Зачёты", "Зачёты и дифференцированные зачёты группы 12002605"),
    "mooc": ("БелГУ - МООК", "МООК группы 12002605"),
}

WORK_KIND_MAP = {
    "лек.": ("lectures", "Лекция"),
    "лек": ("lectures", "Лекция"),
    "лекция": ("lectures", "Лекция"),
    "лекции": ("lectures", "Лекция"),
    "пр.з.": ("practical", "Практическое занятие"),
    "пр.з": ("practical", "Практическое занятие"),
    "пр": ("practical", "Практическое занятие"),
    "пр.": ("practical", "Практическое занятие"),
    "практическое": ("practical", "Практическое занятие"),
    "практическое занятие": ("practical", "Практическое занятие"),
    "лаб.": ("laboratory", "Лабораторная"),
    "лаб": ("laboratory", "Лабораторная"),
    "лабораторная": ("laboratory", "Лабораторная"),
    "лабораторное занятие": ("laboratory", "Лабораторная"),
    "зач.": ("tests", "Зачёт"),
    "зач": ("tests", "Зачёт"),
    "зачёт": ("tests", "Зачёт"),
    "зачет": ("tests", "Зачёт"),
    "дифф.зач.": ("tests", "Дифференцированный зачёт"),
    "дифф.зач": ("tests", "Дифференцированный зачёт"),
    "дифф.зачёт": ("tests", "Дифференцированный зачёт"),
    "дифф.зачет": ("tests", "Дифференцированный зачёт"),
    "дифференцированный зачёт": ("tests", "Дифференцированный зачёт"),
    "дифференцированный зачет": ("tests", "Дифференцированный зачёт"),
}

def normalize_text(value):
    return " ".join(str(value).lower().strip().split()) if value is not None else ""

def normalize_position(position):
    if not position:
        return ""
    value = normalize_text(position)
    return {
        "пр": "преп.", "пр.": "преп.",
        "ст.пр": "ст.преп.", "ст.пр.": "ст.преп.",
        "ст.преп": "ст.преп.", "ст.преп.": "ст.преп.",
    }.get(value, str(position).strip())

def normalize_subgroup(subgroup):
    if not subgroup:
        return ""
    value = str(subgroup).strip()
    normalized = normalize_text(value)
    if normalized.endswith("подгруппа"):
        number = normalized[:-len("подгруппа")].strip()
        if number:
            return f"{number} п/г"
    return value

def is_mooc(lesson):
    subject = normalize_text(lesson.get("dis"))
    if subject == "университетская среда":
        return True
    room = lesson.get("room") or {}
    return normalize_text(room.get("name")) == "онлайн курс"

def detect_calendar(lesson):
    if is_mooc(lesson):
        return "mooc", "МООК"
    return WORK_KIND_MAP.get(normalize_text(lesson.get("edworkkind")), (None, None))

def make_uid(lesson):
    teacher = lesson.get("teacher") or {}
    room = lesson.get("room") or {}
    stable = "|".join([
        GROUP, str(lesson.get("timestart", "")), str(lesson.get("timeend", "")),
        lesson.get("dis") or "", lesson.get("edworkkind") or "",
        lesson.get("subgroup") or "", str(teacher.get("id") or ""),
        str(room.get("id") or ""),
    ])
    return f"{hashlib.sha256(stable.encode('utf-8')).hexdigest()[:24]}@belgu-parser"

def get_teacher_name(lesson):
    teacher = lesson.get("teacher") or {}
    name = teacher.get("name")
    if not name:
        return ""
    position = normalize_position(teacher.get("pos"))
    return f"{position} {name}" if position else name

def format_description(lesson, full_work_kind):
    lines = [f"Тип занятия: {full_work_kind}"]
    subgroup = normalize_subgroup(lesson.get("subgroup"))
    if subgroup:
        lines.append(f"Подгруппа: {subgroup}")
    teacher = get_teacher_name(lesson)
    if teacher:
        lines.append(f"Преподаватель: {teacher}")

    room = lesson.get("room") or {}
    room_name = room.get("name")
    area = room.get("area")

    if area and normalize_text(room_name) != "онлайн курс":
        area_text = str(area).strip()
        prefix = "учебный корпус"
        if area_text.lower().startswith(prefix):
            number = area_text[len(prefix):].strip()
            lines.append(f"Учебный корпус: {number}" if number else f"Учебный корпус: {area_text}")
        else:
            lines.append(f"Учебный корпус: {area_text}")

    if room_name and normalize_text(room_name) != "онлайн курс":
        lines.append(f"Аудитория: {room_name}")

    lines += ["", "Учебные материалы:"]
    for link in lesson.get("links") or []:
        href = link.get("href")
        if href:
            name = link.get("name")
            lines.append(f"{name}: {href}" if name else href)

    lines += ["", "Заметки:"]
    return "\n".join(lines)

def get_location(lesson):
    if is_mooc(lesson):
        return "МООК"

    room = lesson.get("room") or {}
    room_name = room.get("name")
    area = room.get("area")
    parts = []

    if area:
        area_text = str(area).strip()
        if area_text.lower().startswith("учебный корпус"):
            number = area_text[len("учебный корпус"):].strip()
            parts.append(f"Уч. корп. {number}" if number else f"Уч. корп. {area_text}")
        else:
            parts.append(f"Уч. корп. {area_text}")

    if room_name:
        parts.append(f"Ауд. {room_name}")

    if parts:
        return ", ".join(parts)
    if lesson.get("online"):
        return "Онлайн"
    return ""

def get_monday(date):
    return date - timedelta(days=date.weekday())

def get_week_schedule(monday):
    sunday = monday + timedelta(days=6)
    date_from = monday.strftime("%Y-%m-%d")
    date_to = sunday.strftime("%Y-%m-%d")
    url = f"{API_URL}/{GROUP}?from={date_from}&to={date_to}&qdist=1"
    print(f"Загрузка: {date_from} - {date_to}")
    response = requests.get(url, timeout=20, headers={"User-Agent": "BelGU Schedule Parser/3.1"})
    response.raise_for_status()
    data = response.json()
    print(f"  Получено записей: {len(data)}")
    return data

def get_all_schedule():
    today = datetime.now(MSK).date()
    first_monday = get_monday(today)
    all_lessons = []
    for week in range(WEEKS_AHEAD):
        all_lessons.extend(get_week_schedule(first_monday + timedelta(weeks=week)))
    return all_lessons

def create_event(lesson, full_work_kind):
    start = datetime.fromtimestamp(lesson["timestart"], MSK)
    end = datetime.fromtimestamp(lesson["timeend"], MSK)
    event = Event()
    event.add("summary", lesson.get("dis") or "Без названия")
    event.add("dtstart", start)
    event.add("dtend", end)
    event.add("uid", make_uid(lesson))
    event.add("dtstamp", datetime.now(timezone.utc))
    event.add("status", "CONFIRMED")
    event.add("description", format_description(lesson, full_work_kind))
    location = get_location(lesson)
    if location:
        event.add("location", location)
    if lesson.get("pairnumber"):
        event.add("x-belgu-pair-number", str(lesson["pairnumber"]))
    if lesson.get("edworkkind"):
        event.add("x-belgu-work-kind", lesson["edworkkind"])
    event.add("x-belgu-full-work-kind", full_work_kind)
    subgroup = normalize_subgroup(lesson.get("subgroup"))
    if subgroup:
        event.add("x-belgu-subgroup", subgroup)
    return event

def create_calendar(key, lessons):
    name, description = CALENDARS[key]
    calendar = Calendar()
    calendar.add("prodid", "-//BelGU Schedule Parser 3.1//")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("method", "PUBLISH")
    calendar.add("x-wr-calname", name)
    calendar.add("x-wr-timezone", "Europe/Moscow")
    calendar.add("x-wr-caldesc", description)
    for lesson in lessons:
        calendar.add_component(create_event(lesson, lesson["_full_work_kind"]))
    return calendar

def save_calendar(key, lessons):
    OUTPUT_DIR.mkdir(exist_ok=True)
    filename = OUTPUT_DIR / f"{key}.ics"
    with open(filename, "wb") as file:
        file.write(create_calendar(key, lessons).to_ical())
    return filename

def main():
    print("=" * 60)
    print("БелГУ → ICS V3.1")
    print(f"Группа: {GROUP}")
    print(f"Период: {WEEKS_AHEAD} недель")
    print("=" * 60)
    print()

    lessons = get_all_schedule()
    print(f"\nВсего получено записей: {len(lessons)}")

    calendars = {key: [] for key in CALENDARS}
    unknown = []

    for lesson in lessons:
        key, full_kind = detect_calendar(lesson)
        if key:
            lesson["_full_work_kind"] = full_kind
            calendars[key].append(lesson)
        else:
            unknown.append(lesson)

    print("\n" + "-" * 60)
    print("РАСПРЕДЕЛЕНИЕ")
    print("-" * 60)
    for key, items in calendars.items():
        print(f"{CALENDARS[key][0]}: {len(items)}")
    print(f"Не классифицировано: {len(unknown)}")

    if unknown:
        print("\nНе классифицированные записи:")
        seen = {}
        for lesson in unknown:
            kind = lesson.get("edworkkind") or "(без типа)"
            subject = lesson.get("dis") or "Без названия"
            seen[(kind, subject)] = seen.get((kind, subject), 0) + 1
        for (kind, subject), count in seen.items():
            print(f"  {count} × {subject} [{kind}]")

    print("\n" + "-" * 60)
    print("СОХРАНЕНИЕ")
    print("-" * 60)
    for key, items in calendars.items():
        print(f"✓ {save_calendar(key, items)}")

    print("\n" + "=" * 60)
    print("Готово!")
    print("=" * 60)

if __name__ == "__main__":
    main()
