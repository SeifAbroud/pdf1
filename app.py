from flask import Flask, render_template, request, redirect, url_for, send_file
import psycopg2
import os
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# PostgreSQL configuration
DB_HOST = "localhost"
DB_NAME = "v0"
DB_USER = "postgres"
DB_PASSWORD = "password"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pdf_uploads3 (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            sender TEXT,
            receiver TEXT,
            subject TEXT
        )
    ''')
    print("Table created")
    conn.commit()
    cur.close()
    conn.close()

# Function to add ID text on top of the PDF
def add_id_to_pdf(input_pdf_path, output_pdf_path, file_id):
    packet = BytesIO()
    c = canvas.Canvas(packet)
    c.setFont("Helvetica", 12)
    c.drawString(200, 800, "heeeeeeeeeeeeelo")
    c.drawString(100, 800, f"ID: {file_id}")  # Custom position for the ID
    c.save()

    packet.seek(0)
    overlay_pdf = PdfReader(packet)
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    # Adding the overlay with the ID to the original PDF
    page = reader.pages[0]
    page.merge_page(overlay_pdf.pages[0])

    writer.add_page(page)

    # Saving the new PDF
    with open(output_pdf_path, "wb") as f:
        writer.write(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        return "No file selected", 400
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Add the ID on top of the PDF
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO pdf_uploads3 (filename, file_path) VALUES (%s, %s) RETURNING id',
        (file.filename, file_path)
    )
    file_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # Modify the uploaded PDF to add the ID on top of it
    output_file_path = os.path.join(UPLOAD_FOLDER, f"modified_{file.filename}")
    add_id_to_pdf(file_path, output_file_path, file_id)

    return redirect(url_for('add_info', file_id=file_id))

@app.route('/files')
def files():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, filename, sender, receiver, subject FROM pdf_uploads3')
    files = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('files.html', files=files)

@app.route('/download/<int:file_id>')
def download(file_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT filename, file_path FROM pdf_uploads3 WHERE id = %s', (file_id,))
    file = cur.fetchone()
    cur.close()
    conn.close()

    if file and os.path.exists(file[1]):
        return send_file(file[1], as_attachment=True, download_name=file[0])
    return "File not found", 404

@app.route('/preview/<int:file_id>')
def preview(file_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT file_path FROM pdf_uploads3 WHERE id = %s', (file_id,))
    file = cur.fetchone()
    cur.close()
    conn.close()

    if file and os.path.exists(file[0]):
        return render_template('preview.html', file_url=f"/{file[0]}")
    
    return "File not found", 404

@app.route('/add_info/<int:file_id>', methods=['GET', 'POST'])
def add_info(file_id):
    if request.method == 'POST':
        sender = request.form['sender']
        receiver = request.form['receiver']
        subject = request.form['subject']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'UPDATE pdf_uploads3 SET sender = %s, receiver = %s, subject = %s WHERE id = %s',
            (sender, receiver, subject, file_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('files'))

    return render_template('add_info.html', file_id=file_id)

if __name__ == '__main__':
    create_table()
    app.run(debug=True)
