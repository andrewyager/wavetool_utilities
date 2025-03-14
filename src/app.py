# app.py
from flask import Flask, request, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os, uuid, zipfile, shutil, subprocess

app = Flask(__name__)

# Directory for output files (outputs will be kept here for downloading)
OUTPUT_FOLDER = 'outputs'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Allowed file extensions for uploads
ALLOWED_CSV_EXT = {'csv'}
ALLOWED_ZIP_EXT = {'zip'}

def allowed_file(filename, allowed_set):
    """Check if filename has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Ensure a CSV file was uploaded
        if 'csv_file' not in request.files or request.files['csv_file'].filename == '':
            return render_template('index.html', error="Please upload a CSV file.")
        csv_file = request.files['csv_file']
        # Validate CSV extension
        if not allowed_file(csv_file.filename, ALLOWED_CSV_EXT):
            return render_template('index.html', error="Invalid file type for CSV. Only .csv allowed.")
        # Secure the CSV filename and save it
        csv_filename = secure_filename(csv_file.filename)  # sanitize filename [oai_citation_attribution:7‡flask.palletsprojects.com](https://flask.palletsprojects.com/en/stable/patterns/fileuploads/#:~:text=So%20what%20does%20that%20secure_filename,it%20directly%20on%20the%20filesystem)
        # Create a unique working directory for this upload
        prefix = str(uuid.uuid4())[:8]  # short random identifier
        working_dir = os.path.join('/tmp', f"work_{prefix}")
        os.makedirs(working_dir, exist_ok=True)
        csv_path = os.path.join(working_dir, csv_filename)
        csv_file.save(csv_path)
        # Handle optional ZIP file
        if 'zip_file' in request.files and request.files['zip_file'].filename:
            zip_file = request.files['zip_file']
            if zip_file.filename != '' and allowed_file(zip_file.filename, ALLOWED_ZIP_EXT):
                zip_filename = secure_filename(zip_file.filename)
                zip_path = os.path.join(working_dir, zip_filename)
                zip_file.save(zip_path)
                # Extract the ZIP contents (images) into the working directory
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(working_dir)
        # Define output file paths
        output_pla = f"{prefix}.pla"
        output_pdf = f"{prefix}.pdf"
        output_pla_path = os.path.join(OUTPUT_FOLDER, output_pla)
        output_pdf_path = os.path.join(OUTPUT_FOLDER, output_pdf)
        # Call external scripts to process the CSV (and images if provided)
        try:
            subprocess.run(["python3", "make_players.py", csv_path, output_pla_path], check=True)
            subprocess.run(["python3", "mic_cards.py", csv_path, output_pdf_path], check=True)
        except subprocess.CalledProcessError as e:
            # If one of the scripts fails, clean up and return an error
            shutil.rmtree(working_dir, ignore_errors=True)
            return render_template('index.html', error=f"Processing failed: {e}")
        # Clean up the working files (CSV and extracted images)
        shutil.rmtree(working_dir, ignore_errors=True)
        # Display the result page with download links
        return render_template('result.html', pla_file=output_pla, pdf_file=output_pdf)
    # GET request – show the upload form
    return render_template('index.html')

@app.route('/download/<path:filename>')
def download_file(filename):
    """Serve files from the output directory."""
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)
