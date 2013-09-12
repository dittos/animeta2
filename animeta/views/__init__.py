from animeta.views import library

def init_app(app):
    app.register_blueprint(library.bp)
