import os
import uuid
import pathlib
import threading
import logging
from flask import (
    Flask,
    request,
    render_template,
    url_for,
    send_from_directory,
    after_this_request,
    jsonify,
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

BASE_DIR = pathlib.Path(__file__).parent.resolve()
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

ALLOWED_CSV_EXTENSIONS = {"csv"}

# Global dictionary to hold task status.
tasks = {}


# Custom logging handler that writes logs to tasks[task_id]["logs"].
class TaskLogHandler(logging.Handler):
    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id

    def emit(self, record):
        msg = self.format(record)
        if self.task_id in tasks:
            if "logs" not in tasks[self.task_id]:
                tasks[self.task_id]["logs"] = []
            tasks[self.task_id]["logs"].append(msg)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_CSV_EXTENSIONS
    )


def background_process(task_id, input_source, api_key):
    # Create a dedicated logger for this task.
    logger = logging.getLogger(f"task_{task_id}")
    logger.setLevel(logging.INFO)

    # Create and attach the custom handler.
    handler = TaskLogHandler(task_id)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Also attach the same handler to the "util" logger so logs from util.py are captured.
    util_logger = logging.getLogger("util")
    util_logger.setLevel(logging.INFO)
    util_logger.propagate = True
    util_logger.addHandler(handler)

    logger.info(f"Task {task_id} started processing.")
    try:
        # If input_source is a URL, convert the Google Sheet to CSV.
        if input_source.startswith("http"):
            from sheets_parser import google_sheet_to_csv

            csv_path = google_sheet_to_csv(input_source, api_key)
            logger.info(f"Converted Google Sheet to CSV: {csv_path}")
        else:
            csv_path = input_source
            logger.info(f"Using uploaded CSV: {csv_path}")

        # Import the cast list and build the processed array.
        from util import import_castlist, build_castlist

        castlist = import_castlist(csv_path)
        castlist_path = pathlib.Path(csv_path).parent.resolve()
        logger.info(f"Imported cast list with {len(castlist)} entries.")
        wavetool_castlist = build_castlist(castlist, castlist_path)
        logger.info(
            f"Built processed cast list with {len(wavetool_castlist)} entries."
        )

        # Generate output filenames.
        output_pla_filename = f"{task_id}_players.pla"
        output_pdf_filename = f"{task_id}_mic_cards.pdf"
        output_pla_path = OUTPUT_FOLDER / output_pla_filename
        output_pdf_path = OUTPUT_FOLDER / output_pdf_filename

        # Generate the WaveTool player file.
        from make_players import create_wavetool_castlist

        with open(output_pla_path, "wb") as f_pla:
            create_wavetool_castlist(wavetool_castlist, f_pla, castlist_path)
        logger.info(f"Created WaveTool player file: {output_pla_filename}")

        # Generate the mic cards PDF.
        from mic_cards import create_mic_cards

        with open(output_pdf_path, "wb") as f_pdf:
            create_mic_cards(wavetool_castlist, f_pdf, castlist_path)
        logger.info(f"Created Mic Cards PDF file: {output_pdf_filename}")

        tasks[task_id]["status"] = "completed"
        tasks[task_id]["pla"] = output_pla_filename
        tasks[task_id]["pdf"] = output_pdf_filename
        logger.info(f"Task {task_id} completed successfully.")
    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)
        logger.exception(f"Task {task_id} encountered an error.")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        sheet_link = request.form.get("sheet_link", "").strip()
        csv_path = None
        if sheet_link:
            input_source = sheet_link
        elif "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                csv_path = pathlib.Path(app.config["UPLOAD_FOLDER"]) / filename
                file.save(str(csv_path))
                input_source = str(csv_path)
            else:
                return (
                    jsonify(
                        {
                            "error": "Invalid file type. Please upload a CSV file."
                        }
                    ),
                    400,
                )
        else:
            return (
                jsonify(
                    {
                        "error": "Please provide a CSV file or a Google Sheets URL."
                    }
                ),
                400,
            )

        api_key = os.environ.get("GOOGLE_API_KEY") if sheet_link else None
        if sheet_link and not api_key:
            return jsonify({"error": "Google API Key not set."}), 400

        task_id = str(uuid.uuid4())[:8]
        tasks[task_id] = {"status": "processing", "logs": []}
        threading.Thread(
            target=background_process,
            args=(task_id, input_source, api_key),
            daemon=True,
        ).start()

        @after_this_request
        def cleanup(response):
            try:
                if csv_path and pathlib.Path(csv_path).exists():
                    pathlib.Path(csv_path).unlink()
            except Exception as cleanup_err:
                app.logger.error(f"Cleanup error: {cleanup_err}")
            return response

        return jsonify({"redirect": url_for("status", task_id=task_id)})
    else:
        return render_template("index.html")


@app.route("/status/<task_id>")
def status(task_id):
    if task_id not in tasks:
        return "Invalid task ID.", 404
    return render_template("status.html", task_id=task_id)


@app.route("/api/status/<task_id>")
def api_status(task_id):
    if task_id not in tasks:
        return jsonify({"status": "not found"})
    return jsonify(tasks[task_id])


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(str(OUTPUT_FOLDER), filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
