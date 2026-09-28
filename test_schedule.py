import requests

GROUP = "12002605"
FROM = "2026-09-14"
TO = "2026-09-20"

url = f"https://beluni.ru/schedule/g/{GROUP}?from={FROM}&to={TO}&qdist=1"

response = requests.get(url, timeout=15)

print("Статус:", response.status_code)
print("URL:", response.url)
print("Размер:", len(response.content), "байт")
print()
print(response.text[:5000])