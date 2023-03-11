from typing import Dict, Final
import os
import shelve
from dataclasses import dataclass

def read_old_database(database_dir: str) -> Dict[int, int]:
    database = {}
    # read the database and convert to sqlitedatabase
    print('Loading the database...')

    try:
        for filename in os.listdir(database_dir):
            with open(DATABASE_DIR + '/' + filename) as f:
                database[int(filename)] = int(f.read())
        print('Database loaded successfully:')
        print(database)
    except FileNotFoundError:
        print(f'Error: {database_dir} not found')

    return database
def save_user_to_file(db, userid: str):
    with open(DATABASE_DIR + '/' + userid, 'w') as f:
        print(db[userid], file=f)


@dataclass
class Userdata:
    days: int = 0
    days_since_last_check: int = 0
    farm_progress: int = 0

#some code to modify current database
if __name__ == '__main__':
    DATABASE_DIR: Final[str] = 'database.d'
    DATABASE_FILENAME: Final[str] = 'database.db'

    db = {
    #392580231:  Userdata(0,  0, 0),
    664863967:  Userdata(24, 0, 0),
    }
    shelf = shelve.open(DATABASE_FILENAME)

    #for key, value in db.items():
        #shelf[str(key)] = value

    for key, value in shelf.items():
        shelf[key] = Userdata(value, 0, 0)

    for key, value in shelf.items():
        print(key, value)


    shelf.close()

