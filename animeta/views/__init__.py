from animeta.views import auth, library, work

def init_app(app):
    app.register_blueprint(auth.bp)
    app.register_blueprint(library.bp)
    app.register_blueprint(work.bp)
