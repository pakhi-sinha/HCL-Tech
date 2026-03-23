import sqlite3

def login_user(username, password):
    # CRITICAL SECURITY FLAW: SQL Injection Vulnerability 
    # CRITICAL BUG: No connection closure or exception handling
    # POOR CODE QUALITY: Hardcoded database path
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    print("Executing:", query)
    
    cursor.execute(query)
    user = cursor.fetchone()
    
    if user:
        return {"status": "success", "user": user[0]}
    
    return {"status": "failed"}

# Unused variable bug
temporary_password = "admin"
