from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import gridfs
from datetime import datetime
from bson import ObjectId  # Import ObjectId to handle MongoDB IDs

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["filedb"]
fs = gridfs.GridFS(db)

@app.route('/')
def index():
    # Fetch all uploaded courses from MongoDB
    courses = list(fs.find({"metadata.status": {"$ne": "completed"}}))  # Pending courses
    completed_courses = list(fs.find({"metadata.status": "completed"}))  # Completed courses
    return render_template('index.html', courses=courses, completed_courses=completed_courses)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        resource_type = request.form['resource_type']
        course = request.form['course']
        access_level = request.form['access_level']
        file = request.files['file']

        if file.filename == '':
            return "No selected file", 400

        # Save file to MongoDB
        fs.put(file, filename=file.filename, metadata={
            "title": title,
            "description": description,
            "resource_type": resource_type,
            "course": course,
            "access_level": access_level,
            "uploadDate": datetime.utcnow(),
            "status": "pending"  # Default status is "pending"
        })
        return redirect('/')
    return render_template('upload.html')

@app.route('/complete/<file_id>', methods=['POST'])
def complete_course(file_id):
    # Convert file_id to ObjectId
    file = fs.find_one({"_id": ObjectId(file_id)})
    if file:
        try:
            # Read the file content before deleting it
            file_content = file.read()
            fs.delete(ObjectId(file_id))  # Delete the old file
            # Re-upload the file with updated metadata
            fs.put(file_content, filename=file.filename, metadata={**file.metadata, "status": "completed"})
        except Exception as e:
            print(f"Error completing course: {e}")
            return "An error occurred while completing the course.", 500
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)