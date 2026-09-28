import requests
import re

base_url = "https://beluni.ru"

js_url = base_url + "/js/app.c2258d17.js"

response = requests.get(
    js_url,
    headers={
        "User-Agent": "Mozilla/5.0"
    },
    timeout=20
)

print("Статус:", response.status_code)
print("Размер JS:", len(response.content), "байт")

js = response.text

# Сохраняем файл, чтобы при необходимости посмотреть его целиком
with open("app.js", "w", encoding="utf-8") as f:
    f.write(js)

print("\nФайл сохранён: app.js")

# Ищем URL и подозрительные строки
print("\nВОЗМОЖНЫЕ URL:")
print("-" * 70)

urls = re.findall(r'https?://[^"\'\s]+', js)

for url in sorted(set(urls)):
    print(url)

print("\n\nВОЗМОЖНЫЕ API-ПУТИ:")
print("-" * 70)

patterns = [
    r'["\']([^"\']*/api/[^"\']*)["\']',
    r'["\']([^"\']*schedule[^"\']*)["\']',
    r'["\']([^"\']*group[^"\']*)["\']',
    r'["\']([^"\']*lesson[^"\']*)["\']',
    r'["\']([^"\']*timetable[^"\']*)["\']',
    r'["\']([^"\']*raspis[^"\']*)["\']',
]

found = set()

for pattern in patterns:
    for match in re.findall(pattern, js, re.IGNORECASE):
        found.add(match)

for item in sorted(found):
    print(item)