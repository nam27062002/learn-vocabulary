import time
import requests

url = "https://api.dictionaryapi.dev/api/v2/entries/en/meticulous"

start_time = time.time()
response = requests.get(url)
print(response.json())
end_time = time.time()
print(f"Yêu cầu API mất {end_time - start_time} giây")