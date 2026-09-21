from flask import *
import csv_utils
import pandas as pd
import os
from datetime import datetime
import csv
import math
from models import *

# LabVIEW/myRIO posts one sensor packet to this Flask app. The backend stores the
# raw reading, derives module-specific values, and exposes files/API data for the
# dashboard pages that poll for live updates.

def get_tilt_angles(x, y, z):
    pitch = math.atan2(y, math.sqrt(x ** 2 + z ** 2)) * (180 / math.pi)
    roll = math.atan2(x, math.sqrt(y ** 2 + z ** 2)) * (180 / math.pi)
    return {'pitch': pitch, 'roll': roll}


app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def data_file(filename):
    return os.path.join(DATA_DIR, filename)


ADDRESSES_FILE = data_file("addresses.txt")
DEVICE_ID_FILE = data_file("device-id.txt")


def read_text_file(filepath):
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()


def write_text_file(filepath, value):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(value.strip())


update_flags = {
    'tool_drop': True,
    'package_drop': True,
    'vibration': True,
    'agv': True,
    'worker_monitoring': True
}


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/tool-drop')
def tool_drop():
    return render_template("tool-drop.html")


@app.route('/vibration-monitoring')
def vibration_monitoring():
    return render_template("vibration-monitoring.html")


@app.route('/agv-collision')
def agv_collision():
    return render_template("agv-collision.html")


@app.route('/worker-fatigue')
def worker_fatigue():
    return render_template("worker-fatigue.html")


@app.route('/package-drop')
def package_drop():
    return render_template("package-drop.html")


@app.route('/api', methods=['GET', 'POST'])
def api_read():
    if request.method == 'POST':
        try:
            # A single myRIO packet contains all sensor channels used by the
            # dashboard modules; each page interprets a subset differently.
            time_stamp = request.form.get('time')
            x = float(request.form.get('x_axis'))
            y = float(request.form.get('y_axis'))
            z = float(request.form.get('z_axis'))
            light = float(request.form.get('light'))
            temp = float(request.form.get('temp'))
            tilt = float(request.form.get('tilt'))
            mag = float(request.form.get('mag'))
            sound = float(request.form.get('sound'))
            flame = float(request.form.get('flame'))

            magnitude = (x ** 2 + y ** 2 + z ** 2) ** 0.5
            tilt_angles = get_tilt_angles(x, y, z)

            db = SessionLocal()

            # Prototype defaults: each reading is attached to one demo worker,
            # package, and machine so the event tables keep useful foreign keys.
            person_name = "Bob"
            person = db.query(Person).filter_by(name=person_name).first()
            if not person:
                person = Person(name=person_name)
                db.add(person)
                db.commit()  # commit to get the ID

            # Package
            package_name = "Package1"
            package = db.query(Package).filter_by(name=package_name).first()
            if not package:
                package = Package(name=package_name)
                db.add(package)
                db.commit()

            # Machine
            machine_name = "Machine1"
            machine = db.query(Machine).filter_by(name=machine_name).first()
            if not machine:
                machine = Machine(name=machine_name)
                db.add(machine)
                db.commit()

            # --- Insert into tables ---

            # Reading (generic)
            new_reading = Reading(
                time_stamp=time_stamp,
                x=x, y=y, z=z,
                light=light, temp=temp,
                tilt=tilt, mag=mag,
                sound=sound, flame=flame
            )
            db.add(new_reading)

            # ToolDrop (linked to machine)
            tool_drop = ToolDrop(
                time_stamp=time_stamp,
                magnetic=mag,
                magnitude=magnitude,
                sound=sound,
                machine_id=machine.id
            )
            db.add(tool_drop)

            # MachineVibration (linked to machine)
            machine_vibration = MachineVibration(
                time_stamp=time_stamp,
                tilt=tilt,
                x=x, y=y, z=z,
                magnitude=magnitude,
                machine_id=machine.id
            )
            db.add(machine_vibration)

            # AGV (linked to machine)
            agv = AGV(
                magnitude=magnitude,
                time_stamp=time_stamp,
                tilt=tilt,
                pitch=tilt_angles["pitch"],
                roll=tilt_angles["roll"],
                machine_id=machine.id
            )
            db.add(agv)

            # PackageDrop (linked to package)
            package_drop = PackageDrop(
                time_stamp=time_stamp,
                magnitude=magnitude,
                sound=sound,
                package_id=package.id
            )
            db.add(package_drop)

            # Worker (linked to person)
            worker = Worker(
                time_stamp=time_stamp,
                x=x, y=y, z=z,
                posture=tilt, motion=x, alertness=y,
                magnitude=magnitude,
                temperature=temp,
                light=light,
                person_id=person.id
            )
            db.add(worker)

            # Commit once for all inserts
            db.commit()
            db.close()

            # Write raw accel
            csv_utils.write_accel_to_csv(time_stamp, x, y, z, light, temp, tilt, mag, sound, flame, filepath=data_file("accel.csv"))


            try:
                if os.path.exists(data_file('accel.csv')):
                    df = pd.read_csv(data_file('accel.csv'))

                    if not df.empty and 'magnitude' in df.columns:
                        # CSV logs are kept alongside SQLite because they are
                        # easy to inspect, export, and use as validation traces.
                        latest_magnitude = df['magnitude'].iloc[-1]
                        latest_sound = df['sound'].iloc[-1]

                        new_data = {
                            'timestamp': datetime.now().isoformat(),
                            'magnitude': latest_magnitude,
                            'sound': latest_sound
                        }

                        output_file = data_file('tool-drop-detection.csv')
                        should_add = True

                        if os.path.exists(output_file):
                            existing_df = pd.read_csv(output_file)

                            if should_add:
                                new_df = pd.concat([existing_df, pd.DataFrame([new_data])], ignore_index=True)
                            else:
                                new_df = existing_df
                        else:
                            new_df = pd.DataFrame([new_data])

                        if should_add and update_flags['tool_drop']:
                            new_df.to_csv(output_file, index=False)
                            print(f"Added to tool-drop-detection.csv: magnitude={latest_magnitude}")
                        else:
                            print(f"Skipped duplicate magnitude: {latest_magnitude}")

                        if len(df) > 0:
                            latest_row = df.iloc[-1]
                            full_data_entry = {
                                'timestamp': datetime.now().isoformat(),
                                'x_axis': latest_row.get('x_accel', latest_row.get('x_axis', 0)),
                                'y_axis': latest_row.get('y_accel', latest_row.get('y_axis', 0)),
                                'z_axis': latest_row.get('z_accel', latest_row.get('z_axis', 0)),
                                'magnitude': latest_magnitude
                            }

                            full_output_file = data_file('full-accel-data.csv')
                            should_add_full = True

                            if os.path.exists(full_output_file):
                                existing_full_df = pd.read_csv(full_output_file)

                                if should_add_full:
                                    new_full_df = pd.concat([existing_full_df, pd.DataFrame([full_data_entry])],
                                                            ignore_index=True)
                                else:
                                    new_full_df = existing_full_df
                            else:
                                new_full_df = pd.DataFrame([full_data_entry])

                            if should_add_full and update_flags['vibration']:
                                new_full_df.to_csv(full_output_file, index=False)
                                print(
                                    f"Added to full-accel-data.csv: x={full_data_entry['x_axis']}, y={full_data_entry['y_axis']}, z={full_data_entry['z_axis']}, magnitude={full_data_entry['magnitude']}")
                            else:
                                print(f"Skipped duplicate full data entry")

                        # -------- AGV Data Export --------
                        fall_val = latest_row.get('fall', None)

                        tilt1 = get_tilt_angles(latest_row['x_axis'], latest_row['y_axis'], latest_row['z_axis'])
                        pitch = tilt1['pitch']
                        roll = tilt1['roll']

                        agv_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'x_axis': latest_row['x_axis'],
                            'y_axis': latest_row['y_axis'],
                            'z_axis': latest_row['z_axis'],
                            'fall': fall_val,
                            'pitch': pitch,
                            'roll': roll,
                            'tilt': tilt
                        }

                        agv_file = data_file('agv-data.csv')
                        if os.path.exists(agv_file) and update_flags['agv']:
                            agv_df = pd.read_csv(agv_file)
                            agv_df = pd.concat([agv_df, pd.DataFrame([agv_entry])], ignore_index=True)
                        elif update_flags['agv']:
                            agv_df = pd.DataFrame([agv_entry])
                        agv_df.to_csv(agv_file, index=False)
                        print(f"AGV entry added: {agv_entry}")

                        # -------- Posture Data Export --------
                        try:
                            row_id = len(df)
                            x_axis = float(latest_row['x_axis'])
                            y_axis = float(latest_row['y_axis'])
                            z_axis = float(latest_row['z_axis'])
                            light = float(latest_row['light'])
                            temp = float(latest_row['temp'])

                            posture = abs(x_axis) + 3
                            motion = abs(y_axis) + 3
                            alertness = abs(z_axis) + 2

                            posture_entry = {
                                'timestamp': datetime.now().isoformat(),
                                'id': row_id,
                                'posture': posture,
                                'motion': motion,
                                'alertness': alertness,
                                'fall': fall_val,
                                'light': light,
                                'temp': temp
                            }

                            posture_file = data_file('posture-data.csv')
                            if os.path.exists(posture_file) and update_flags['worker_monitoring']:
                                posture_df = pd.read_csv(posture_file)
                                posture_df = pd.concat([posture_df, pd.DataFrame([posture_entry])], ignore_index=True)
                            elif update_flags['worker_monitoring']:
                                posture_df = pd.DataFrame([posture_entry])

                            posture_df.to_csv(posture_file, index=False)
                            print(f"Posture entry added: {posture_entry}")

                        except Exception as posture_err:
                            print(f"Posture export error: {posture_err}")

                        # -------- Collision Data Export --------
                        collision_entry = {
                            'id': len(df),
                            'fall': fall_val,
                            'magnitude': latest_magnitude,
                            'timestamp': datetime.now().isoformat(),
                            'light': light,
                            'temp': temp
                        }

                        collision_file = data_file('collision-data.csv')
                        if os.path.exists(collision_file) and update_flags['agv']:
                            collision_df = pd.read_csv(collision_file)
                            collision_df = pd.concat([collision_df, pd.DataFrame([collision_entry])], ignore_index=True)
                        elif update_flags['agv']:
                            collision_df = pd.DataFrame([collision_entry])
                        collision_df.to_csv(collision_file, index=False)
                        print(f"Collision entry added: {collision_entry}")

            except Exception as tool_csv_error:
                print(f"Tool CSV processing error: {tool_csv_error}")

        except (ValueError, TypeError) as e:
            return f"Invalid input: {e}", 400

    elif request.method == 'GET':
        try:
            if not os.path.exists(data_file('accel.csv')):
                return jsonify({'error': 'accel.csv file not found', 'status': 'failed'}), 404

            df = pd.read_csv(data_file('accel.csv'))
            if df.empty:
                return jsonify({'error': 'accel.csv file is empty', 'status': 'failed'}), 400
            if 'magnitude' not in df.columns:
                return jsonify({'error': 'magnitude column not found in accel.csv', 'status': 'failed'}), 400

            latest_magnitude = df['magnitude'].iloc[-1]

            output_file = data_file('tool-drop-detection.csv')
            if os.path.exists(output_file):
                tool_df = pd.read_csv(output_file)
                total_records = len(tool_df)
                latest_tool_entry = tool_df.iloc[-1] if not tool_df.empty else None
            else:
                total_records = 0
                latest_tool_entry = None

            full_output_file = data_file('full-accel-data.csv')
            if os.path.exists(full_output_file):
                full_df = pd.read_csv(full_output_file)
                full_total_records = len(full_df)
                latest_full_entry = full_df.iloc[-1] if not full_df.empty else None
            else:
                full_total_records = 0
                latest_full_entry = None

            return jsonify({
                'message': 'API status and export information',
                'accel_csv': {
                    'total_records': len(df),
                    'latest_magnitude': float(latest_magnitude),
                    'columns': list(df.columns)
                },
                'tool_drop_detection': {
                    'file_exists': os.path.exists(output_file),
                    'total_records': total_records,
                    'latest_entry': {
                        'magnitude': float(latest_tool_entry['magnitude']) if latest_tool_entry is not None else None,
                        'timestamp': latest_tool_entry['timestamp'] if latest_tool_entry is not None else None
                    } if latest_tool_entry is not None else None
                },
                'full_accel_data': {
                    'file_exists': os.path.exists(full_output_file),
                    'total_records': full_total_records,
                    'latest_entry': {
                        'x_axis': float(latest_full_entry['x_axis']) if latest_full_entry is not None else None,
                        'y_axis': float(latest_full_entry['y_axis']) if latest_full_entry is not None else None,
                        'z_axis': float(latest_full_entry['z_axis']) if latest_full_entry is not None else None,
                        'magnitude': float(latest_full_entry['magnitude']) if latest_full_entry is not None else None,
                        'timestamp': latest_full_entry['timestamp'] if latest_full_entry is not None else None
                    } if latest_full_entry is not None else None
                },
                'status': 'success'
            }), 200

        except pd.errors.EmptyDataError:
            return jsonify({'error': 'accel.csv file is empty or corrupted', 'status': 'failed'}), 400
        except pd.errors.ParserError:
            return jsonify({'error': 'Error parsing accel.csv file', 'status': 'failed'}), 400
        except Exception as e:
            return jsonify({'error': f'Unexpected error: {str(e)}', 'status': 'failed'}), 500

    return ""


@app.route('/api/read')
def get_tooldrop_data():
    df = pd.read_csv(data_file('accel.csv'))
    latest = df.iloc[-1]  # Get the last row
    return jsonify({
        'id': int(latest['id']),
        'x_axis': float(latest['x_axis']),
        'y_axis': float(latest['y_axis']),
        'z_axis': float(latest['z_axis']),
        'fall': int(latest['fall']),
        'LED': int(latest['LED']),
        'magnitude': float(latest['magnitude']),
        'light': float(latest['light']),
        'temp': float(latest['temp']),
        'tilt': float(latest['tilt']),
        'mag': float(latest['mag']),
        'sound': float(latest['sound']),
        'flame': float(latest['flame'])
    })


@app.route('/tool-drop-detection.csv')
def tool_drop_data_csv():
    try:
        return send_file(data_file("tool-drop-detection.csv"), as_attachment=True, download_name="tool-drop-detection.csv")
    except FileNotFoundError:
        return "Collision data not found", 404


@app.route('/full-accel-data.csv', methods=['GET'])
def download_full_accel_csv():
    try:
        # Check if file exists
        if not os.path.exists(data_file('full-accel-data.csv')):
            return jsonify({
                'error': 'Full accelerometer data CSV file not found',
                'status': 'failed'
            }), 404

        # Send the file
        return send_file(data_file('full-accel-data.csv'),
                         mimetype='text/csv',
                         as_attachment=False)

    except Exception as e:
        return jsonify({
            'error': f'Error serving full accelerometer CSV file: {str(e)}',
            'status': 'failed'
        }), 500


@app.route('/agv-data.csv', methods=['GET'])
def download_agv_csv():
    if not os.path.exists(data_file('agv-data.csv')):
        return jsonify({'error': 'AGV data file not found', 'status': 'failed'}), 404
    return send_file(data_file('agv-data.csv'), mimetype='text/csv', as_attachment=False)


@app.route('/collision-data.csv')
def export_collision_csv():
    try:
        return send_file(data_file("collision-data.csv"), as_attachment=True, download_name="collision-data.csv")
    except FileNotFoundError:
        return "Collision data not found", 404


@app.route('/posture-data.csv')
def posture_data_csv():
    try:
        return send_file(data_file("posture-data.csv"), as_attachment=True, download_name="posture-data.csv")
    except FileNotFoundError:
        return "Collision data not found", 404


@app.route('/api/toggle_updates', methods=['POST'])
def toggle_updates():
    data = request.json
    target = data.get('target')
    if target not in update_flags:
        return jsonify({'error': 'Invalid target'}), 400

    # Flip the current flag
    update_flags[target] = not update_flags[target]

    return jsonify({'status': 'success', 'target': target, 'is_updating': update_flags[target]})


@app.route('/addresses')
def address_page():
    return render_template('address.html')


addresses_str = ""
@app.route('/api/addresses', methods=['GET', 'POST'])
def update_addresses():
    global addresses_str

    if request.method == 'POST':
        # Try to get JSON first
        data = request.get_json(silent=True)
        if data and 'addresses' in data:
            addresses_str = data['addresses'].strip()
            write_text_file(ADDRESSES_FILE, addresses_str)
            print(1, addresses_str)
            return "OK", 200

        return "Bad Request: Missing 'addresses' field", 400

    # GET method handling here...
    return addresses_str or read_text_file(ADDRESSES_FILE)


addresses_str2 = ""


@app.route('/api/addresses_helper', methods=['GET', 'POST'])
def addresses_helper():
    global addresses_str2

    if request.method == 'POST':
        if 'addresses' in request.form:
            addresses_str2 = request.form['addresses'].strip()
            write_text_file(ADDRESSES_FILE, addresses_str2)
            print("[myRIO data received]", addresses_str2)
            return "OK", 200
        else:
            return "Bad Request: Missing 'addresses' field", 400

    # GET request — return the stored string
    return addresses_str2 or addresses_str or read_text_file(ADDRESSES_FILE)

addresses_str3 = ""

@app.route('/api/id_helper', methods=['GET', 'POST'])
def id_helper():
    global addresses_str3

    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data and 'ID' in data:
            addresses_str3 = data['ID'].strip()
            write_text_file(DEVICE_ID_FILE, addresses_str3)
            print("[myRIO data received id]", addresses_str3)
            return "OK", 200
        else:
            return "Bad Request: Missing 'ID' field", 400

    # GET request — return the stored string
    return addresses_str3 or read_text_file(DEVICE_ID_FILE)

addresses_str4 = ""  # global variable to store the single ID

@app.route('/api/id_display', methods=['GET', 'POST'])
def id_display():
    global addresses_str4

    if request.method == 'POST':
        if 'ID' in request.form:
            addresses_str4 = request.form['ID'].strip()
            write_text_file(DEVICE_ID_FILE, addresses_str4)
            print("[myRIO data received id]", addresses_str4)
            return "OK", 200
        else:
            return "Bad Request: Missing 'ID' field", 400
    return addresses_str4 or addresses_str3 or read_text_file(DEVICE_ID_FILE)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)



