import re
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'appa,amma',
    'database': 'attendance'
}

# Email configuration
email_config = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'kathermytheen143143@gmail.com',
    'password': 'qwdf ldlr ssfq lksl'
}

def send_email(to_email, student_name, percentage, message):
    subject = "Attendance and Percentage Alert"
    body = f"Dear {student_name},\n\n{message}\n\nYour attendance percentage is: {percentage}%.\n\nRegards,\nAdmin"

    msg = MIMEMultipart()
    msg['From'] = email_config['email']
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
            server.starttls()
            server.login(email_config['email'], email_config['password'])
            server.sendmail(email_config['email'], to_email, msg.as_string())
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}. Error: {str(e)}")

def update_total_days():
    """
    Updates the total_days column in cs_stu_details and bca_stu_details tables.
    Counts tables matching the structure cs_stu_details_%Y_%m_%d or bca_stu_details_%Y_%m_%d.
    """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Fetch all table names
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        # Extract only table names as a list
        table_names = [t[0] for t in tables]

        # Patterns for cs_stu_details and bca_stu_details tables
        cs_pattern = re.compile(r"^cs_stu_details_\d{4}_\d{2}_\d{2}$")
        bca_pattern = re.compile(r"^bca_stu_details_\d{4}_\d{2}_\d{2}$")

        # Count matching tables
        cs_count = sum(1 for table in table_names if cs_pattern.match(table))
        bca_count = sum(1 for table in table_names if bca_pattern.match(table))

        # Update total_days in cs_stu_details
        update_cs_query = """
        UPDATE cs_stu_details
        SET total_days = %s
        """
        cursor.execute(update_cs_query, (cs_count,))

        # Update total_days in bca_stu_details
        update_bca_query = """
        UPDATE bca_stu_details
        SET total_days = %s
        """
        cursor.execute(update_bca_query, (bca_count,))

        conn.commit()
        print("Total days updated successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error updating total_days: {e}")

    finally:
        conn.close()

def calculate_and_update_percentage():
    """
    Calculate and update the percentage column in cs_stu_details and bca_stu_details tables.
    Percentage = (total_presents / (total_days * 5)) * 100
    """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Update percentage for cs_stu_details
        update_cs_percentage_query = """
        UPDATE cs_stu_details
        SET percentagae = 
            CASE 
                WHEN total_days > 0 THEN ROUND((total_presents / (total_days * 5)) * 100, 2)
                ELSE 0 
            END
        """
        cursor.execute(update_cs_percentage_query)

        # Update percentage for bca_stu_details
        update_bca_percentage_query = """
        UPDATE bca_stu_details
        SET percentagae = 
            CASE 
                WHEN total_days > 0 THEN ROUND((total_presents / (total_days * 5)) * 100, 2)
                ELSE 0 
            END
        """
        cursor.execute(update_bca_percentage_query)

        conn.commit()
        print("Percentage updated successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error updating percentage: {e}")

    finally:
        conn.close()

@app.before_request
def before_request():
    """Ensure total_days is updated before handling any request."""
    update_total_days()
    calculate_and_update_percentage()
    #check_and_notify()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    query = "SELECT aname, pass, allowed_table,role FROM admins WHERE aname = %s AND pass = %s"
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check how many rows exist for this username
        query = "SELECT allowed_table FROM admins WHERE aname = %s AND pass = %s"
        cursor.execute(query, (username, password))
        tables = cursor.fetchall()  # Fetch all allowed tables

        if tables:
            session['user'] = username
            session['role'] = 'admin'
            session['allowed_tables'] = [table[0] for table in tables]  # Store allowed tables in session
            print("DEBUG: Stored Allowed Tables ->", session['allowed_tables'])  # Debug print

            query = "SELECT aname, pass, allowed_table,role FROM admins WHERE aname = %s AND pass = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()

            session['button'] = user[3]

            flash('Login successful!', 'success')
            return redirect(url_for('admin_login'))  
        else:
            flash('Invalid credentials!', 'danger')

        conn.close()

    return render_template('login.html')


@app.route('/admin_login')
def admin_login():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_login.html')


@app.route('/detail')
def detail():
    if 'user' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('login'))
    
    allowed_tables = session.get('allowed_tables')  # Get allowed tables
    print("DEBUG: Retrieved Allowed Tables ->", allowed_tables)  # Debug print

    if not allowed_tables:
        flash("You are not authorized to view any table.", "danger")
        return redirect(url_for('login'))

    return render_template('new_work.html', tables=allowed_tables)  # Pass list of tables


@app.route('/search/<table>', methods=['GET', 'POST'])
def search(table):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    
    # Fetch all students from the selected table
    query = f"SELECT * FROM {table}"
    cursor.execute(query)
    students = cursor.fetchall()

    if request.method == 'POST':
        roll_num = request.form['roll_num']
        # Query the table to find the student by roll number
        query = f"SELECT * FROM {table} WHERE stu_roll_num = %s"
        cursor.execute(query, (roll_num,))
        student = cursor.fetchone()  # Get the first result if any
        if student:
            return render_template('student_detail.html', student=student)
        else:
            return f"No student found with roll number {roll_num}"

    # Render the page with all students from the table
    return render_template('search.html', table=table, students=students)

@app.route('/student_detail/<table>/<roll_num>', methods=['GET'])
def student_detail(table, roll_num):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    # Query the table for the specific student by roll number
    query = f"SELECT * FROM {table} WHERE stu_roll_num = %s"
    cursor.execute(query, (roll_num,))
    student = cursor.fetchone()  # Fetch the student's details
    
    if student:
        return render_template('student_detail.html', student=student)
    else:
        return f"No student found with roll number {roll_num}"



@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    allowed_tables = session.get('allowed_tables', [])  # Get tables from session
    is_super_admin = session.get('button') == 'superradmin'

    return render_template('admin_dashboard.html', tables=allowed_tables,is_super_admin=is_super_admin)


@app.route('/select_period/<table_name>', methods=['GET', 'POST'])
def select_period(table_name):
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Check if total_days exceeds 90 for the given table
        query = f"SELECT MAX(total_days) FROM {table_name}"
        cursor.execute(query)
        total_days = cursor.fetchone()[0]

        if total_days > 90:
            # Redirect to a message page if total_days >= 90
            return redirect(url_for('working_days_message'))

    except Exception as e:
        flash(f"Error: {e}", 'error')

    finally:
        conn.close()

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Get today's date formatted as table name
    current_date = datetime.datetime.now().strftime("%Y_%m_%d")
    attendance_table_name = f"{table_name}_{current_date}"

    # Check if attendance table exists
    cursor.execute("SHOW TABLES LIKE %s", (attendance_table_name,))
    table_exists = cursor.fetchone()

    submitted_periods = set()
    if table_exists:
        # Fetch periods where attendance is already submitted
        cursor.execute(f"SELECT DISTINCT period_1, period_2, period_3, period_4, period_5 FROM {attendance_table_name}")
        rows = cursor.fetchall()
        for row in rows:
            for period, value in enumerate(row, start=1):
                if value == 1:  # 1 means attendance was marked
                    submitted_periods.add(period)

    conn.close()

    # Available periods (1-5) excluding already submitted ones
    available_periods = [p for p in range(1, 6) if p not in submitted_periods]

    if request.method == 'POST':
        period = int(request.form['period'])
        if period not in available_periods:
            flash("Period already submitted or invalid!", 'danger')
            return redirect(url_for('select_period', table_name=table_name))

        return redirect(url_for('table_details', table_name=table_name, period=period))

    return render_template('select_period.html', table_name=table_name, periods=available_periods)

@app.route('/working_days_message')
def working_days_message():
    """Show a message when total working days exceed 90."""
    is_super_admin = session.get('button')
    return render_template('working_days_message.html',is_super_admin=is_super_admin)

@app.route('/table/<table_name>', methods=['GET'])
def table_details(table_name):
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    period = request.args.get('period')
    if not period or not table_name:
        return "Invalid access", 400

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        query = f"""
        SELECT 
            stu_roll_num, 
            stu_name, 
            present, 
            absent, 
            temp_present, 
            temp_absent 
        FROM {table_name}
        """
        cursor.execute(query)
        student_details = cursor.fetchall()
    except Exception as e:
        conn.close()
        return f"Error fetching data: {e}"

    conn.close()
    return render_template(
        'table_details.html',
        table_name=table_name,
        student_details=student_details,
        period=period
    )

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    roll_num = request.form['roll_num']
    action = request.form['action']
    table_name = request.form['table_name']
    period = request.form['period']

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    if action == 'Present':
        query = f"""
        UPDATE {table_name}
        SET temp_present = 1, temp_absent = 0
        WHERE stu_roll_num = %s
        """
    elif action == 'Absent':
        query = f"""
        UPDATE {table_name}
        SET temp_present = 0, temp_absent = 1
        WHERE stu_roll_num = %s
        """
    else:
        conn.close()
        return "Invalid action"

    try:
        cursor.execute(query, (roll_num,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Error updating attendance: {e}", 'error')

    conn.close()
    return redirect(url_for('table_details', table_name=table_name, period=period))

@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    table_name = request.form['table_name']
    period = int(request.form['period'])
    professor_username = session.get('user')  # Professor username

    # Get the current date in the format YYYY_MM_DD
    current_date = datetime.datetime.now().strftime("%Y_%m_%d")
    attendance_table_name = f"{table_name}_{current_date}"

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Update total_days and percentage
        update_total_days()
        calculate_and_update_percentage()

        # Create table with professor tracking if it doesn't exist
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {attendance_table_name} (
            stu_roll_num VARCHAR(100),
            period_1 INT DEFAULT 0,
            prof_1 VARCHAR(100) DEFAULT NULL,
            period_2 INT DEFAULT 0,
            prof_2 VARCHAR(100) DEFAULT NULL,
            period_3 INT DEFAULT 0,
            prof_3 VARCHAR(100) DEFAULT NULL,
            period_4 INT DEFAULT 0,
            prof_4 VARCHAR(100) DEFAULT NULL,
            period_5 INT DEFAULT 0,
            prof_5 VARCHAR(100) DEFAULT NULL,
            presents INT DEFAULT 0
        )
        """
        cursor.execute(create_table_query)

        # Get all students and their temp_present status
        query = f"SELECT stu_roll_num, temp_present, total_days FROM {table_name}"
        cursor.execute(query)
        student_details = cursor.fetchall()

        for roll_num, temp_present, total_days in student_details:
            present_value = 1 if temp_present == 1 else 0

            # Check if student already has an entry for today
            check_query = f"SELECT * FROM {attendance_table_name} WHERE stu_roll_num = %s"
            cursor.execute(check_query, (roll_num,))
            existing_record = cursor.fetchone()

            if existing_record:
                # Update attendance and professor name for the specific period
                update_query = f"""
                UPDATE {attendance_table_name}
                SET period_{period} = %s, prof_{period} = %s, presents = COALESCE(presents, 0) + %s
                WHERE stu_roll_num = %s
                """
                cursor.execute(update_query, (present_value, professor_username, present_value, roll_num))
            else:
                # Insert new record
                insert_query = f"""
                INSERT INTO {attendance_table_name} (stu_roll_num, period_{period}, prof_{period}, presents)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_query, (roll_num, present_value, professor_username, present_value))

            # Update total_presents in the main table
            update_total_query = f"""
            UPDATE {table_name}
            SET total_presents = total_presents + %s
            WHERE stu_roll_num = %s
            """
            cursor.execute(update_total_query, (present_value, roll_num))

        conn.commit()

        # Recalculate percentage and send notifications if conditions are met
        if total_days == 15 and period == 5:
            calculate_and_update_percentage()
            query_cs = f"""
            SELECT stu_name, mail_id, percentagae FROM {table_name}
            WHERE percentagae < 75.00;
            """
            cursor.execute(query_cs)
            students = cursor.fetchall()

            for student_name, email, percentage in students:
                percentage = float(percentage)
                if 60 <= percentage < 75:
                    message = "15 days over,Your attendance percentage is between 60% and 74%."
                elif 50 <= percentage < 60:
                    message = "15 days over,Your attendance percentage is between 50% and 59%."
                elif percentage < 50:
                    message = "15 days over,Your attendance percentage is below 50%."
                else:
                    continue
                send_email(email, student_name, percentage, message)
        elif total_days == 30 and period == 5:
            calculate_and_update_percentage()
            query_cs = f"""
            SELECT stu_name, mail_id, percentagae FROM {table_name}
            WHERE percentagae < 75.00;
            """
            cursor.execute(query_cs)
            students = cursor.fetchall()

            for student_name, email, percentage in students:
                percentage = float(percentage)
                if 60 <= percentage < 75:
                    message = "30 days over,Your attendance percentage is between 60% and 74%."
                elif 50 <= percentage < 60:
                    message = "30 days over,Your attendance percentage is between 50% and 59%."
                elif percentage < 50:
                    message = "30 days over,Your attendance percentage is below 50%."
                else:
                    continue
                send_email(email, student_name, percentage, message)
        elif total_days == 45 and period == 5:
            calculate_and_update_percentage()
            query_cs = f"""
            SELECT stu_name, mail_id, percentagae FROM {table_name}
            WHERE percentagae < 75.00;
            """
            cursor.execute(query_cs)
            students = cursor.fetchall()

            for student_name, email, percentage in students:
                percentage = float(percentage)
                if 60 <= percentage < 75:
                    message = "45 days over,Your attendance percentage is between 60% and 74%."
                elif 50 <= percentage < 60:
                    message = "45 days over,Your attendance percentage is between 50% and 59%."
                elif percentage < 50:
                    message = "45 days over,Your attendance percentage is below 50%."
                else:
                    continue
                send_email(email, student_name, percentage, message)
        elif total_days == 60 and period == 5:
            calculate_and_update_percentage()
            query_cs = f"""
            SELECT stu_name, mail_id, percentagae FROM {table_name}
            WHERE percentagae < 75.00;
            """
            cursor.execute(query_cs)
            students = cursor.fetchall()

            for student_name, email, percentage in students:
                percentage = float(percentage)
                if 60 <= percentage < 75:
                    message = "60 days over,Your attendance percentage is between 60% and 74%."
                elif 50 <= percentage < 60:
                    message = "60 days over,Your attendance percentage is between 50% and 59%."
                elif percentage < 50:
                    message = "60 days over,Your attendance percentage is below 50%."
                else:
                    continue
                send_email(email, student_name, percentage, message)
        elif total_days == 75 and period == 5:
            calculate_and_update_percentage()
            query_cs = f"""
            SELECT stu_name, mail_id, percentagae FROM {table_name}
            WHERE percentagae < 75.00;
            """
            cursor.execute(query_cs)
            students = cursor.fetchall()

            for student_name, email, percentage in students:
                percentage = float(percentage)
                if 60 <= percentage < 75:
                    message = "75 days over,Your attendance percentage is between 60% and 74%."
                elif 50 <= percentage < 60:
                    message = "75 days over,Your attendance percentage is between 50% and 59%."
                elif percentage < 50:
                    message = "75 days over,Your attendance percentage is below 50%."
                else:
                    continue
                send_email(email, student_name, percentage, message)
        elif total_days == 90 and period == 5:
            calculate_and_update_percentage()
            query_cs = f"""
            SELECT stu_name, mail_id, percentagae FROM {table_name}
            WHERE percentagae < 75.00;
            """
            cursor.execute(query_cs)
            students = cursor.fetchall()

            for student_name, email, percentage in students:
                percentage = float(percentage)
                if 60 <= percentage < 75:
                    message = "ATTENDANCE IS OVER,Your attendance percentage is between 60% and 74%. Please pay the fine amount immediately."
                elif 50 <= percentage < 60:
                    message = "ATTENDANCE IS OVER,Your attendance percentage is between 50% and 59%. Please pay the fine amount and submit a medical certificate."
                elif percentage < 50:
                    message = "ATTENDANCE IS OVER,Your attendance percentage is below 50%. You are not permitted to attend the exam."
                else:
                    continue
                send_email(email, student_name, percentage, message)

    except Exception as e:
        conn.rollback()
        flash(f"Error submitting attendance: {e}", 'error')

    finally:
        conn.close()

    return redirect(url_for('admin_login'))



import mysql.connector
import datetime
import re

def archive_and_clear_old_attendance():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Create an archive table if it doesn't exist
    current_date = datetime.datetime.now().strftime("%Y_%m_%d")
    archive_table_name = f"cs_stu_details_archive_{current_date}"
    create_archive_table_query = f"""
    CREATE TABLE IF NOT EXISTS `{archive_table_name}` (
        stu_roll_num VARCHAR(100),
        period_1 INT DEFAULT 0,
        prof_1 VARCHAR(100) DEFAULT NULL,
        period_2 INT DEFAULT 0,
        prof_2 VARCHAR(100) DEFAULT NULL,
        period_3 INT DEFAULT 0,
        prof_3 VARCHAR(100) DEFAULT NULL,
        period_4 INT DEFAULT 0,
        prof_4 VARCHAR(100) DEFAULT NULL,
        period_5 INT DEFAULT 0,
        prof_5 VARCHAR(100) DEFAULT NULL,
        presents INT DEFAULT 0,
        archive_date DATE
    )
    """
    cursor.execute(create_archive_table_query)

    # Fetch all table names from the database
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    ####################################################################     CS     ########################################################################
    # Regex pattern to match 'cs_stu_details_YYYY_MM_DD' format
    table_pattern = re.compile(r"^cs_stu_details_\d{4}_\d{2}_\d{2}$")
    
    for (table_name,) in tables:
        if table_pattern.match(table_name):  # Check if table name matches our pattern
            print(f"Processing table: {table_name}")  # Debugging print

            # Escape table name properly
            table_name_escaped = f"`{table_name}`"

            # Extract archive date from table name
            archive_date = table_name.split("_")[-3:]  # Extract YYYY_MM_DD
            archive_date = "-".join(archive_date)  # Convert to YYYY-MM-DD format

            # Fetch attendance data from the current table
            select_query = f"""
            SELECT stu_roll_num, period_1,prof_1, period_2,prof_2, period_3,prof_3, period_4,prof_4, period_5,prof_5, presents 
            FROM {table_name_escaped}
            """
            print("Executing SQL:", select_query)  # Debugging print
            cursor.execute(select_query)
            students = cursor.fetchall()

            # Insert records into the archive table
            for student in students:
                roll_num = student[0]
                period_1 = student[1]
                prof_1= student[2]
                period_2 = student[3]
                prof_2= student[4]
                period_3 = student[5]
                prof_3= student[6]
                period_4 = student[7]
                prof_4= student[8]
                period_5 = student[9]
                prof_5= student[10]
                presents = student[11]

                insert_query = f"""
                INSERT INTO `{archive_table_name}` 
                (stu_roll_num, period_1,prof_1, period_2,prof_2, period_3,prof_3, period_4,prof_4, period_5,prof_5, presents, archive_date)
                VALUES (%s, %s, %s,%s,%s,%s,%s,%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (roll_num, period_1,prof_1, period_2,prof_2, period_3,prof_3, period_4,prof_4, period_5,prof_5, presents, archive_date))
            
            # Delete the old attendance table after archiving
            delete_table_query = f"DROP TABLE {table_name_escaped}"
            cursor.execute(delete_table_query)
            print(f"Deleted table: {table_name}")

    # Reset total_presents, percentage, and total_days in the main student table
    reset_main_table_query = """
    UPDATE cs_stu_details
    SET total_presents = 0, percentagae = 0, total_days = 0
    """
    cursor.execute(reset_main_table_query)
    print("Main student table reset successfully.")

    # Commit changes and close connection
##    conn.commit()
##    conn.close()
##    print("Attendance data archived, old tables deleted, and main table reset successfully.")
########################################################################################## BCA ####################################################################################
    # Create an archive table if it doesn't exist
    current_date = datetime.datetime.now().strftime("%Y_%m_%d")
    archive_table_name = f"bca_stu_details_archive_{current_date}"
    create_archive_table_query = f"""
    CREATE TABLE IF NOT EXISTS `{archive_table_name}` (
        stu_roll_num VARCHAR(100),
        period_1 INT DEFAULT 0,
        prof_1 VARCHAR(100) DEFAULT NULL,
        period_2 INT DEFAULT 0,
        prof_2 VARCHAR(100) DEFAULT NULL,
        period_3 INT DEFAULT 0,
        prof_3 VARCHAR(100) DEFAULT NULL,
        period_4 INT DEFAULT 0,
        prof_4 VARCHAR(100) DEFAULT NULL,
        period_5 INT DEFAULT 0,
        prof_5 VARCHAR(100) DEFAULT NULL,
        presents INT DEFAULT 0,
        archive_date DATE
    )
    """
    cursor.execute(create_archive_table_query)

    # Fetch all table names from the database
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
 # Regex pattern to match 'cs_stu_details_YYYY_MM_DD' format
    table_pattern = re.compile(r"^bca_stu_details_\d{4}_\d{2}_\d{2}$")
    
    for (table_name,) in tables:
        if table_pattern.match(table_name):  # Check if table name matches our pattern
            print(f"Processing table: {table_name}")  # Debugging print

            # Escape table name properly
            table_name_escaped = f"`{table_name}`"

            # Extract archive date from table name
            archive_date = table_name.split("_")[-3:]  # Extract YYYY_MM_DD
            archive_date = "-".join(archive_date)  # Convert to YYYY-MM-DD format

            # Fetch attendance data from the current table
            select_query = f"""
            SELECT stu_roll_num, period_1,prof_1, period_2,prof_2, period_3,prof_3, period_4,prof_4, period_5,prof_5, presents 
            FROM {table_name_escaped}
            """
            print("Executing SQL:", select_query)  # Debugging print
            cursor.execute(select_query)
            students = cursor.fetchall()

            # Insert records into the archive table
            for student in students:
                roll_num = student[0]
                period_1 = student[1]
                prof_1= student[2]
                period_2 = student[3]
                prof_2= student[4]
                period_3 = student[5]
                prof_3= student[6]
                period_4 = student[7]
                prof_4= student[8]
                period_5 = student[9]
                prof_5= student[10]
                presents = student[11]

                insert_query = f"""
                INSERT INTO `{archive_table_name}` 
                (stu_roll_num, period_1,prof_1, period_2,prof_2, period_3,prof_3, period_4,prof_4, period_5,prof_5, presents, archive_date)
                VALUES (%s, %s, %s,%s,%s,%s,%s,%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (roll_num, period_1,prof_1, period_2,prof_2, period_3,prof_3, period_4,prof_4, period_5,prof_5, presents, archive_date))
            
            # Delete the old attendance table after archiving
            delete_table_query = f"DROP TABLE {table_name_escaped}"
            cursor.execute(delete_table_query)
            print(f"Deleted table: {table_name}")

    # Reset total_presents, percentage, and total_days in the main student table
    reset_main_table_query = """
    UPDATE cs_stu_details
    SET total_presents = 0, percentagae = 0, total_days = 0
    """
    cursor.execute(reset_main_table_query)
    print("Main student table reset successfully.")

    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Attendance data archived, old tables deleted, and main table reset successfully.")


@app.route('/clear_old_attendance', methods=['POST'])
def clear_old_attendance():
    # Call the function to archive and clean data
    archive_and_clear_old_attendance()
    flash("Old attendance data has been cleared and archived!", 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
