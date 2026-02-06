"""
Routing dla health check
"""
from flask import Blueprint, jsonify
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    GET /api/health
    """
    logger.info("Health check requested")
    return jsonify({
        "status": "OK",
        "message": "Blog Platform is running",
        "timestamp": datetime.utcnow().isoformat()
    }), 200