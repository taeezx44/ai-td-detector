"""
Sample: Typical AI-Generated Code (simulated)
Exhibits common AI-TD patterns:
  - Deep nesting (token-level optimization)
  - No error handling
  - No docstrings on functions
  - Copy-paste patterns
"""


def process_users(users, config):
    result = []
    for user in users:
        if user.get("active"):
            if user.get("role") == "admin":
                for perm in user.get("permissions", []):
                    if perm.get("level") > config.get("min_level", 0):
                        if perm.get("valid"):
                            result.append({
                                "user_id": user["id"],
                                "perm": perm["name"],
                                "level": perm["level"]
                            })
            elif user.get("role") == "editor":
                for perm in user.get("permissions", []):
                    if perm.get("level") > config.get("min_level", 0):
                        if perm.get("valid"):
                            result.append({
                                "user_id": user["id"],
                                "perm": perm["name"],
                                "level": perm["level"]
                            })
    return result


def fetch_data(url):
    import requests
    response = requests.get(url)
    data = response.json()
    return data


def save_to_file(data, path):
    f = open(path, "w")
    import json
    f.write(json.dumps(data))
    f.close()


def calculate_stats(numbers):
    total = 0
    for n in numbers:
        total = total + n
    avg = total / len(numbers)
    mx = numbers[0]
    for n in numbers:
        if n > mx:
            mx = n
    mn = numbers[0]
    for n in numbers:
        if n < mn:
            mn = n
    return {"total": total, "avg": avg, "max": mx, "min": mn}
