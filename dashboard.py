from flask import Flask, render_template, request, redirect, send_file
import subprocess
import os
import threading
from flask import jsonify

app = Flask(__name__)

# Set maximum request size to 16MB (adjust as needed)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Paths to files
log_file = 'logs.txt'
checkpoint_file = 'checkpoint.txt'
failed_uploads_file = 'failed_uploads.txt'

def read_last_lines(file_path, num_lines=12):
    """Read the last `num_lines` lines of a file."""
    if not os.path.exists(file_path):
        return "No logs available."
    with open(file_path, 'r', encoding='utf-8') as file:  # Specify utf-8 encoding
        lines = file.readlines()[-num_lines:]
    return ''.join(lines)

def run_scraping_bot():
    """Run the bot in a separate thread."""
    subprocess.Popen(['python', 'app.py'])

@app.route('/')
def index():
    logs = read_last_lines(log_file)
    failed = read_last_lines(failed_uploads_file) if os.path.exists(failed_uploads_file) else "No failed uploads yet."
    
    # Calculate progress
    total_urls = len(open('sitemap.csv').readlines())
    crawled_urls = len(open(checkpoint_file).readlines()) if os.path.exists(checkpoint_file) else 0
    failed_urls = len(open(failed_uploads_file).readlines()) if os.path.exists(failed_uploads_file) else 0

    return render_template('index.html', logs=logs, failed=failed, crawled_urls=crawled_urls, total_urls=total_urls, failed_urls=failed_urls)

@app.route('/run_bot')
def run_bot():
    """Start the scraping bot."""
    threading.Thread(target=run_scraping_bot).start()
    return redirect('/')

@app.route('/download_logs')
def download_logs():
    """Download the complete log file."""
    return send_file(log_file, as_attachment=True)

@app.route('/download_failed_uploads')
def download_failed_uploads():
    """Download the failed uploads file."""
    return send_file(failed_uploads_file, as_attachment=True)

@app.route('/download_checkpoints')
def download_checkpoints():
    """Download the checkpoints file."""
    return send_file(checkpoint_file, as_attachment=True)

@app.route('/edit_file/<file_type>', methods=['GET', 'POST'])
def edit_file(file_type):
    """Edit a file dynamically based on the file type."""
    file_paths = {
        'config' : 'config.json',
        'sitemap': 'sitemap.csv',
        'failed_uploads': failed_uploads_file,
        'checkpoints': checkpoint_file
    }

    if file_type not in file_paths:
        return "Invalid file type", 400

    file_path = file_paths[file_type]

    if request.method == 'POST':
        if 'file_upload' in request.files:
            # Handle file upload
            uploaded_file = request.files['file_upload']
            uploaded_file.save(file_path)
        else:
            # Handle textarea content
            file_content = request.form.get('file_content')
            with open(file_path, 'w') as f:
                f.write(file_content.replace('\r', ''))
        return redirect('/')
    else:
        # Load the current file content
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                file_content = f.read()
        else:
            file_content = ''
        return render_template('edit_file.html', file_name=file_type.replace('_', ' ').title(), file_content=file_content)

@app.route('/get_logs')
def get_logs():
    """Serve the last 12 lines of logs dynamically."""
    return read_last_lines(log_file, num_lines=12)

@app.route('/get_stats')
def get_stats():
    """Serve the statistics dynamically."""
    total_urls = len(open('sitemap.csv').readlines())
    crawled_urls = len(open(checkpoint_file).readlines()) if os.path.exists(checkpoint_file) else 0
    failed_urls = len(open(failed_uploads_file).readlines()) if os.path.exists(failed_uploads_file) else 0

    return jsonify({
        'crawled_urls': crawled_urls,
        'total_urls': total_urls,
        'failed_urls': failed_urls
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)