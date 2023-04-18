import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
from functools import wraps

app = Flask(__name__)

app.secret_key = "8d1714ff51178feb7050f48ca3b3ac91"
# Set the upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'

# Valid extensions for the file
VALID_EXTENSIONS = {'xlsx', 'csv'}


# Decorator to check that user is logged in or not
def login_required(func):
    @wraps(func)
    def login_wrapper(*args, **kwargs):
        is_user_logged_in = session.get("is_user", False)
        if not is_user_logged_in:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return login_wrapper


# Function to check if the file is valid file or not with the extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in VALID_EXTENSIONS


# Route for the home page
@app.route('/')
def home():
    return render_template('home.html')


# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    is_user_logged_in = session.get("is_user", False)
    if is_user_logged_in:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            flash('Invalid credentials. Please try again', "danger")
        else:
            session["is_user"] = True
            return redirect(url_for('dashboard'))
    return render_template('login.html', title='Login')


# Route for logging out
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    is_user_logged_in = session.get("is_user", False)
    if is_user_logged_in:
        flash("Sucessfully logged out", "success")
        session.pop("is_user")
    return redirect(url_for('login'))


# Route for the dashboard page
@app.route('/dashboard')
@login_required
def dashboard():
    files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        files_in_dir = os.listdir(app.config['UPLOAD_FOLDER'])
        files = [file for file in files_in_dir]
    return render_template('dashboard.html', title='Dashboard', files=enumerate(files))


# Route for the upload file
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    # Check if the file is present in the request
    file = request.files['file']
    if not file.filename:
        flash("Please select the file to upload", "warning")
        return redirect(url_for('dashboard'))
    # Check if the file has an allowed extension
    if not allowed_file(file.filename):
        flash("Invalid file extension. Please upload the file with extensions .csv or .xlsx", "warning")
        return redirect(url_for('dashboard'))
    # Save the file to the upload folder
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.mkdir(app.config['UPLOAD_FOLDER'])
    if file and allowed_file(file.filename):
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash(f"File {filename} is uploaded successfully", "success")
        return redirect(url_for('view_file', filename=filename))
    else:
        flash("Please select the file to upload")
        return redirect(url_for('dashboard'))


# Route to view the file
@app.route('/view/<filename>', methods=['GET', 'POST'])
@login_required
def view_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        extension = filepath.split(".")[-1]
        try:
            if extension == "csv":
                df = pd.read_csv(filepath, encoding='unicode_escape')
            else:
                df = pd.read_excel(filepath)
            column_names = list(df.columns.values)
            row_data = df.values.tolist()
            return render_template('file.html', filename=filename, columns=column_names, row_data=row_data)
        except Exception as err:
            os.remove(filepath)
            flash("File content is malformed. Please upload a valid file. Deleted the current file", "danger")
            return redirect(url_for('dashboard'))
    else:
        flash(f"File {filename} does not exist", "info")
        return redirect(url_for('dashboard'))


# Route to download the file
@app.route('/download/<filename>', methods=['GET', 'POST'])
@login_required
def download(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        flash(f"File {filename} does not exist", "info")
        return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
