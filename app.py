import hashlib
import mysql.connector
import uuid
import boto3
import os
from flask import Flask, render_template, request, redirect, flash, url_for, session,make_response, jsonify
from botocore.client import Config
import logging
from uploads.handlers import create_connection, allowed_file
import re


app = Flask(__name__)
app.secret_key = ''
logging.basicConfig(filename='app.log', level=logging.INFO)

username_pattern = r'^(([a-zA-Z0-9._])\2*|)+$'
S3_BUCKET = ''
REGION_NAME = ''
s3 = boto3.client('s3',
                  aws_access_key_id='',
                  aws_secret_access_key='',
                  region_name=REGION_NAME,
                  config=Config(signature_version='s3v4'))

def test_regex(pattern, value):
    return bool(re.match(pattern, value))


def get_presigned_file_url(provided_file_name):
    if not provided_file_name:
        return
    return s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': S3_BUCKET,
            'Key': provided_file_name,
            'ResponseContentDisposition': f"attachment; filename={provided_file_name}"
        },
        ExpiresIn= None,
        HttpMethod='GET',  # Specify the HTTP method (GET)
    )


@app.route('/upload', methods=['POST', 'TRACE'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file and allowed_file(file.filename):
        try:
            # Save the file to a temporary location on the server
            file_path = '/tmp/' + file.filename
            file.save(file_path)

            # Upload the file to S3
            
            s3.upload_file(file_path, S3_BUCKET, file.filename)
            
            conn = create_connection() 
            if conn is not None:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET File_Name=%s WHERE id=%s', (file.filename,session['user_id']))
                conn.commit()
                conn.close()
                session['File_Name']=file.filename

                flash(f'{file.filename} was successfully uploaded', 'success')
            return redirect('/dashboard')
        except Exception as e:
            return jsonify({'error': str(e)})
    else:
        return jsonify({'error': 'File type not allowed'})




# Route for the login page
@app.route('/')
def home():
    return render_template('home.html')    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = create_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, hashed_password))
            user = cursor.fetchone()
            conn.close()

            if user:
                # Store user data in session
                session['user_id'] = user[0]  
                session['username'] = user[1]  
                session['email'] = user[2]  
                session['home_address'] = user[3]
                session['Education'] = user[4] 
                session['Experience'] = user[5]  
                session['pin'] = user[6] 
                session['File_Name'] = user[7]  
                session['state'] = user[8]
                session['country'] = user[9]  
               
                if session['user_id']==e_e:
                    return redirect('/recruiter')
                
                else:
                    return redirect('/dashboard')
            
            return render_template('login.html', error='Invalid username or password')
        else:
            logging.error('Failed to connect to the database')
            return render_template('login.html', error='Failed to connect to the database')
    else:
        return render_template('login.html')

# Route for the registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if test_regex(username_pattern, request.form['username']):
            username=request.form['username']
            email=request.form.get('email')
        else:
            return render_template('register.html', error='Invalid username or email')
        password = request.form.get('password')
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        if not username or not email or not password:  # Check if any of the fields are empty
            return render_template('register.html', error='Username, email, or password cannot be empty')

        conn = create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()

                # Check if the username or email already exists
                cursor.execute('SELECT * FROM users WHERE username=%s OR email=%s', (username, email))
                existing_user = cursor.fetchone()

                if existing_user:
                    return render_template('register.html', error='Username or email already exists')

               
                cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, hashed_password))
                conn.commit()
                conn.close()

                return redirect(url_for('login'))
            except mysql.connector.Error as e:
               
                logging.error(f"Database error: {str(e)}")
                return render_template('register.html', error=f"Database error: {str(e)}")
            finally:
                if conn.is_connected():
                    conn.close()
        else:
            logging.error('Failed to connect to the database')
            return render_template('register.html', error='Failed to connect to the database')
    else:
        return render_template('register.html')

@app.route('/recruiter')
def recruiter():
    if 'user_id' in session: 
        if session['user_id']==e_e:
            
            conn = create_connection()
            if conn is not None:
                try:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM users')
                    users = cursor.fetchall()
                    conn.close()
                    return render_template('recruiterdashboard.html', users=users,get_presigned_file_url=get_presigned_file_url)

                except mysql.connector.Error as e:
                    # Handle database error
                    logging.error(f"Database error: {e}")
                    flash('Failed to delete user', 'error')
                    return redirect('/login')
            else:
                
                logging.error('Failed to connect to the database')
                flash('Failed to connect to the database', 'error')
                return render_template('error.html')
        else: return render_template('forbidden1.html')
    else:
        return render_template('forbidden.html')    
   
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():    
    if 'user_id' in session:

        user_id = session.get('user_id')
        if user_id:       
                    username=session['username']     
                    user_id = session['user_id'] 
                    email=session['email'] 
                    home_address=session['home_address']
                    Education=session['Education']
                    Experience=session['Experience']  
                    pin=session['pin'] 
                    File_Name=session['File_Name']
                    state=session['state']  
                    country=session['country'] 
                    download_url=get_presigned_file_url(File_Name)
                        
                    return render_template('dashboard.html',username=username , user_id=user_id,
                                            email=email,
                                            home_address=home_address,
                                            pin=pin,File_Name=File_Name,download_url=download_url,Education=Education,
                                            Experience=Experience,state=state,
                                            country=country)
        else:
            return redirect(url_for('login'))
    else:
        return render_template('forbidden1.html')

i_i=0o35
@app.route('/update_user', methods=['POST'])  # Corrected method specification
def update_user():      
    if 'user_id' in session:
        if request.method == 'POST':
            
            user_id = request.form.get('user_id')
            username = request.form.get('username')
            email = request.form.get('email')
            experience=request.form.get('Experience')
            education=request.form.get('Education')
            home_address = request.form.get('home_address')
            pin = request.form.get('pin')
            state = request.form.get('state')
            country = request.form.get('country')

            # Update the session data with the new information   
            session['username'] = username
            session['email'] = email
            session['home_address'] = home_address
            session['Education'] = education
            session['Experience'] = experience  
            session['pin'] = pin
            session['state'] = state
            session['country'] = country
           
            conn = create_connection()
            try:
                if conn is not None:    
                        cursor = conn.cursor()
                        cursor.execute('UPDATE users SET id=%s, pin=%s, email=%s,Education=%s, Experience=%s, home_address=%s, state=%s, country=%s WHERE id=%s', ( user_id, pin, email,education,experience, home_address, state, country, session['user_id']))
                        conn.commit()
                        conn.close()    
                else:
                    logging.error('Failed to connect to the database')
                    return render_template('login.html', error='Failed to connect to the database')  
                return redirect(url_for('dashboard'))
            except mysql.connector.Error as e:
                # Handle database error
                logging.error(f"Database error: {e}")
                flash('Failed to delete user', 'error')
                return redirect('/login')           
    else:
        return render_template('forbidden1.html')



@app.route('/ping', methods=['POST', 'GET'])
def ping():
   
    if 'user_id' in session:
        url = request.args.get('url')
        if not url:
            return jsonify({'error': 'URL parameter is missing'}), 400

        temp_file = '/tmp/ping_output.txt'
        ping_command = f'ping -c 4 {url} > {temp_file}'
        os.system(ping_command)
        with open(temp_file, 'r') as file:
            output = file.read()
        if output.strip(): 
            return jsonify({'message': output}), 200
        else: 
            return jsonify({'message': 'Ping failed'}), 500
    else:
        return render_template('forbidden1.html')

@app.route('/delete_user', methods=['POST', 'GET'])
def delete_user():
    if 'user_id' in session:  # Check if the user is logged in
        user_id = request.form.get('user_id')  # Retrieve user ID from form data

        
        conn = create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor() 
                q = 'DELETE FROM users WHERE id = %s'
                cursor.execute(q, (user_id,))
                conn.commit()
                conn.close()
                return redirect('/logout')
            except mysql.connector.Error as e:
               
                logging.error(f"Database error: {e}")
                flash('Failed to delete user', 'error')
                return redirect('/login')
        else:
            
            logging.error('Failed to connect to the database')
            flash('Failed to connect to the database', 'error')
            return redirect('/login')
    else:   
        return render_template('forbidden.html')
   


# @app.route('/generate_pdf', methods=['GET'])
# def generate_pdf():
a_a=0x235
# Render the HTML page
# rendered_html = render_template('user_info_template.html')
    
# Create PDF from rendered HTML
# pdf = pdfkit.from_string(rendered_html, False, configuration=config)
e_e=0b1011# Specify the path to save the PDF
# Specify the path to save the PDF
# pdf_path = os.path.join(app.root_path, 'static', 'output1.pdf')
# Write the PDF content to the file
#with open(pdf_path, 'wb') as f:
# f.write(pdf)
#return 'PDF generated and saved successfully!'

@app.route('/logout')
def logout():
   
    session.clear()
    response = redirect(url_for('login'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


if __name__ == '__main__':
    app.run(host ="0.0.0.0" , port=int("8000"),debug=True)
