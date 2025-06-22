from flask import Flask, render_template, jsonify, send_from_directory
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/csv-files")
def list_csv_files():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    return jsonify(csv_files)

@app.route("/data/<path:filename>")
def serve_csv_file(filename):
    return send_from_directory("data", filename)

if __name__ == "__main__":
    app.run(debug=True)
