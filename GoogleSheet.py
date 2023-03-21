#Ejemplo de prueba para integrar Google Sheet en vez de un excel

import datetime
import openpyxl
import os.path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Obtener la fecha actual
today = datetime.date.today().strftime('%Y-%m-%d')

# Verificar si las credenciales de OAuth 2.0 ya existen
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/spreadsheets'])
else:
    print('No se encontró el archivo de credenciales.')

# ID de la hoja de Google Sheets
spreadsheet_id = 'YOUR_SPREADSHEET_ID'

# Nombre de la hoja de Google Sheets
sheet_name = 'Sheet1'

# Crear un nuevo libro de Excel
workbook = openpyxl.Workbook()
sheet = workbook.active
sheet['A1'] = 'Mensaje'
sheet['B1'] = 'Fecha y hora'

# Ejecutar la función print y guardar la información en la hoja de Google Sheets
print('Hola, mundo!')
row = (f'Hola, mundo!', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
sheet.append(row)

# Guardar el archivo de Excel como un archivo temporal
temp_file = f'informacion_{today}.xlsx'
workbook.save(temp_file)

# Subir el archivo temporal a la hoja de Google Sheets
try:
    # Autenticar y crear una instancia del servicio de hojas de Google
    service = build('sheets', 'v4', credentials=creds)
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_id = sheet_metadata['sheets'][0]['properties']['sheetId']
    url = sheet_metadata['spreadsheetUrl']

    # Subir el archivo como un nuevo archivo adjunto a la hoja de Google Sheets
    file_metadata = {'name': temp_file}
    media = googleapiclient.http.MediaFileUpload(temp_file, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    # Convertir el archivo adjunto en una imagen en la hoja de Google Sheets
    requests