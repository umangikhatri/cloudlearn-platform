import os
from flask import Flask, render_template_string, request, redirect, session, send_from_directory

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# User Database
USERS = {
    "t1@school.com": {"password": "123", "role": "teacher", "name": "Prof. Smith"},
    "t2@school.com": {"password": "123", "role": "teacher", "name": "Prof. Jones"},
    "s1@school.com": {"password": "456", "role": "student", "name": "Alice"},
    "s2@school.com": {"password": "456", "role": "student", "name": "Bob"}
}

# ---------------- LOGIN PAGE ----------------
login_template = """
<style>
body{
font-family:'Segoe UI',sans-serif;
background:linear-gradient(135deg,#6a11cb,#2575fc);
display:flex;
justify-content:center;
align-items:center;
height:100vh;
margin:0;
}

.login-box{
background:white;
padding:2rem;
border-radius:15px;
box-shadow:0 10px 30px rgba(0,0,0,0.2);
width:320px;
text-align:center;
}

input{
width:100%;
padding:10px;
margin:10px 0;
border:1px solid #ddd;
border-radius:5px;
}

button{
width:100%;
padding:10px;
background:#3498db;
color:white;
border:none;
border-radius:6px;
cursor:pointer;
}

button:hover{
background:#2980b9;
}
</style>

<div class="login-box">
<h2>CloudLearn Login</h2>
<form action="/login" method="POST">
<input type="email" name="email" placeholder="Email" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">Sign In</button>
</form>
</div>
"""

# ---------------- PORTAL PAGE ----------------
portal_template = """
<style>

body{
font-family:'Segoe UI',sans-serif;
background:#f0f2f5;
margin:0;
}

.navbar{
background:linear-gradient(90deg,#2c3e50,#34495e);
color:white;
padding:1rem 2rem;
display:flex;
justify-content:space-between;
align-items:center;
}

.container{
max-width:900px;
margin:2rem auto;
padding:2rem;
background:white;
border-radius:12px;
box-shadow:0 4px 15px rgba(0,0,0,0.1);
}

.card{
background:white;
padding:1.5rem;
border-radius:10px;
margin-bottom:20px;
box-shadow:0 4px 12px rgba(0,0,0,0.1);
}

.btn{
background:#3498db;
color:white;
border:none;
padding:8px 16px;
border-radius:6px;
cursor:pointer;
text-decoration:none;
}

.del-btn{
background:#e74c3c;
color:white;
border:none;
padding:8px 16px;
border-radius:6px;
cursor:pointer;
}

.file-item{
display:flex;
justify-content:space-between;
padding:12px;
border-bottom:1px solid #eee;
align-items:center;
}

.logout{
color:#ff6b6b;
text-decoration:none;
font-weight:bold;
}

</style>

<div class="navbar">
<h2>CloudLearn Platform</h2>
<div>Welcome, <b>{{ name }}</b> ({{ role|capitalize }}) | 
<a href="/logout" class="logout">Logout</a></div>
</div>

<div class="container">

<div class="card">
<h3>Total Courses: {{ total_courses }}</h3>
<p>Total Materials: {{ total_files }}</p>
</div>

{% if role == 'teacher' %}
<div class="card">

<h3>Teacher Control Panel</h3>

<form action="/upload" method="POST" enctype="multipart/form-data">

<select name="course">
<option value="Mathematics">Mathematics</option>
<option value="ComputerScience">Computer Science</option>
<option value="Physics">Physics</option>
</select>

<input type="file" name="file">

<button type="submit" class="btn">Upload Resource</button>

</form>

</div>
{% endif %}

<h3>Available Course Materials</h3>

<div style="border:1px solid #ddd;border-radius:8px;">

{% for course, files in courses.items() %}

<h3 style="padding:10px;">{{ course }}</h3>

{% for file in files %}

<div class="file-item">

<span>📄 {{ file }}</span>

<div>

<a href="/download/{{ course }}/{{ file }}" target="_blank" class="btn">Preview</a>

<a href="/download/{{ course }}/{{ file }}" class="btn">Download</a>

{% if role == 'teacher' %}
<form action="/delete/{{ course }}/{{ file }}" method="POST" style="display:inline;">
<button type="submit" class="del-btn">Delete</button>
</form>
{% endif %}

</div>

</div>

{% endfor %}

{% endfor %}

</div>

</div>
"""

# ---------------- ROUTES ----------------

@app.route('/')
def home():

    if 'email' not in session:
        return login_template

    courses = {}

    for course in os.listdir(app.config['UPLOAD_FOLDER']):
        course_path = os.path.join(app.config['UPLOAD_FOLDER'], course)

        if os.path.isdir(course_path):
            courses[course] = os.listdir(course_path)

    total_courses = len(courses)
    total_files = sum(len(files) for files in courses.values())

    return render_template_string(
        portal_template,
        name=session['name'],
        role=session['role'],
        courses=courses,
        total_courses=total_courses,
        total_files=total_files
    )

@app.route('/login', methods=['POST'])
def login():

    email = request.form['email']
    password = request.form['password']

    user = USERS.get(email)

    if user and user['password'] == password:

        session['email'] = email
        session['role'] = user['role']
        session['name'] = user['name']

        return redirect('/')

    return "Invalid Login! <a href='/'>Go Back</a>"

@app.route('/upload', methods=['POST'])
def upload():

    if session.get('role') == 'teacher':

        course = request.form['course']
        f = request.files['file']

        course_folder = os.path.join(app.config['UPLOAD_FOLDER'], course)
        os.makedirs(course_folder, exist_ok=True)

        if f.filename:
            f.save(os.path.join(course_folder, f.filename))

    return redirect('/')

@app.route('/delete/<course>/<filename>', methods=['POST'])
def delete_file(course, filename):

    if session.get('role') == 'teacher':

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], course, filename)

        if os.path.exists(file_path):
            os.remove(file_path)

    return redirect('/')

@app.route('/download/<course>/<filename>')
def download_file(course, filename):

    return send_from_directory(
        os.path.join(app.config['UPLOAD_FOLDER'], course),
        filename
    )

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)




