from .pages_routes import pages_bp
from .surveillance_routes import surveillance_bp
from .analytics import analytics_bp  # ✅ Correct
from .surveillance_routes import surveillance_bp
__all__ = ['pages_bp', 'surveillance_bp', 'analytics_bp']
