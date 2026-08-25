import pymysql
from urllib.parse import urlparse

# 1. Your Aiven Service URI
uri = "mysql://avnadmin:AVNS_fF_fOUGsItnRLvORNbA@cepproject-cepproject8485202526.c.aivencloud.com:21206/defaultdb?ssl-mode=REQUIRED"

# 2. Automatically split the URI into pieces Python can read
parsed = urlparse(uri)

# 3. Connect using the extracted parts
connection = pymysql.connect(
    host=parsed.hostname,
    port=parsed.port,
    user=parsed.username,
    password=parsed.password,
    database=parsed.path.lstrip('/'),
    ssl={'ssl': {}}  # Aiven requires SSL; this turns it on safely
)

try:
    with connection.cursor() as cursor:
        # 4. Define and run your query
        query = "truncate table startups;"
        cursor.execute(query)
        
        # 5. Print results cleanly
        results = cursor.fetchall()
        print("\n--- Query Results ---")
        for row in results:
            print(row)
            
finally:
    connection.close()
