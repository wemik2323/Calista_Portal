import os
import tempfile

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)
from werkzeug.utils import secure_filename

from .cups_client import CUPSClient, CUPSClientError

print_bp = Blueprint(
    'print_service',
    __name__,
    url_prefix='/print',
    template_folder='templates',
    static_folder='static',
)



cups_client = CUPSClient()



ALLOWED_EXTENSIONS = {
    '.pdf', 
    '.txt', 
    '.jpg', 
    '.jpeg', 
    '.png', 
    '.gif'
}


def allowed_file(filename):
    extension = os.path.splitext(filename)[1].lower()
    return extension in ALLOWED_EXTENSIONS


@print_bp.route('/')
def index():
    printers = cups_client.get_printers()

    return render_template(
        'print.html',
        printers=printers,
        current_service_name='Печать документов'
    )


@print_bp.route('/api/printers')
def get_printers():
    return jsonify(
        cups_client.get_printers()
    )



@print_bp.route('/api/print', methods=['POST'])
def print_document():
        
    if 'file' not in request.files:
        return jsonify(
            {
                'status': 'error', 
                'message': 'Файл не найден'
            }
        ), 400


    file = request.files['file']


    printer_name = request.form.get(
        'printer',
        ""
    ).strip()



    paper_size = request.form.get(
        "paper_size",
        "A4"
    )

    if paper_size not in {"A4"}:
        return jsonify(
            {
                "status": "error",
                "message": "Неподдерживаемый формат бумаги."
            }
        ), 400



    orientation = request.form.get(
        "orientation",
        "portrait"
    )

    if orientation not in {
        "portrait",
        "landscape"
    }:
        return jsonify(
            {
                "status": "error",
                "message": "Неподдерживаемая ориентация."
            }
        ), 400




    scaling = request.form.get(
        "scaling",
        "auto"
    )

    if scaling not in {
        "auto",
        "fill"
    }:
       return jsonify(
            {
                "status": "error",
                "message": "Неподдерживаемый режим масштабирования."
            }
        ), 400




    if not file.filename:
        return jsonify(
            {
                'status': 'error', 
                'message': 'Файл не выбран'
            }
        ), 400
        
        
    if not printer_name:
        return jsonify(
            {
                'status': 'error', 
                'message': 'Принтер не выбран'
            }
        ), 400

        
    if not allowed_file(file.filename):
        return jsonify(
            {
                'status': 'error', 
                'message': f'Неподдерживаемый формат. Разрешены: {", ".join(ALLOWED_EXTENSIONS)}'
            }
        ), 400
        

    filename = secure_filename(file.filename)


    if not filename:
        return jsonify(
            {
                "status": "error",
                "message": "Некорректное имя файла.",
            }
        ), 400


    try:

        with tempfile.TemporaryDirectory() as temp_dir:
            
            filepath = os.path.join(
                temp_dir,
                filename,
            )

            file.save(filepath)

            job_id = cups_client.print_file(
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
        return jsonify(
            {
                "status": "error",
                "message": str(e),
            }
        ), 500

@print_bp.route('/api/job/<int:job_id>')
def get_job_status(job_id):
    status = cups_client.get_job_status(job_id)
    return jsonify(status)
