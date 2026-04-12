import os
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["Content-Type", "Authorization", "X-Requested-With"], methods=["GET", "POST", "OPTIONS"])

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

    from routes.analyze import analyze_bp
    from routes.optimize import optimize_bp
    from routes.auth import auth_bp
    from routes.payments import payments_bp
    from routes.download import download_bp
    from routes.recruiter import recruiter_bp

    app.register_blueprint(analyze_bp, url_prefix="/api")
    app.register_blueprint(optimize_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(payments_bp, url_prefix="/api")
    app.register_blueprint(download_bp, url_prefix="/api")
    app.register_blueprint(recruiter_bp, url_prefix="/api")

    app.limiter = limiter

    @app.route("/api/health")
    def health():
        return {"status": "ok", "version": "1.0.0"}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
