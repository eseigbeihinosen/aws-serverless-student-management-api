import json
import os
import boto3
import pymysql


# ----------------------------------------
# Database Connection
# ----------------------------------------
def get_connection():
    secret_name = os.environ["SECRET_NAME"]

    client = boto3.client(
        "secretsmanager",
        region_name="us-east-1"
    )

    response = client.get_secret_value(
        SecretId=secret_name
    )

    secret = json.loads(response["SecretString"])

    return pymysql.connect(
        host=secret["host"],
        user=secret["username"],
        password=secret["password"],
        database=secret["dbname"],
        cursorclass=pymysql.cursors.DictCursor
    )


# ----------------------------------------
# Standard API Response
# ----------------------------------------
def api_response(status, body):

    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, default=str)
    }


# ----------------------------------------
# Lambda Router
# ----------------------------------------
def lambda_handler(event, context):

    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]

    try:

        if path == "/students":

            if method == "GET":
                return get_students()

            elif method == "POST":
                return create_student(event)

        elif path.startswith("/students/"):

            student_id = int(
                event["pathParameters"]["student_id"]
            )

            if method == "GET":
                return get_student(student_id)

            elif method == "PUT":
                return update_student(student_id, event)

            elif method == "DELETE":
                return delete_student(student_id)

        return api_response(
            404,
            {
                "message": "Route not found"
            }
        )

    except Exception as e:

        print(e)

        return api_response(
            500,
            {
                "error": str(e)
            }
        )


 # ----------------------------------------
# GET /students
# ----------------------------------------
def get_students():

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT *
                FROM students
                ORDER BY student_id
            """)

            students = cursor.fetchall()

        return api_response(
            200,
            students
        )

    finally:
        conn.close()


# ----------------------------------------
# GET /students/{student_id}
# ----------------------------------------
def get_student(student_id):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT *
                FROM students
                WHERE student_id = %s
            """, (student_id,))

            student = cursor.fetchone()

        if not student:

            return api_response(
                404,
                {
                    "message": "Student not found"
                }
            )

        return api_response(
            200,
            student
        )

    finally:
        conn.close()


# ----------------------------------------
# POST /students
# ----------------------------------------
def create_student(event):

    body = json.loads(event["body"])

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                INSERT INTO students
                (
                    tenant_id,
                    first_name,
                    last_name,
                    gender,
                    date_of_birth,
                    class_name
                )
                VALUES
                (%s, %s, %s, %s, %s, %s)
            """,
            (
                body["tenant_id"],
                body["first_name"],
                body["last_name"],
                body["gender"],
                body["date_of_birth"],
                body["class_name"]
            ))

            conn.commit()

            student_id = cursor.lastrowid

        return api_response(
            201,
            {
                "message": "Student created successfully",
                "student_id": student_id
            }
        )

    finally:
        conn.close()     


 # ----------------------------------------
# PUT /students/{student_id}
# ----------------------------------------
def update_student(student_id, event):

    body = json.loads(event["body"])

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                UPDATE students
                SET
                    tenant_id = %s,
                    first_name = %s,
                    last_name = %s,
                    gender = %s,
                    date_of_birth = %s,
                    class_name = %s
                WHERE student_id = %s
            """,
            (
                body["tenant_id"],
                body["first_name"],
                body["last_name"],
                body["gender"],
                body["date_of_birth"],
                body["class_name"],
                student_id
            ))

            conn.commit()

            if cursor.rowcount == 0:
                return api_response(
                    404,
                    {
                        "message": "Student not found"
                    }
                )

        return api_response(
            200,
            {
                "message": "Student updated successfully"
            }
        )

    finally:
        conn.close()


# ----------------------------------------
# DELETE /students/{student_id}
# ----------------------------------------
def delete_student(student_id):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                DELETE FROM students
                WHERE student_id = %s
            """, (student_id,))

            conn.commit()

            if cursor.rowcount == 0:
                return api_response(
                    404,
                    {
                        "message": "Student not found"
                    }
                )

        return api_response(
            200,
            {
                "message": "Student deleted successfully"
            }
        )

    finally:
        conn.close()                