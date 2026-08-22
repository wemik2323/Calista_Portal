from datetime import datetime

import psutil
from flask import Blueprint, jsonify, render_template


monitoring_bp = Blueprint(
    'monitoring_service',
    __name__,
    url_prefix='/status',
    template_folder='templates',
    static_folder='static',
)

@monitoring_bp.route('/')
def index():
    return render_template(
        'status.html',
        current_service_name='Мониторинг'
    )

@monitoring_bp.route('/api/stats')
def get_stats():
    return jsonify({
        'cpu': psutil.cpu_percent(interval=0.1),
        'memory': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent,
        'uptime': get_uptime(),
    })


def get_uptime():
    uptime_seconds = datetime.now().timestamp() - psutil.boot_time()

    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)

    return {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
    }
