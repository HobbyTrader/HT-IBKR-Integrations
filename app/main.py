# from app.services.api_client import APIClient
# from app.core.database import get_db_connection

def main():
    print("Starting project...")
    conn = get_db_connection()
    api = APIClient()
    data = api.get_data("users")
    print("Fetched ", data)
    conn.close()

if __name__ == "__main__":
    main()