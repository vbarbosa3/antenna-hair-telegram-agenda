"""Autoriza o bot a acessar o Google Calendar uma única vez."""
from google_calendar import authorize_and_test

if __name__ == "__main__":
    print(authorize_and_test())
    print("O arquivo token.json foi criado. Não publique esse arquivo.")
