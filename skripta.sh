#!bin/bash
#Prije pokretanja skripte pokrenuti sljedeće naredbe (pretpostavlja se da je Python već instaliran):
#python3 -m venv projekt
#source ~projekt/bin/activate
#smjestiti skriptu u /projekt/bin
#chmod +x skripta.sh
#sh skripta.sh
pip install pygame
pip install zodb
echo "Inicijalizacija baze podataka..."
db_file="dbfile.fs"
if [ ! -f "$db_file" ]; then
    sudo python3 -c "from ZODB.FileStorage import FileStorage; from ZODB.DB import DB; import transaction; storage = FileStorage('$db_file'); db = DB(storage); connection = db.open(); root = connection.root(); root['game_state'] = {'level': 1, 'life': 3, 'score': 0, 'highScore': 0}; transaction.commit(); connection.close(); db.close()"
    echo "Baza podataka je uspješno inicijalizirana."
else
    echo "Baza podataka već postoji."
fi
