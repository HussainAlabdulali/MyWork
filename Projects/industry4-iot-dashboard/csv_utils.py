import csv, os
import math


def write_accel_to_csv(time, x_axis, y_axis, z_axis, light, temp, tilt, mag, sound, flame, filepath="accel.csv"):
    if not all([time, x_axis, y_axis, z_axis]):
        raise ValueError("All fields (time, x_axis, y_axis, z_axis) must be provided")

    try:
        x = float(x_axis)
        y = float(y_axis)
        z = float(z_axis)
    except ValueError:
        raise ValueError("x_axis, y_axis, z_axis must be valid floats")

    LED = ""
    LED += "1" if abs(x) > 0.3 else "0"
    LED += "1" if abs(y) > 0.3 else "0"
    LED += "1" if abs(z) > 1.3 else "0"

    fall = detect_fall(x, y, z)

    if os.path.isfile(filepath):
        with open(filepath, newline='') as f:
            row_count = sum(1 for row in f) - 1
            next_id = row_count + 1
    else:
        next_id = 1

    data = {
        "id": next_id,
        "time": time,
        "x_axis": x,
        "y_axis": y,
        "z_axis": z,
        "LED": LED,
        "fall": fall,
        "magnitude": math.sqrt(x * x + y * y + z * z),
        "light": light,
        "temp": temp,
        "tilt": tilt,
        "mag": mag,
        "sound": sound,
        "flame": flame

    }

    file_exists = os.path.isfile(filepath) and os.path.getsize(filepath) > 0
    with open(filepath, "a", newline="", encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "time", "x_axis", "y_axis", "z_axis", "LED", "fall", "magnitude",
                                               "light", "temp", "tilt", "mag", "sound", "flame"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


def get_all_rows(filepath="accel.csv"):
    if not os.path.exists(filepath):
        return []
    with open(filepath) as f:
        return list(csv.DictReader(f))


def modify_row_by_id(accel_id, updates, filepath="accel.csv"):
    rows = get_all_rows(filepath)
    modified = False

    for row in rows:
        if row["id"] == str(accel_id):
            for key in ["time", "x_axis", "y_axis", "z_axis", "LED", "fall"]:
                if key in updates and updates[key]:
                    row[key] = updates[key]
            modified = True
            break

    if not modified:
        return False

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "time", "x_axis", "y_axis", "z_axis", "LED", "fall"])
        writer.writeheader()
        writer.writerows(rows)

    return True


def delete_row_by_id(accel_id, filepath="accel.csv"):
    rows = get_all_rows(filepath)
    new_rows = [row for row in rows if row["id"] != str(accel_id)]
    if len(new_rows) == len(rows):
        return False  # Nothing deleted

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "time", "x_axis", "y_axis", "z_axis", "LED", "fall"])
        writer.writeheader()
        writer.writerows(new_rows)

    return True


def get_all_rows_as_json():
    rows = get_all_rows()
    return [dict(r) for r in rows]


def get_latest_led():
    rows = get_all_rows()
    if not rows:
        return None

    valid_rows = []
    for r in rows:
        try:
            rid = int(r.get("id", -1))
            if rid >= 0:
                valid_rows.append(r)
        except (ValueError, TypeError):
            continue

    if not valid_rows:
        return None

    latest = sorted(valid_rows, key=lambda r: int(r["id"]), reverse=True)[0]
    return latest["LED"]


def get_latest_fall():
    rows = get_all_rows()
    if not rows:
        return None

    valid_rows = []
    for r in rows:
        try:
            rid = int(r.get("id", -1))
            if rid >= 0:
                valid_rows.append(r)
        except (ValueError, TypeError):
            continue

    if not valid_rows:
        return None

    latest = sorted(valid_rows, key=lambda r: int(r["id"]), reverse=True)[0]
    return latest["fall"]


def detect_fall(x, y, z):
    # Fall state convention used by the dashboard: 0 = sudden stop,
    # 1 = sudden acceleration/impact, -1 = normal range.
    total_accel = (x ** 2 + y ** 2 + z ** 2) ** 0.5

    if total_accel < 0.7:
        return 0
    elif total_accel > 1.8:
        return 1
    else:
        return -1
