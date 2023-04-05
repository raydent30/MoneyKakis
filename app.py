# ? Cross-origin Resource Sharing - here it allows the view and core applications deployed on different ports to communicate. No need to know anything about it since it's only used once
from flask_cors import CORS, cross_origin
# ? Python's built-in library for JSON operations. Here, is used to convert JSON strings into Python dictionaries and vice-versa
import json
# ? flask - library used to write REST API endpoints (functions in simple words) to communicate with the client (view) application's interactions
# ? request - is the default object used in the flask endpoints to get data from the requests
# ? Response - is the default HTTP Response object, defining the format of the returned data by this api
from flask import Flask, request, Response, render_template, url_for, flash, redirect, session
# ? sqlalchemy is the main library we'll use here to interact with PostgresQL DBMS
import sqlalchemy
import psycopg2
# ? Just a class to help while coding by suggesting methods etc. Can be totally removed if wanted, no change
from typing import Dict
# a class to help with password hashing before storing it in the database for security 
# from werkzeug.security import generate_password_hash 


"""
    note:

    CRUD operations have already been implemented by the TA.

    We now need to create our own functions and write custom sql for them. 
"""

""" create a group
    
    def create_group():
    
    def gen_create_group_statement()-> str:
        return statement
"""


# ? web-based applications written in flask are simply called apps are initialized in this format from the Flask base class. You may see the contents of `__name__` by hovering on it while debugging if you're curious
app = Flask(__name__)
app.secret_key = 'mysecretkey'
app.debug = True

# ? Just enabling the flask app to be able to communicate with any request source
CORS(app)

# ? building our `engine` object from a custom configuration string
# ? for this project, we'll use the default postgres user, on a database called `postgres` deployed on the same machine
YOUR_POSTGRES_PASSWORD = "postgres"
connection_string = f"postgresql://postgres:{YOUR_POSTGRES_PASSWORD}@localhost/postgres"
engine = sqlalchemy.create_engine(
    "postgresql://postgres:postgres@localhost/postgres"
)

# ? `db` - the database (connection) object will be used for executing queries on the connected database named `postgres` in our deployed Postgres DBMS
db = engine.connect()

with open('schema.sql', 'r') as s:
    schema = s.read()
    db.execute(sqlalchemy.text(schema))
    db.commit()
'''
with open('triggers.sql', 'r') as f:
    triggers = f.read()
# executing triggers in the background
    db.execute(sqlalchemy.text(triggers))
    db.commit()
''' 

# ? A dictionary containing
data_types = {
    'boolean': 'BOOL',
    'integer': 'INT',
    'text': 'TEXT',
    'time': 'TIME',
}

@app.route("/")
def index():
    return render_template("frontview.html")

ADMIN_MAIL = "admin@adminmail.com"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        input_email = request.form.get('email')
        input_password = request.form.get('password')
        # check if the input email even exists - if it does then check password if not then return error message and ask to sign up
        statement = sqlalchemy.text("SELECT * FROM users WHERE email = :email")
        params = {'email':input_email}
        # returns as a tuple - can index into the tuple knowing the schema
        res = db.execute(statement, params).fetchone()
        if res == None:
            # return error message and prompt to sign up
            flash("Invalid e-mail/password: E-mail does not exist. Sign up now in the link below!", category='error')
            return redirect(url_for('login'))
        else:
            # check the password as well
            if input_password == res[3]:
                # storing email to get info from database and name to welcome the person
                session['email'] = res[2]
                session['name'] = res[1]
                session['id'] = res[0]


                # Check if admin

                if input_email == ADMIN_MAIL:
                    return redirect(url_for('admin_home'))

                flash('Login successful! Welcome.', category='success')
                
                return redirect(url_for('userguide'))
                
                # log him in 
            else: 
                flash("Invalid e-mail/password: Wrong e-mail password combination. Try again.")
                return redirect(url_for('login'))
                
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        country = request.form.get('country')


        try:
            statement = sqlalchemy.text('INSERT INTO users (name, email, password, country) VALUES (:name, :email, :password, :country)')
            params = {'name': name, 'email': email, 'password': password, 'country': country}
            db.execute(statement, params)
            db.commit()
            flash('Registration was successful!', category='success')
            return redirect(url_for('login'))
        except Exception as e:
            db.rollback()
            if "Email already" in str(e):
                flash('Invalid e-mail: E-mail already in use.')
                return redirect(url_for('register'))
            elif "Password must" in str(e):
                flash("Invalid password: Password must be at least 8 characters long and contain at least one uppercase and lowercase character")
                return redirect(url_for('register'))
    else:
        return render_template("register.html")

@app.get('/userguide')
def userguide():
    return render_template("userguide.html")

########################################## ADMIN CODE BEGINS HERE ##########################################

@app.route('/admin_home', methods=['GET', 'POST'])
def admin_home():
    result = None
    headers = None

    if request.method == 'POST':
        ###### "Data Analytics" queries here ######
        if request.form['action'] == 'Query':
            conn = psycopg2.connect(dbname='postgres', user='postgres', password='postgres', host='localhost')

            # Create a cursor object
            cur = conn.cursor()

            # Get the selected query type from the form
            query_type = request.form.get('query_type')

            # Perform the selected query
            if query_type == 'list_users':
                cur.execute('SELECT * FROM users')
                headers = [desc[0] for desc in cur.description] 
                result = cur.fetchall()
            elif query_type == 'list_groups':
                cur.execute('SELECT * FROM groups')
                headers = [desc[0] for desc in cur.description] 
                result = cur.fetchall()
            elif query_type == 'list_group_members':
                cur.execute('SELECT * FROM group_members')
                headers = [desc[0] for desc in cur.description] 
                result = cur.fetchall()
            else:
                result = None

            # Close the cursor and connection
            cur.close()
            conn.close()

            # Render the template with the query result
            return render_template('admin_pages/adminHome.html', headers=headers, result=result)
        ###### "Data Analytics" queries here ######
        else:
            group_or_user = request.form.get('group_or_user')
            add_or_delete = request.form.get('add_or_delete')

            if (group_or_user=="group" and add_or_delete=="add"):
                return redirect(url_for('admin_group_add'))
            elif (group_or_user=="group" and add_or_delete=="delete"):
                return redirect(url_for('admin_group_delete'))
            elif (group_or_user=="user" and add_or_delete=="add"):
                return redirect(url_for('admin_user_add'))
            elif (group_or_user=="user" and add_or_delete=="delete"):
                return redirect(url_for('admin_user_delete'))

    return render_template('admin_pages/adminHome.html', headers=headers, result=result)

@app.route('/admin_group_add', methods=['GET', 'POST'])
def admin_group_add():
    if request.method == "POST":
        name = request.form.get('name')
        passcode = request.form.get('passcode')

        try:
            conn = psycopg2.connect(dbname='postgres', user='postgres', password='postgres', host='localhost')
            cur = conn.cursor()

            cur.execute("INSERT INTO groups (name, passcode) VALUES (%s, %s)", (name, passcode))
            conn.commit()

            cur.close()
            conn.close()
            
            flash('Registration was successful!', category='success')
            return redirect(url_for('admin_group_add'))
        except Exception as e:
            db.rollback()
            if "Password must" in str(e):
                flash("Invalid password: Password must be at least 8 characters long and contain at least one uppercase and lowercase character")
                return redirect(url_for('admin_group_add'))

    return render_template('admin_pages/adminGroupAdd.html')

@app.route('/admin_group_delete', methods=['GET', 'POST'])
def admin_group_delete():
    if request.method == "POST":
        id = request.form.get('id')

        try:
            conn = psycopg2.connect(dbname='postgres', user='postgres', password='postgres', host='localhost')
            cur = conn.cursor()

            cur.execute("DELETE FROM group_members WHERE group_id = %s", (id,))
            cur.execute("DELETE FROM groups WHERE id = %s", (id,))
            conn.commit()

            cur.close()
            conn.close()
            
            flash('Deletion was successful!', category='success')
            return redirect(url_for('admin_group_delete'))
        except Exception as e:
            db.rollback()
            flash("Please enter a valid group ID.")
            return redirect(url_for('admin_group_delete'))
    return render_template('admin_pages/adminGroupDelete.html')

@app.route('/admin_user_add', methods=['GET', 'POST'])
def admin_user_add():
    if request.method == "POST":
        userID = request.form.get('userid')
        groupID = request.form.get('groupid')

        try:
            conn = psycopg2.connect(dbname='postgres', user='postgres', password='postgres', host='localhost')
            cur = conn.cursor()

            cur.execute("INSERT INTO group_members (user_id, group_id) VALUES (%s, %s)", (userID, groupID))
            conn.commit()

            cur.close()
            conn.close()
            
            flash('Added user to group!', category='success')
            return redirect(url_for('admin_user_add'))
        except Exception as e:
            db.rollback()
            flash("Please enter valid user and group IDs")
            return redirect(url_for('admin_user_add'))

    return render_template('admin_pages/adminUserAdd.html')

@app.route('/admin_user_delete', methods=['GET', 'POST'])
def admin_user_delete():
    if request.method == "POST":
        userID = request.form.get('userid')
        groupID = request.form.get('groupid')

        try:
            conn = psycopg2.connect(dbname='postgres', user='postgres', password='postgres', host='localhost')
            cur = conn.cursor()

            cur.execute("DELETE FROM group_members WHERE user_id = %s AND group_id = %s", (userID, groupID))
            conn.commit()

            cur.close()
            conn.close()
            
            flash('Deleted user from group!', category='success')
            return redirect(url_for('admin_user_delete'))
        except Exception as e:
            db.rollback()
            flash("Please enter valid user and group IDs")
            return redirect(url_for('admin_user_delete'))

    return render_template('admin_pages/adminUserDelete.html')

########################################## ADMIN CODE ENDS HERE ##########################################



"""
dashboard logic:
    for the user:
        get a list of all groups they are in [-> list]
    end for
    
    for group in that list:
        find all those who owe you money, print that amount
        find all those who you owe money, print that amount
    end for

SQL - Equivalent

SELECT g.name, g.id, FROM group_members gm, groups g WHERE gm.group

"""

@app.route('/groupexpenses/<gid>', methods=["GET", "POST"])
def groupexpenses(gid):
    session["groupid"] = gid
    if request.method == "GET":
        # query through the group_id to get all the expenses
        query = sqlalchemy.text("SELECT E.name, E.user_id, u1.name, E.amount, E.id\
                                FROM expenses E, users u1 \
                                WHERE E.id IN (SELECT e.id FROM expenses e, group_members gm, users u WHERE e.group_id = :group_id AND u.id = e.user_id GROUP BY e.id) \
                                AND E.user_id = u1.id")
        params = {"group_id": gid}
        expenses_data = db.execute(query, params).fetchall()
        print(len(expenses_data))
        query_for_grpmembers = sqlalchemy.text('SELECT COUNT(gm.user_id)\
                                                FROM group_members gm WHERE\
                                                gm.group_id = :groupid \
                                                ;') 
        query_for_names = sqlalchemy.text('SELECT u.id, u.name \
                                           FROM users u \
                                            WHERE u.id IN (SELECT gm.user_id \
                                            FROM groups g, group_members gm \
                                            WHERE g.id = :grpid AND \
                                            gm.group_id = :grpid) AND u.id \
                                            <> :id;') # nested query !!
        params_names = {"grpid": gid, "id":session["id"]}
        data_fornames = db.execute(query_for_names, params_names).fetchall()
        params_no = {"groupid": gid}
        totalnoOfmembers = db.execute(query_for_grpmembers, params_no).fetchone()

        query_groupname = sqlalchemy.text('SELECT g.name FROM groups g WHERE g.id = :groupID;')
        params_grpname = {"groupID": gid}
        get_groupname = db.execute(query_groupname, params_grpname).fetchone()

        
        return render_template('groupexpenses.html', data=expenses_data, number=totalnoOfmembers, names=data_fornames, groupname=get_groupname)


@app.route("/home", methods=["GET", "POST"])
def home():
    if 'email' in session:
        statement = sqlalchemy.text("SELECT g.name, g.id \
                                FROM group_members gm, groups g \
                                WHERE gm.group_id = g.id \
                                AND gm.user_id = :userid")
        params = {"userid": session["id"]}
        group_data = db.execute(statement, params).fetchall()
        return render_template("home.html", name=session["name"], group_data=group_data)
    return redirect(url_for("login"))
    
@app.get("/managegroups")
def managegroups():
    return render_template("managegroups.html")

# Called when the Join Group form is submitted
@app.post("/joingroup")
def joingroup():
    group_ID = request.form.get("groupID")
    passcode = request.form.get("passcode")
    # Check to make sure group ID exists and passcode matches
    statement = sqlalchemy.text("SELECT * \
                                FROM groups \
                                WHERE id = :id")
    params = {"id": group_ID}
    res = db.execute(statement, params).fetchone()
    # Check to ensure the group ID entered exists
    if res == None:
        # The group ID entered does not exist
        flash("Error: group ID entered does not exist", category='error')
    else:   # Group ID exists
        # Check to ensure passcode is correct
        if passcode == res[2]:
            # Passcode is correct - now check to make sure the user has not already joined this group
            statement = sqlalchemy.text("SELECT * \
                                        FROM group_members \
                                        WHERE user_id = :user_id \
                                        AND group_id = :group_id")
            params = {"user_id": session["id"], "group_id": group_ID}
            if db.execute(statement, params).fetchone() == None:
                # The user has not yet joined this group
                try:
                    statement = sqlalchemy.text("INSERT INTO group_members (user_id, group_id) VALUES (:user_id, :group_id)")
                    params = {"user_id": session["id"], "group_id": group_ID}
                    db.execute(statement, params)
                    db.commit()
                    flash("Successfully joined group!", category="success")
                except Exception as e:
                    db.rollback()
                    flash("There was an error when attempting to join group.", category="error")
            else:   # The user has already joined this group
                flash("Error: you have already joined this group.")
        else:   # Passcode is incorrect
            flash("Error: group ID and passcode do not match. Please try again.")
    return redirect(url_for("managegroups"))

# Called when the create group form is submitted
@app.post("/creategroup")
def creategroup():
    group_name = request.form.get("groupname")
    passcode = request.form.get("passcode")
    # Create the group and add the user to it.
    try:
        # Return the id of the group created so we can add the user to it if the group is created successfully.
        # Group creation and member addition should both be part of the same transaction - either both occur or neither occur.
        statement = sqlalchemy.text("INSERT INTO groups (name, passcode) VALUES (:groupname, :passcode) RETURNING id")
        params = {"groupname": group_name, "passcode": passcode}
        group_id = db.execute(statement, params).fetchone()[0]
        statement = sqlalchemy.text("INSERT INTO group_members (user_id, group_id) VALUES (:userid, :groupid)")
        params = {"userid": session["id"], "groupid": group_id}
        db.execute(statement, params)
    except Exception:
        db.rollback()
        flash("An error occurred. Group not created.", category="error")
    else:
        # Both statements were executed successfully. We now commit the transaction to the database.
        db.commit()
        # Tell the user what their group ID is. The user can then share this ID with their friends in order for them to be able to join the group.
        flash(f"Group created successfully! Your group ID is: {group_id}. \nPlease save this number and share it, along with your passcode, to anyone who you invite to join your group.", category="success")
    return redirect(url_for("managegroups"))

@app.route('/addexpenses', methods=["POST"])
def addexpense():
    type = request.form.get('name')
    g_id = session["groupid"]
    amount = request.form.get('amount')
    u_id = session["id"]
    try:
        insertion_query = sqlalchemy.text('INSERT INTO expenses(name, user_id, group_id, amount) VALUES (:type, :userid, :groupid, :amount);')
        params = {"type": type, "userid":u_id, "groupid":g_id, "amount":amount}
        db.execute(insertion_query,params)
        db.commit()
        flash('Expense added successfully', category='success')
        return redirect(url_for('groupexpenses', gid=g_id))
    except Exception:
        db.rollback()
        flash('Amount entered is invalid: make sure amount is greater than $0 and key in 2 decimal places (i.e 30.00)', category='error')
        return redirect(url_for('groupexpenses', gid=g_id))
    
@app.route('/settleup', methods=["POST"])
def settleup():
    expense_id = request.form.get('expenseid')
    print(expense_id)
    query_delete = sqlalchemy.text('DELETE FROM expenses e WHERE e.id = :eid;')
    params = {"eid":expense_id}
    db.execute(query_delete, params)
    db.commit()
    return redirect(url_for('groupexpenses', gid=session["groupid"]))

    
@app.route('/logout', methods=["POST", "GET"])
def logout():
    session.clear()
    return render_template('frontview.html')

# ? @app.get is called a decorator, from the Flask class, converting a simple python function to a REST API endpoint (function)

'''
@app.get("/table")
def get_relation():
    # ? This method returns the contents of a table whose name (table-name) is given in the url `http://localhost:port/table?name=table-name`
    # ? Below is the default way of parsing the arguments from http url's using flask's request object
    relation_name = request.args.get('name', default="", type=str)
    # ? We use try-except statements for exception handling since any wrong query will crash the whole flow
    try:
        # ? Statements are built using f-strings - Python's formatted strings
        # ! Use cursors for better results
        statement = sqlalchemy.text(f"SELECT * FROM {relation_name};")
        # ? Results returned by the DBMS after execution are stored into res object defined in sqlalchemy (for reference)
        res = db.execute(statement)
        # ? committing the statement writes the db state to the disk; note that we use the concept of rollbacks for safe DB management
        db.commit()
        # ? Data is extracted from the res objects by the custom function for each query case
        # ! Note that you'll have to write custom handling methods for your custom queries
        data = generate_table_return_result(res)
        # ? Response object is instantiated with the formatted data and returned with the success code 200
        return Response(data, 200)
    except Exception as e:
        # ? We're rolling back at any case of failure
        db.rollback()
        # ? At any error case, the error is returned with the code 403, meaning invalid request
        # * You may customize it for different exception types, in case you may want
        return Response(str(e), 403)


# ? a flask decorator listening for POST requests at the url /table-create
@app.post("/table-create")
def create_table():
    # ? request.data returns the binary body of the POST request
    data = request.data.decode()
    try:
        # ? data is converted from stringified JSON to a Python dictionary
        table = json.loads(data)
        # ? data, or table, is an object containing keys to define column names and types of the table along with its name
        statement = generate_create_table_statement(table)
        # ? the remaining steps are the same
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/table-insert")
# ? a flask decorator listening for POST requests at the url /table-insert and handles the entry insertion into the given table/relation
# * You might wonder why PUT or a similar request header was not used here. Fundamentally, they act as POST. So the code was kept simple here
def insert_into_table():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        insertion = json.loads(data)
        statement = generate_insert_table_statement(insertion)
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/table-update")
# ? a flask decorator listening for POST requests at the url /table-update and handles the entry updates in the given table/relation
def update_table():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        update = json.loads(data)
        statement = generate_update_table_statement(update)
        db.execute(statement)
        db.commit()
        return Response(statement.text, 200)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/entry-delete")
# ? a flask decorator listening for POST requests at the url /entry-delete and handles the entry deletion in the given table/relation
def delete_row():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        delete = json.loads(data)
        statement = generate_delete_statement(delete)
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


def generate_table_return_result(res):
    # ? An empty Python list to store the entries/rows/tuples of the relation/table
    rows = []

    # ? keys of the SELECT query result are the columns/fields of the table/relation
    columns = list(res.keys())

    # ? Constructing the list of tuples/rows, basically, restructuring the object format
    for row_number, row in enumerate(res):
        rows.append({})
        for column_number, value in enumerate(row):
            rows[row_number][columns[column_number]] = value

    # ? JSON object with the relation data
    output = {}
    output["columns"] = columns  # ? Stores the fields
    output["rows"] = rows  # ? Stores the tuples

    """
        The returned object format:
        {
            "columns": ["a","b","c"],
            "rows": [
                {"a":1,"b":2,"c":3},
                {"a":4,"b":5,"c":6}
            ]
        }
    """
    # ? Returns the stringified JSON object
    return json.dumps(output)


def generate_delete_statement(details: Dict):
    # ? Fetches the entry id for the table name
    table_name = details["relationName"]
    id = details["deletionId"]
    # ? Generates the deletion query for the given entry with the id
    statement = f"DELETE FROM {table_name} WHERE id={id};"
    return sqlalchemy.text(statement)


def generate_update_table_statement(update: Dict):

    # ? Fetching the table name, entry/tuple id and the update body
    table_name = update["name"]
    id = update["id"]
    body = update["body"]

    # ? Default for the SQL update statement
    statement = f"UPDATE {table_name} SET "
    # ? Constructing column-to-value maps looping
    for key, value in body.items():
        statement += f"{key}=\'{value}\',"

    # ?Finalizing the update statement with table and row details and returning
    statement = statement[:-1]+f" WHERE {table_name}.id={id};"
    return sqlalchemy.text(statement)


def generate_insert_table_statement(insertion: Dict):
    # ? Fetching table name and the rows/tuples body object from the request
    table_name = insertion["name"]
    body = insertion["body"]
    valueTypes = insertion["valueTypes"]

    # ? Generating the default insert statement template
    statement = f"INSERT INTO {table_name}  "

    # ? Appending the entries with their corresponding columns
    column_names = "("
    column_values = "("
    for key, value in body.items():
        column_names += (key+",")
        if valueTypes[key] == "TEXT" or valueTypes[key] == "TIME":
            column_values += (f"\'{value}\',")
        else:
            column_values += (f"{value},")

    # ? Removing the last default comma
    column_names = column_names[:-1]+")"
    column_values = column_values[:-1]+")"

    # ? Combining it all into one statement and returning
    #! You may try to expand it to multiple tuple insertion in another method
    statement = statement + column_names+" VALUES "+column_values+";"
    return sqlalchemy.text(statement)


def generate_create_table_statement(table: Dict):
    # ? First key is the name of the table
    table_name = table["name"]
    # ? Table body itself is a JSON object mapping field/column names to their values
    table_body = table["body"]
    # ? Default table creation template query is extended below. Note that we drop the existing one each time. You might improve this behavior if you will
    # ! ID is the case of simplicity
    statement = f"DROP TABLE IF EXISTS {table_name}; CREATE TABLE {table_name} (id serial NOT NULL PRIMARY KEY,"
    # ? As stated above, column names and types are appended to the creation query from the mapped JSON object
    for key, value in table_body.items():
        statement += (f"{key}"+" "+f"{value}"+",")
    # ? closing the final statement (by removing the last ',' and adding ');' termination and returning it
    statement = statement[:-1] + ");"
    return sqlalchemy.text(statement)

"""
    Matt's Note:

    Maybe can modify the above function so that the primary key is whatever we need it to be. Maybe make it known that
    the first entry will always be the primary key?

    this way there is no way to get composite keys. 
"""
'''


# ? This method can be used by waitress-serve CLI 
def create_app():
   return app

# ? The port where the debuggable DB management API is served
PORT = 4173
# ? Running the flask app on the localhost/0.0.0.0, port 2222
# ? Note that you may change the port, then update it in the view application too to make it work (don't if you don't have another application occupying it)
if __name__ == "__main__":
    app.run("0.0.0.0", PORT)
    # ? Uncomment the below lines and comment the above lines below `if __name__ == "__main__":` in order to run on the production server
    # ? Note that you may have to install waitress running `pip install waitress`
    # ? If you are willing to use waitress-serve command, please add `/home/sadm/.local/bin` to your ~/.bashrc
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=PORT)

