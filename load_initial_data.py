from app.database import setup_database, load_csv_to_db

def load_initial_data():
    setup_database()
    load_csv_to_db("data/internships.csv", "internships")
    load_csv_to_db("data/students.csv", "students")
    print("Initial data loaded successfully.")

if __name__ == "__main__":
    load_initial_data()
