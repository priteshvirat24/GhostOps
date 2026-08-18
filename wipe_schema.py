import psycopg

conn = psycopg.connect("postgresql://pritesh:ysRDe3WNkWdFAoptajYf0Q@valid-shaman-32362.j77.aws-ap-south-1.cockroachlabs.cloud:26257/ghostops?sslmode=verify-full&sslrootcert=/Users/priteshhome/.postgresql/root.crt", autocommit=True)
cur = conn.cursor()

cur.execute("DROP SCHEMA IF EXISTS public CASCADE;")
cur.execute("CREATE SCHEMA public;")

print("Schema public dropped and recreated.")
