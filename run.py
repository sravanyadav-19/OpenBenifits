from dotenv import load_dotenv

# Load variables from .env into environment
load_dotenv()

from openbenefits import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)