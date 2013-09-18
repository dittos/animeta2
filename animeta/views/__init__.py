from animeta.views import api, auth, library, work

def init_app(app):
    app.register_blueprint(api.bp, url_prefix='/api/v2')
    app.register_blueprint(auth.bp)
    app.register_blueprint(library.bp)
    app.register_blueprint(work.bp)
