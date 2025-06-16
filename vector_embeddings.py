import pymysql
import os, openai, json
import numpy as np
from openai import OpenAI

# read environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# connect to tidb database
conn = pymysql.connect(host="127.0.0.1", port=62919, user="root", password="", database="test")

cursor = conn.cursor()

client=OpenAI(api_key="OPENAI_API_KEY")

# read rows that still need an embedding (those w/ empty _vec)
cursor.execute("SELECT id, description FROM user WHERE description_vec IS NULL")

rows=cursor.fetchall()

for uid, text in rows:
    # obtain embeddings
    response=client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        encoding_format="float"
    )
    
    # put in array
    vec = np.array(response.data[0].embedding,dtype=float)

    # TiDB accepts the bracketed string form:  [0.1, -0.2, …]
    vec_str = "[" + ",".join(f"{x:.7g}" for x in vec) + "]"

    # update description_vec field
    cursor.execute("UPDATE user SET description_vec = CAST(%s AS VECTOR(1536)) WHERE id = %s",(vec_str, uid))

# submit updates
conn.commit()
conn.close()

print("successful update!")
