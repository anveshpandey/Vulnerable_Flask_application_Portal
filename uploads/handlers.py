import mysql.connector


def create_connection():
    conn = mysql.connector.connect(
        host="",
        user="",  # Your MySQL username
        passwd="",  # Your MySQL password
        database=""
    )
    return conn


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc'}

def allowed_file(filename):
    if any(ext in filename for ext in ALLOWED_EXTENSIONS):
        return True
    # return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS