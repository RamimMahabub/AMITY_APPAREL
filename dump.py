import sqlite3

try:
    con = sqlite3.connect('instance/amity_apparel.db')
    with open('database.sql', 'w', encoding='utf-8') as f:
        for line in con.iterdump():
            f.write('%s\n' % line)
    con.close()
    print("Database dumped successfully to database.sql")
except Exception as e:
    print(f"Error dumping database: {e}")
