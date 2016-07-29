"""Run the flask server. Not for production use.
"""
from quizApp import create_app


def run_dev_server():
    """Run a server with development config.
    """
    app = create_app("development")
    app.run()

if __name__ == '__main__':
    run_dev_server()
