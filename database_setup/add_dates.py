import os
import mysql.connector

# Check if a credentials file exists to read database login details
# If it does not exist, ask the user to enter them manually
if os.path.isfile('../credentials.txt'):
    with open("../credentials.txt", "r") as reader:
        u, p = [line.strip() for line in reader.readlines()]
else:
    u = input("Enter database user: ")
    p = input("Enter database password: ")

# Connect to the MySQL database using the provided credentials
# This connects to the local database that stores meal information
cnx = mysql.connector.connect(
    host="127.0.0.1",
    port=3308,
    user=u,
    password=p,
    database="meals"
)

# Create a cursor to execute SQL queries on the database
cur = cnx.cursor()

# Fetch the names of all meals currently stored in the table
cur.execute("SELECT Name FROM MealsTable;")
meals = [r[0] for r in cur.fetchall()]

# Update the Last_Made date for each meal to a fixed date
# This ensures the column has valid data for all existing meals
sql = "UPDATE MealsTable SET Last_Made = %s WHERE Name = %s"
for name in meals:
    cur.execute(sql, ("2021-04-23", name))

# Save the changes and close the database connection
cnx.commit()
cur.close()
cnx.close()

# Print a confirmation message once the update is completed
print(" Last_Made backfilled.")
