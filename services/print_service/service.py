import os
import tempfile

from flask import jsonify, render_template, request
from werkzeug.utils import secure_filename

from services.base import BaseService

from .cups_client import CUPSClient, CUPSClientError


class PrintService(BaseService):
    name = "Печать документов"
    url_prefix = "/print"
    order = 1
    available = True

    def __init__(self):
        self.cups_client = CUPSClient()
        super().__init__()

    def register_routes(self):
        bp = self.blueprint

        ALLOWED_EXTENSIONS = {".pdf", ".txt", ".jpg", ".jpeg", ".png", ".gif"}

        def allowed_file(filename: str) -> bool:
            return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

        @bp.route("/")
        def index():
            printers = self.cups_client.get_printers()
            return render_template(
                "print.html",
                printers=printers,
                current_service_name=self.name,
            )

        @bp.route("/api/printers")
        def get_printers():
            return jsonify(self.cups_client.get_printers())

        @bp.route("/api/print", methods=["POST"])
        def print_document():
            if "file" not in request.files:
                return jsonify({"status": "error", "message": "Файл не найден"}), 400

            file = request.files["file"]
            printer_name = request.form.get("printer", "").strip()
            paper_size = request.form.get("paper_size", "A4")
            orientation = request.form.get("orientation", "portrait")
            scaling = request.form.get("scaling", "auto")

            if paper_size not in {"A4"}:
                return jsonify(
                    {"status": "error", "message": "Неподдерживаемый формат бумаги."}
                ), 400

            if orientation not in {"portrait", "landscape"}:
                return jsonify(
                    {"status": "error", "message": "Неподдерживаемая ориентация."}
                ), 400

            if scaling not in {"auto", "fill"}:
                return jsonify(
                    {
                        "status": "error",
                        "message": "Неподдерживаемый режим масштабирования.",
                    }
                ), 400

            if not file.filename:
                return jsonify({"status": "error", "message": "Файл не выбран"}), 400

            if not printer_name:
                return jsonify({"status": "error", "message": "Принтер не выбран"}), 400

            if not allowed_file(file.filename):
                return jsonify(
                    {
                        "status": "error",
                        "message": f"Неподдерживаемый формат. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}",
                    }
                ), 400

            filename = secure_filename(file.filename)
            if not filename:
                return jsonify(
                    {"status": "error", "message": "Некорректное имя файла."}
                ), 400

            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    filepath = os.path.join(temp_dir, filename)
                    file.save(filepath)

                    job_id = self.cups_client.print_file(
                        printer_name,
                        filepath,
                        filename,
                        paper_size=paper_size,
                        orientation=orientation,
                        scaling=scaling,
                    )

                return jsonify(
                    {
                        "status": "success",
                        "message": "Документ отправлен на печать.",
                        "job_id": job_id,
                    }
                )

            except CUPSClientError as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @bp.route("/api/job/<int:job_id>")
        def get_job_status(job_id: int):
            return jsonify(self.cups_client.get_job_status(job_id))
