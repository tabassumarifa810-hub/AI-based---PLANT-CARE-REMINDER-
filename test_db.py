from db import get_db_connection

try:
	connection = get_db_connection()
	print("PlantCare database connected successfully!")
	connection.close()

except Exception as error:
	print("Database connection failed:", error)
