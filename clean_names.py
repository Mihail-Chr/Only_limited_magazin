import sqlite3

conn = sqlite3.connect('db/only_limited.sqlite3')

# Обновляем baseGameName, убирая "Видеоигра " в начале
conn.execute("""
    UPDATE product 
    SET baseGameName = TRIM(REPLACE(baseGameName, 'Видеоигра ', ''))
    WHERE baseGameName LIKE 'Видеоигра %'
""")

conn.commit()
print("Названия очищены от слова 'Видеоигра'.")