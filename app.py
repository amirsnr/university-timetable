from datetime import datetime
import io
from flask import Flask, jsonify, request, render_template, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from auth import auth_bp, token_required, admin_required, decode_token
from db import get_db_connection, conn

app = Flask(__name__)

app.config['SECRET_KEY'] = 'mysecretkey'
app.register_blueprint(auth_bp)

# === Index Page ===
@app.route('/')
def index():
    token = request.cookies.get('token')
    is_admin = False
    if token:
        try:
            data = decode_token(token)
            email = data['email']
            cur = conn.cursor()
            cur.execute("SELECT * FROM admins WHERE email = %s", (email,))
            admin = cur.fetchone()
            is_admin = admin is not None
        except:
            pass
    return render_template('index.html', is_admin=is_admin)

# === Timetable Routes ===
@app.route('/timetable', methods=['GET'])
@token_required
def get_timetable(current_user_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM timetable ORDER BY day_of_week, start_time")
        rows = cur.fetchall()
    
        timetable = []
        for row in rows:
            start_time = row[4].strftime('%H:%M') if row[4] else None
            end_time = row[5].strftime('%H:%M') if row[5] else None
            timetable.append({
                "id": row[0],
                "course_name": row[1],
                "room_number": row[2],
                "day_of_week": row[3],
                "start_time": start_time,
                "end_time": end_time,
                "teacher_name": row[6]
            })
        return jsonify(timetable)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/timetable', methods=['POST'])
@admin_required
def add_timetable(admin_id):
    data = request.get_json()
    required_fields = ['course_name', 'room_number', 'day_of_week', 'start_time', 'end_time']
    conn = None

    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields!'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Validate start and end time
        if data['end_time'] <= data['start_time']:
            return jsonify({'message': 'End time must be after start time.', 'error': True}), 400

        # Check for conflicting course in the same time slot
        cur.execute("""
            SELECT * FROM timetable
            WHERE day_of_week = %s
              AND start_time = %s
              AND end_time = %s
        """, (data['day_of_week'], data['start_time'], data['end_time']))
        existing_slot = cur.fetchone()
        if existing_slot:
            return jsonify({'message': 'A subject already exists in this time slot.', 'error': True}), 400

        # Ensure room exists
        cur.execute("SELECT room_id FROM rooms WHERE room_number = %s", (data['room_number'],))
        room = cur.fetchone()
        if not room:
            cur.execute("INSERT INTO rooms (room_number, capacity) VALUES (%s, %s) RETURNING room_id", 
                        (data['room_number'], 100))
            room_id = cur.fetchone()[0]
        else:
            room_id = room[0]

        # Ensure course exists
        cur.execute("SELECT course_id FROM courses WHERE course_name = %s", (data['course_name'],))
        course = cur.fetchone()
        if not course:
            cur.execute("INSERT INTO courses (course_name) VALUES (%s) RETURNING course_id", (data['course_name'],))
            course_id = cur.fetchone()[0]
        else:
            course_id = course[0]

        # Insert into timetable
        cur.execute("""
            INSERT INTO timetable 
            (course_name, room_number, day_of_week, start_time, end_time, teacher_name, course_id, room_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['course_name'],
            data['room_number'],
            data['day_of_week'],
            data['start_time'],
            data['end_time'],
            data.get('teacher_name', ''),
            course_id,
            room_id
        ))

        conn.commit()
        return jsonify({'message': 'Entry added!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/timetable/<int:entry_id>', methods=['PUT'])
@admin_required
def update_timetable(admin_id, entry_id):
    data = request.get_json()
    required_fields = ['course_name', 'room_number', 'day_of_week', 'start_time', 'end_time']
    conn = None

    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields!'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Validate start and end time
        if data['end_time'] <= data['start_time']:
            return jsonify({'message': 'End time must be after start time.', 'error': True}), 400

        # Check for conflicting course in the same time slot (excluding current entry)
        cur.execute("""
            SELECT * FROM timetable
            WHERE day_of_week = %s
              AND start_time = %s
              AND end_time = %s
              AND id != %s
        """, (data['day_of_week'], data['start_time'], data['end_time'], entry_id))
        existing_slot = cur.fetchone()
        if existing_slot:
            return jsonify({'message': 'A subject already exists in this time slot.', 'error': True}), 400

        cur.execute("""
            UPDATE timetable SET
                course_name = %s,
                room_number = %s,
                day_of_week = %s,
                start_time = %s,
                end_time = %s,
                teacher_name = %s
            WHERE id = %s
        """, (
            data['course_name'],
            data['room_number'],
            data['day_of_week'],
            data['start_time'],
            data['end_time'],
            data.get('teacher_name', ''),
            entry_id
        ))
        conn.commit()
        return jsonify({'message': 'Entry updated!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/timetable/<int:entry_id>', methods=['DELETE'])
@admin_required
def delete_timetable(admin_id, entry_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM timetable WHERE id = %s", (entry_id,))
        conn.commit()
        return jsonify({'message': 'Entry deleted!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# === Admin API Routes ===
@app.route('/admin-summary', methods=['GET'])
@admin_required
def admin_summary(admin_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        users_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM admins")
        admins_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM timetable")
        timetable_count = cur.fetchone()[0]
        return jsonify({
            'total_users': users_count,
            'total_admins': admins_count,
            'total_timetable_entries': timetable_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# === Timetable Filtering and PDF Download ===
@app.route('/timetable/filter', methods=['GET'])
@token_required
def filter_timetable(current_user_id):
    day = request.args.get('day')
    course = request.args.get('course')
    conn = None

    query = "SELECT * FROM timetable WHERE 1=1"
    params = []
    if day:
        query += " AND day_of_week = %s"
        params.append(day)
    if course:
        query += " AND course_name = %s"
        params.append(course)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        print("Running filter query:", cur.mogrify(query, params))
        cur.execute(query, params)
        result = cur.fetchall()
        timetable = []
        for row in result:
            start_time = row[4].strftime('%H:%M') if row[4] else None
            end_time = row[5].strftime('%H:%M') if row[5] else None
            timetable.append({
                'id': row[0],
                'course_name': row[1],
                'room_number': row[2],
                'day_of_week': row[3],
                'start_time': start_time,
                'end_time': end_time,
                'teacher_name': row[6]
            })
        return jsonify({'filtered_timetable': timetable}), 200
    except Exception as e:
        print("❌ Error while filtering timetable:", e)
        return jsonify({'message': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/timetable/download', methods=['GET'])
def download_timetable():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, course_name, room_number, day_of_week, start_time, end_time, teacher_name FROM timetable")
        rows = cur.fetchall()
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - 40
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "University Class Timetable")
        y -= 30
        pdf.setFont("Helvetica", 10)
        for row in rows:
            line = f"{row[0]}. {row[1]} | {row[2]} | {row[3]} | {row[4].strftime('%-H:%M')} - {row[5].strftime('%-H:%M')} | {row[6]}"
            pdf.drawString(50, y, line)
            y -= 15
            if y < 50:
                pdf.showPage()
                y = height - 40
        pdf.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="timetable.pdf", mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# === Dropdown Data Endpoints ===
@app.route('/api/courses')
def get_courses():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT course_name FROM courses ORDER BY course_name")
        courses = [row[0] for row in cur.fetchall()]
        return jsonify(courses)
    except Exception as e:
        print(f"Error fetching courses: {str(e)}")
        return jsonify([])
    finally:
        if conn:
            conn.close()

# === App Runner ===
if __name__ == '__main__':
    app.run(debug=True)