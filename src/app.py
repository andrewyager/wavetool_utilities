import os
import sys
import uuid
import pathlib
from flask import (
    Flask,
    request,
    render_template,
    send_from_directory,
    after_this_request,
)
from werkzeug.utils import secure_filename
from sheets_parser import google_sheet_to_csv
from util import import_castlist  # shared function
from make_players import create_wavetool_castlist
from mic_cards import create_mic_cards
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)

ALLOWED_CSV_EXTENSIONS = {"csv"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_CSV_EXTENSIONS
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Choose between Google Sheets URL or file upload
        sheet_link = request.form.get("sheet_link", "").strip()
        csv_path = None
        if sheet_link:
            try:
                csv_path = google_sheet_to_csv(sheet_link, GOOGLE_API_KEY)
            except Exception as e:
                return render_template(
                    "index.html", error=f"Error processing Google Sheet: {e}"
                )
        elif "file" in request.files and request.files["file"].filename != "":
            file = request.files["file"]
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                csv_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(csv_path)
            else:
                return render_template(
                    "index.html",
                    error="Invalid file type. Please upload a CSV file.",
                )
        else:
            return render_template(
                "index.html",
                error="Please provide a CSV file or a Google Sheets URL.",
            )

        try:
            # Use shared import_castlist from util.py.
            castlist = import_castlist(csv_path, default_resize=True)
        except Exception as e:
            return render_template(
                "index.html", error=f"Error reading cast list: {e}"
            )

        castlist_path = pathlib.Path(csv_path).parent.resolve()
        prefix = str(uuid.uuid4())[:8]
        output_pla_filename = f"{prefix}_players.pla"
        output_pdf_filename = f"{prefix}_mic_cards.pdf"
        output_pla_path = os.path.join(OUTPUT_FOLDER, output_pla_filename)
        output_pdf_path = os.path.join(OUTPUT_FOLDER, output_pdf_filename)

        try:
            with open(output_pla_path, "wb") as f_pla:
                create_wavetool_castlist(castlist, f_pla, castlist_path)
        except Exception as e:
            return render_template(
                "index.html", error=f"Error creating WaveTool player file: {e}"
            )

        try:
            with open(output_pdf_path, "wb") as f_pdf:
                create_mic_cards(castlist, f_pdf, castlist_path)
        except Exception as e:
            return render_template(
                "index.html", error=f"Error creating Mic Cards PDF: {e}"
            )

        @after_this_request
        def cleanup(response):
            try:
                if csv_path and os.path.exists(csv_path):
                    os.remove(csv_path)
            except Exception as cleanup_err:
                app.logger.error(f"Cleanup error: {cleanup_err}")
            return response

        return render_template(
            "result.html",
            pla_file=output_pla_filename,
            pdf_file=output_pdf_filename,
        )
    else:
        return render_template("index.html")


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
