import json
import time
import redis
import requests

r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)


def request_redis(url: str, headers, attempts: int = 10) -> dict:
    try:
        cached_data = r.get(url)
        if cached_data:
            return json.loads(cached_data)
    except redis.RedisError as re:
        pass

    for attempt in range(attempts):
        try:
            print(url)
            response = requests.get(url, timeout=10, headers=headers)

            if response.status_code == 200:
                data_json = response.json()
                try:
                    r.set(name=url, value=json.dumps(data_json))
                except redis.RedisError as re:
                    pass

                return data_json

            raise requests.exceptions.HTTPError(
                f"Status {response.status_code}"
            )

        except (requests.exceptions.RequestException, Exception) as e:
            print(f"wait: {e}")

            if attempt+1 < attempts:
                time.sleep(60)
            else:
                raise
