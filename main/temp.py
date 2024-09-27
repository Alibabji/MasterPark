import sqlite3

# Connect to your SQLite database (replace with your actual database file path)
conn = sqlite3.connect('user-info.db')
cursor = conn.cursor()

# Query to select all data from the 'users' table
cursor.execute("SELECT * FROM users;")
rows = cursor.fetchall()

# Print the fetched data
for row in rows:
    print(row)

# Close the connection
conn.close()
