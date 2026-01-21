from imoveis_web_multi import celery, app

if __name__ == "__main__":
    with app.app_context():
        # Ensure tasks are discovered
        pass
