from app import create_app, celery

app = create_app()
app.app_context().push()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)