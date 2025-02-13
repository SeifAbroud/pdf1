from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import io

app = Flask(__name__)

# PostgreSQL configuration
DB_HOST = "localhost"
DB_NAME = "pdf_scoring_db"
DB_USER = "postgres"
DB_PASSWORD = "2025"

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
        CREATE TABLE IF NOT EXISTS pdf_uploads (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            file_data BYTEA NOT NULL
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

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

    file_data = file.read()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO pdf_uploads (filename, file_data) VALUES (%s, %s)',
        (file.filename, psycopg2.Binary(file_data))  # <-- Add closing parenthesis here
    )  # ✅ Corrected line
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('files'))

    return redirect(url_for('files'))

@app.route('/files')
def files():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, filename FROM pdf_uploads')
    files = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('files.html', files=files)

@app.route('/download/<int:file_id>')
def download(file_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT filename, file_data FROM pdf_uploads WHERE id = %s', (file_id,))
    file = cur.fetchone()
    cur.close()
    conn.close()

    if file:
        return app.response_class(
            file[1],
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{file[0]}"'}
        )
    return "File not found", 404

if __name__ == '__main__':
    create_table()
    app.run(debug=True)