from datetime import datetime
from flask import Flask, redirect, request, jsonify, session
from db import get_connection
from werkzeug.security import generate_password_hash
from utils import generate_random_password
from email_service import send_email
from werkzeug.security import check_password_hash
import os
from flask import render_template
from functools import wraps

from dotenv import load_dotenv # type: ignore

load_dotenv()

app = Flask(__name__)

# app.secret_key = "super_secret_key"
app.secret_key = os.getenv("SECRET_KEY")



@app.route("/")
def home():
  return render_template("login.html")




@app.errorhandler(Exception)
def handle_exception(e):
    return {"message": "Something went wrong"}, 500


#login in student account 

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "student_id" not in session:
            return {"message": "Login required"}, 401
        return f(*args, **kwargs)
    return decorated



#student login
@app.route("/student/login", methods=["POST"])
def student_login():
    data = request.json
    student_id = data.get("student_id")
    password = data.get("password")

    if not student_id or not password:
        return {"message": "Student ID and password required"}, 400

    conn = get_connection()
    cur = conn.cursor()

    # 🔹 Fetch hashed password
    cur.execute(
        "SELECT password FROM student_login WHERE student_id = %s",
        (student_id,)
    )
    row = cur.fetchone()

    cur.close()
    conn.close()

    # 🔹 Check hash
    if not row or not check_password_hash(row[0], password):
        return {"message": "Invalid credentials"}, 401

    # 🔹 Login success
    session["student_id"] = student_id
    return {"message": "Login successful"}


#student dashboard
@app.route("/student/dashboard")
def student_dashboard():
    if "student_id" not in session:
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT student_name
        FROM student
        WHERE student_id = %s
    """, (session["student_id"],))

    row = cur.fetchone()
    cur.close()
    conn.close()

    student_name = row[0] if row else "Student"

    return render_template(
        "student_dashboard.html",
        student_name=student_name
    )



#student_profile
@app.route("/student/profile", methods=["GET"])
@student_required
def student_profile():
    student_id = session.get("student_id")

    if not student_id:
        return {"message": "Not logged in"}, 401

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT student_id, student_name, dob, email, year_of_admission
        FROM student
        WHERE student_id = %s
    """, (student_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"message": "Student not found"}, 404

    return {
        "student_id": row[0],
        "name": row[1],
        "dob": str(row[2]),
        "email": row[3],
        "year_of_admission": row[4]
    }



# see guardian details
@app.route("/student/guardian", methods=["GET"])
@student_required
def student_guardian():
    student_id = session.get("student_id")

    if not student_id:
        return {"message": "Not logged in"}, 401

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT g.guardian_name, g.email, g.phone
        FROM guardian g 
        JOIN student s ON g.student_id = s.student_id
        WHERE s.student_id = %s
    """, (student_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"message": "Guardian not assigned"}, 404

    return {
        "guardian_name": row[0],
        "email": row[1],
        "phone": row[2]
    }

@app.route("/student/mentor", methods=["GET"])
@student_required
def student_mentor():
    student_id = session.get("student_id")

    if not student_id:
        return {"message": "Not logged in"}, 401

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT m.name, m.email, m.cabin
        FROM student s
        JOIN mentor m ON s.mentor_id = m.faculty_id
        WHERE s.student_id = %s
    """, (student_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"message": "Mentor not assigned"}, 404

    return {
        "mentor_name": row[0],
        "email": row[1],
        "cabin": row[2]
    }

# see academic details
@app.route("/student/academic", methods=["GET"])
@student_required
def student_academic():
    student_id = session.get("student_id")

    if not student_id:
        return {"message": "Not logged in"}, 401

    conn = get_connection()
    cur = conn.cursor()

    #  Academic details (course + branch)
    cur.execute("""
        SELECT
            c.course_name,
            b.branch_name
        FROM student s
        JOIN branch b ON s.branch_id = b.branch_id
        JOIN course c ON b.course_id = c.course_id
        WHERE s.student_id = %s
    """, (student_id,))

    academic = cur.fetchone()

    if not academic:
        cur.close()
        conn.close()
        return {"message": "Academic data not found"}, 404

    # 2️⃣ Semester-wise SGPA
    cur.execute("""
        SELECT sem.semester_no, sr.sgpa
        FROM semester_result sr
        JOIN semester sem ON sr.semester_id = sem.semester_id
        WHERE sr.student_id = %s
        ORDER BY sem.semester_no
    """, (student_id,))

    semester_rows = cur.fetchall()

    # 3️⃣ CGPA calculation
    cur.execute("""
        SELECT ROUND(AVG(sgpa), 2)
        FROM semester_result
        WHERE student_id = %s
    """, (student_id,))

    cgpa = cur.fetchone()[0]

    cur.close()
    conn.close()

    # Format semester results
    semester_results = [
        {
            "semester": row[0],
            "sgpa": float(row[1])
        }
        for row in semester_rows
    ]

    return {
        "course": academic[0],
        "branch": academic[1],
        "semester_results": semester_results,
        "cgpa": float(cgpa) if cgpa is not None else None
    }


@app.route("/student/fees", methods=["GET"])
@student_required
def student_fees():
    student_id = session.get("student_id")

    if not student_id:
        return {"message": "Not logged in"}, 401

    semester_id = request.args.get("semester_id")

    conn = get_connection()
    cur = conn.cursor()

    # If no semester selected → use current semester
    if not semester_id:
        cur.execute("""
            SELECT current_semester_id
            FROM student
            WHERE student_id = %s
        """, (student_id,))
        semester_id = cur.fetchone()[0]

    # Get course + hostel fee
    cur.execute("""
        SELECT 
            b.fee_per_semester,
            COALESCE(h.hostel_fee_semester, 0)
        FROM student s
        JOIN branch b ON s.branch_id = b.branch_id
        LEFT JOIN hostel_allocation ha ON s.student_id = ha.student_id
        LEFT JOIN room r ON ha.room_id = r.room_id
        LEFT JOIN hostel h ON r.hostel_id = h.hostel_id
        WHERE s.student_id = %s
    """, (student_id,))

    course_fee, hostel_fee = cur.fetchone()
    total_fee = course_fee + hostel_fee

    # Calculate paid
    cur.execute("""
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM fee_payment
        WHERE student_id = %s AND semester_id = %s
    """, (student_id, semester_id))

    paid = cur.fetchone()[0]
    due = total_fee - paid

    cur.close()
    conn.close()

    return {
        "semester_id": int(semester_id),
        "total_fee": float(total_fee),
        "paid": float(paid),
        "due": float(due)
    }



@app.route("/student/pay", methods=["POST"])
@student_required
def pay_fee():
    student_id = session.get("student_id")

    if not student_id:
        return {"message": "Not logged in"}, 401

    data = request.json
    amount = data.get("amount")
    semester_id = data.get("semester_id")

    if amount is None or amount <= 0:
        return {"message": "Invalid amount"}, 400

    if not semester_id:
        return {"message": "Semester not selected"}, 400

    conn = get_connection()
    cur = conn.cursor()

    # Verify semester exists
    cur.execute("""
        SELECT semester_id FROM semester WHERE semester_id = %s
    """, (semester_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return {"message": "Invalid semester"}, 400

    # Get total fee (course + hostel)
    cur.execute("""
        SELECT 
            b.fee_per_semester + COALESCE(h.hostel_fee_semester, 0)
        FROM student s
        JOIN branch b ON s.branch_id = b.branch_id
        LEFT JOIN hostel_allocation ha ON s.student_id = ha.student_id
        LEFT JOIN room r ON ha.room_id = r.room_id
        LEFT JOIN hostel h ON r.hostel_id = h.hostel_id
        WHERE s.student_id = %s
    """, (student_id,))
    
    total_fee = cur.fetchone()[0]

    # Get already paid
    cur.execute("""
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM fee_payment
        WHERE student_id = %s AND semester_id = %s
    """, (student_id, semester_id))
    paid = cur.fetchone()[0]

    due = total_fee - paid

    if due <= 0:
        cur.close()
        conn.close()
        return {"message": "Fee already fully paid"}, 400

    # ❌ prevent overpayment
    if amount > due:
        cur.close()
        conn.close()
        return {"message": "Amount exceeds due fee"}, 400

    # ✅ record payment
    cur.execute("""
        INSERT INTO fee_payment (student_id, semester_id, amount_paid)
        VALUES (%s, %s, %s)
    """, (student_id, semester_id, amount))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Payment successful"}



@app.route("/student/payments", methods=["GET"])
@student_required
def payment_history():
    student_id = session.get("student_id")

    if not student_id:
        return {"message": "Not logged in"}, 401
    
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT semester_id, amount_paid, paid_at
        FROM fee_payment
        WHERE student_id = %s
        ORDER BY paid_at DESC
    """, (student_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return {
        "payments": [
            {
                "semester": r[0],
                "amount": float(r[1]),
                "paid_at": r[2].strftime("%Y-%m-%d %H:%M")
            }
            for r in rows
        ]
    }


@app.route("/student/hostel", methods=["GET"])
@student_required
def student_hostel():
    student_id = session.get("student_id")

    if not student_id:
        return {"message": "Not logged in"}, 401

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            h.hostel_name,
            h.hostel_type,
            r.room_no
        FROM hostel_allocation ha
        JOIN room r ON ha.room_id = r.room_id
        JOIN hostel h ON r.hostel_id = h.hostel_id
        WHERE ha.student_id = %s
    """, (student_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"message": "Hostel not allotted"}, 200

    return {
        "hostel_name": row[0],
        "hostel_type": row[1],
        "room_no": row[2]
    }



# admin ka ilaka 
#1




from functools import wraps
from flask import redirect, session

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            return redirect("/")   # go back to login page
        return f(*args, **kwargs)
    return decorated






@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.json
    admin_id = data.get("admin_id")
    password = data.get("password")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT admin_id FROM admin_login
        WHERE admin_id = %s AND password = %s
    """, (admin_id, password))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"message": "Invalid admin credentials"}, 401

    session["admin_id"] = admin_id
    return {"message": "Admin login successful"}



@app.route("/admin/full-student/<student_id>", methods=["GET"])
@admin_required
def admin_full_student(student_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            s.student_id,
            s.student_name,
            s.email,
            s.dob,
            s.year_of_admission,
            c.course_name,
            b.branch_name,
            sem.semester_no,
            m.name AS mentor_name,
            m.email AS mentor_email,
            g.guardian_name,
            g.phone,
            h.hostel_name,
            r.room_no
        FROM student s
        JOIN branch b ON s.branch_id = b.branch_id
        JOIN course c ON b.course_id = c.course_id
        JOIN semester sem ON s.current_semester_id = sem.semester_id
        LEFT JOIN mentor m ON s.mentor_id = m.faculty_id
        LEFT JOIN guardian g ON s.student_id = g.student_id
        LEFT JOIN hostel_allocation ha ON s.student_id = ha.student_id
        LEFT JOIN room r ON ha.room_id = r.room_id
        LEFT JOIN hostel h ON r.hostel_id = h.hostel_id
        WHERE s.student_id = %s
    """, (student_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"message": "Student not found"}, 404

    return {
        "student_id": row[0],
        "name": row[1],
        "email": row[2],
        "dob": str(row[3]),
        "year_of_admission": row[4],
        "course": row[5],
        "branch": row[6],
        "semester": row[7],
        "mentor": row[8],
        "mentor_email": row[9],
        "guardian": row[10],
        "guardian_phone": row[11],
        "hostel": row[12],
        "room": row[13]
    }


@app.route("/admin/allocate-hostel", methods=["POST"])
@admin_required
def allocate_hostel():

    if "admin_id" not in session:
        return {"message": "Admin not logged in"}, 401

    data = request.json
    student_id = data.get("student_id")
    hostel_id = data.get("hostel_id")
    room_no = data.get("room_no")

    if not student_id or not hostel_id or not room_no:
        return {"message": "All fields required"}, 400

    conn = get_connection()
    cur = conn.cursor()

    try:
        # 1️⃣ Get room_id
        cur.execute("""
            SELECT room_id
            FROM room
            WHERE hostel_id = %s AND room_no = %s
        """, (hostel_id, room_no))

        room_row = cur.fetchone()

        if not room_row:
            return {"message": "Room not found in this hostel"}, 404

        room_id = room_row[0]

        # 2️⃣ Get hostel capacity
        cur.execute("""
            SELECT hostel_type
            FROM hostel
            WHERE hostel_id = %s
        """, (hostel_id,))

        hostel_type = cur.fetchone()[0]

        # Extract capacity number from string like "2sharing"
        capacity = int(''.join(filter(str.isdigit, hostel_type)))

        # 3️⃣ Count current occupants
        cur.execute("""
            SELECT COUNT(*)
            FROM hostel_allocation
            WHERE room_id = %s
        """, (room_id,))

        occupied = cur.fetchone()[0]

        if occupied >= capacity:
            return {"message": "Room is full"}, 400

        # 4️⃣ Insert or update allocation
        cur.execute("""
            INSERT INTO hostel_allocation (student_id, room_id)
            VALUES (%s, %s)
            ON CONFLICT (student_id)
            DO UPDATE SET room_id = EXCLUDED.room_id
        """, (student_id, room_id))

        conn.commit()
        return {"message": "Hostel allocated successfully"}

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}, 500

    finally:
        cur.close()
        conn.close()



@app.route("/admin/update-student-field", methods=["PUT"])
@admin_required
def admin_update_student_field():
    if "admin_id" not in session:
        return {"message": "Admin not logged in"}, 401

    data = request.json
    student_id = data.get("student_id")
    field = data.get("field")
    value = data.get("value")

    # Whitelist allowed fields (VERY IMPORTANT)
    allowed_fields = {
        "name": "student_name",
        "email": "email",
        
    }

    if field not in allowed_fields:
        return {"message": "Invalid field"}, 400

    column = allowed_fields[field]

    conn = get_connection()
    cur = conn.cursor()

    try:
        query = f"""
            UPDATE student
            SET {column} = %s
            WHERE student_id = %s
        """
        cur.execute(query, (value, student_id))

        if cur.rowcount == 0:
            return {"message": "Student not found"}, 404

        conn.commit()
        return {"message": f"{field} updated successfully"}

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}, 500

    finally:
        cur.close()
        conn.close()



@app.route("/admin/add-student", methods=["POST"])
@admin_required
def admin_add_student():
    if "admin_id" not in session:
        return {"message": "Admin not logged in"}, 401

    data = request.json
    conn = get_connection()
    cur = conn.cursor()
    plain_password = generate_random_password(8)
    hashed_password = generate_password_hash(plain_password)

    try:
        # check duplicate
        cur.execute(
            "SELECT 1 FROM student WHERE student_id = %s",
            (data["student_id"],)
        )
        if cur.fetchone():
            return {"message": "Student already exists"}, 400

        # insert student
        cur.execute("""
            INSERT INTO student (
                student_id, student_name, dob, email,
                year_of_admission, branch_id, gender_id,
                mentor_id, current_semester_id
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data["student_id"],
            data["name"],
            data["dob"],
            data["email"],
            data["year_of_admission"],
            data["branch_id"],
            data["gender_id"],
            data["mentor_id"],
            data["current_semester_id"]
        ))

   

        cur.execute("""
        INSERT INTO student_login (student_id, password)
        VALUES (%s, %s)
        """, (data["student_id"], hashed_password))
        
        send_email(
            data["email"],
            "Student Portal Login Credentials",
            f"""
            Hello {data['name']},

            Your Student Portal account has been created.

            Student ID: {data["student_id"]}
            Temporary Password: {plain_password}

            Please login and change your password immediately."""
        )
        conn.commit()
        return {"message": "Student added successfully"}

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}, 500

    finally:
        cur.close()
        conn.close()

@app.route("/admin/delete-student/<student_id>", methods=["DELETE"])
@admin_required
def admin_delete_student(student_id):
   

    conn = get_connection()
    cur = conn.cursor()

    try:
        # delete dependent data first
        cur.execute("DELETE FROM hostel_allocation WHERE student_id = %s", (student_id,))
        cur.execute("DELETE FROM fee_payment WHERE student_id = %s", (student_id,))
        cur.execute("DELETE FROM semester_result WHERE student_id = %s", (student_id,))
        cur.execute("DELETE FROM student_login WHERE student_id = %s", (student_id,))
        cur.execute("DELETE FROM guardian WHERE student_id = %s", (student_id,))

        # finally delete student
        cur.execute("DELETE FROM student WHERE student_id = %s", (student_id,))

        if cur.rowcount == 0:
            return {"message": "Student not found"}, 404

        conn.commit()
        return {"message": "Student deleted successfully"}

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}, 500

    finally:
        cur.close()
        conn.close()


@app.route("/student/logout", methods=["POST"])
def student_logout():
    session.pop("student_id", None)
    return {"message": "Logged out successfully"}


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin_id", None)
    return {"message": "Admin logged out successfully"}





from utils import generate_otp, otp_expiry_time
from email_service import send_email

@app.route("/student/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    student_id = data["student_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT email FROM student WHERE student_id=%s", (student_id,))
    row = cur.fetchone()
    if not row:
        return {"message": "If student exists, OTP sent"}, 200

    otp = generate_otp()
    expiry = otp_expiry_time()

    cur.execute("""
        INSERT INTO password_reset_otp (student_id, otp, expires_at)
        VALUES (%s,%s,%s)
        ON CONFLICT (student_id)
        DO UPDATE SET otp=%s, expires_at=%s
    """, (student_id, otp, expiry, otp, expiry))

    send_email(
        row[0],
        "Password Reset OTP",
        f"Your OTP is {otp}. Valid for 10 minutes."
    )

    conn.commit()
    return {"message": "OTP sent"}


from werkzeug.security import generate_password_hash

@app.route("/student/reset-password", methods=["POST"])
def reset_password():
    data = request.json

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT otp, expires_at FROM password_reset_otp
        WHERE student_id=%s
    """, (data["student_id"],))

    row = cur.fetchone()
    if not row or row[0] != data["otp"] or row[1] < datetime.now():
        return {"message": "Invalid or expired OTP"}, 400

    hashed = generate_password_hash(data["new_password"])

    cur.execute("""
        UPDATE student_login SET password=%s WHERE student_id=%s
    """, (hashed, data["student_id"]))

    cur.execute("""
        DELETE FROM password_reset_otp WHERE student_id=%s
    """, (data["student_id"],))

    conn.commit()
    return {"message": "Password updated successfully"}


@app.route("/forgot-password")
def forgot_password_page():
    return render_template("forgot_password.html")

@app.route("/reset-password")
def reset_password_page():
    return render_template("reset_password.html")
 



@app.route("/admin/dashboard")
# @admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")




@app.route("/db-test")
def db_test():
    conn = get_connection()
    conn.close()
    return {"status": "Database connected"}


if __name__ == "__main__":
   app.run(debug=True, port=5000)




# APIs which are not implemented yet but can be added in future for more functionality


# #2  to see all students of a particular course and branch (for admin)
# @app.route("/admin/students", methods=["POST"])
# # @admin_required
# def admin_get_students():
#     if "admin_id" not in session:
#         return {"message": "Admin not logged in"}, 401

#     data = request.json
#     course_id = data.get("course_id")
#     branch_id = data.get("branch_id")

#     if not course_id or not branch_id:
#         return {"message": "course_id and branch_id are required"}, 400

#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute("""
#         SELECT
#             s.student_id,
#             s.student_name,
#             c.course_name,
#             b.branch_name,
#             sem.semester_no
#         FROM student s
#         JOIN branch b ON s.branch_id = b.branch_id
#         JOIN course c ON b.course_id = c.course_id
#         JOIN semester sem ON s.current_semester_id = sem.semester_id
#         WHERE c.course_id = %s
#           AND b.branch_id = %s
#         ORDER BY s.student_id
#     """, (course_id, branch_id))

#     rows = cur.fetchall()
#     cur.close()
#     conn.close()

#     return {
#         "students": [
#             {
#                 "student_id": r[0],
#                 "name": r[1],
#                 "course": r[2],
#                 "branch": r[3],
#                 "semester": r[4]
#             }
#             for r in rows
#         ]
#     }


#5
# @app.route("/admin/promote", methods=["POST"])
# # @admin_required
# def promote_student():
#     if "admin_id" not in session:
#         return {"message": "Admin not logged in"}, 401

#     data = request.json
#     student_id = data.get("student_id")

#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute("""
#         UPDATE student
#         SET current_semester_id = current_semester_id + 1
#         WHERE student_id = %s
#     """, (student_id,))

#     conn.commit()
#     cur.close()
#     conn.close()

#     return {"message": "Student promoted successfully"}
