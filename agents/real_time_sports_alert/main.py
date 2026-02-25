#!/usr/bin/env python3
#import modules
import requests
import os
import pandas as pd
import time
import smtplib
import logging
import supabase  # Supabase
import socket
from dotenv import load_dotenv
from sqlalchemy import create_engine # Postgres
from firebase_admin import credentials, firestore # Firebase
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#######################
#####Configuration#####
#######################


### Environment Variables ###

# Load environment variables from the .env file
load_dotenv()

# API and Database Configuration
API_KEY = 'your_api_key_here'
BASE_URL = 'https://api.sportsdata.io/v3/nba/scores/json/'
POSTGRES_DB_URL = 'postgresql://username:password@localhost:5432/nba_db'  # Adjust with your PostgreSQL credentials
FIREBASE_DB_URL = ''
SUPABASE_DB_URL = ''

# Email envs
EMAIL_SENDER = 'your_email@example.com'
EMAIL_PASSWORD = 'your_email_password'
SMTP_SERVER = 'smtp.example.com'  # e.g., smtp.gmail.com
SMTP_PORT = 465  # For SSL, or 587 for TLS
EMAIL_RECIPIENT = 'recipient_email@example.com'

# NBA Season Dates
SEASON_START_DATE = date(2024, 10, 24)  # Adjust for season start
SEASON_END_DATE = date(2025, 4, 14)     # Adjust for season end

# Access environment variables
# database_url = os.getenv("DATABASE_URL")
# api_key = os.getenv("API_KEY")

# Create and configure logger
logging.basicConfig(filename="logger.log",
                    format='%(asctime)s %(message)s',
                    filemode='w',
                    level=logging.DEBUG)

# Test messages
# logger.debug("Harmless debug Message")
# logger.info("Just an information")
# logger.warning("Its a Warning")
# logger.error("Did you try to divide by zero")
# logger.critical("Internet is down")

###################
#####Functions#####
###################
def check_server_health():
  """
  Check if the server has an active internet connection.
  """
  try:
    # Attempt to connect to a reliable host
    socket.create_connection(("8.8.8.8", 53), timeout=5)
    print("Server is active and connected to the internet.")
    return True
  except (OSError, socket.error) as e:
    print("Server is inactive or disconnected from the internet:", e)
    return False

def fetch_game_data(game_date):
  """
  Fetch game data for a specific game ID.
  """
  url = f"{BASE_URL}GamesByDate/{game_date}"
  headers = {
    'Ocp-Apim-Subscription-Key': API_KEY
  }
  response = requests.get(url, headers=headers)
  if response.status_code == 200:
    logger.info(f"API Results returned")
    print("API Results: ", response.json())
    return response.json()
  else:
    logger.error(f"Error fetching data: {response.status_code}")
    # print("Error fetching data:", response.status_code)
    return None

def parse_data(game_data):
  """
  Parse the JSON data into a structured dictionary for database storage.
  """
  game_data = {
      'HomeTeam': game_data['HomeTeam'],
      'AwayTeam': game_data['AwayTeam'],
      'score_q1': game_data['HomeTeamScoreQuarter1'],
      'score_q2': game_data['HomeTeamScoreQuarter2'],
      'score_q3': game_data['HomeTeamScoreQuarter3'],
      'score_q4': game_data['HomeTeamScoreQuarter4'],
      'timestamp': datetime.now()  # Capture the timestamp of data extraction
  }
  parsed_data = pd.DataFrame([game_data])  # Convert to DataFrame for easy storage
  str_parsed_data = ''.join( f'{k}: {v}' for k,v in game_data.items())
  logger.info(f"{game_data['HomeTeam']} vs {game_data['AwayTeam']} Game Data: {str_parsed_data} ")
  # print(f"{game_data['HomeTeam']} vs {game_data['AwayTeam']}: {game_data}")
  return parsed_data

def send_email_notification(parsed_data):
  """
  Send an email notification with the parsed game data.
  """
  # Set up the email message
  msg = MIMEMultipart()
  msg['From'] = EMAIL_SENDER
  msg['To'] = EMAIL_RECIPIENT
  msg['Subject'] = f"NBA Game Update: {parsed_data['team1']} vs {parsed_data['team2']}"

  # Create the body of the email
  body = f"""
  New NBA Game Event Recorded:
  Teams: {parsed_data['team1']} vs {parsed_data['team2']}
  Scores:
    - Q1: {parsed_data['score_q1']}
    - Q2: {parsed_data['score_q2']}
    - Q3: {parsed_data['score_q3']}
    - Q4: {parsed_data['score_q4']}
  Timestamp: {parsed_data['timestamp']}
  """
  msg.attach(MIMEText(body, 'plain'))

  # Send the email
  try:
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    # print("Email sent successfully.")
    logger.info("Email sent successfully.")
  except Exception as e:
    # print("Failed to send email:", e)
    logger.error(f"Failed to send email: {e}")
    # with smtplib.SMTP_SSL('smtp.example.com', 465) as server:
    #     server.login('your_email@example.com', 'your_password')
    #     server.sendmail(msg['From'], [msg['To']], msg.as_string())

def store_to_postgresql(parsed_data):
  """
  Store the parsed data into the PostgreSQL database.
  """
  # Initialize the database connection
  engine = create_engine(POSTGRES_DB_URL)
  if engine is None:
    logger.error("Database connection not available.")
    raise Exception("Database connection not available.")
    return None
  # convert dataframe to structured table
  parsed_data.to_sql('nba_games', engine, if_exists='append', index=False)
  # print("Data ingested into Postgres database")
  logger.info("Data ingested into Postgres database")

def store_to_firebase(parsed_data):
  # Initialize the database connectionn
  cred = credentials.Certificate("path/to/firebase_credentials.json")
  firebase_admin.initialize_app(cred)

  # Access Firestore database
  db = firestore.client()

  # Get a document
  # doc_ref = db.collection('nba_games').document('game1')
  # doc = doc_ref.get()

  for _, row in df.iterrows():
    db.collection('nba_games').add(row.to_dict())
  # print("Data ingested into Firebase database:", parsed_data)
  logger.info("Data ingested into Firebase database")

def store_to_supabase(parsed_data):
  # Initialize the database connectionn
  client = supabase.create_client("your_supabase_url", "your_supabase_key")
  client.table("nba_games").insert(df.to_dict(orient='records')).execute()
  # print("Data ingested into Firebase database:", parsed_data)
  logger.info("Data ingested into Firebase database")

def poll_live_games(game_date, interval=30):
  """
  Poll live game data every `interval` seconds.
  """
  # Check if today is within the NBA season
  if not (SEASON_START_DATE <= date.today() <= SEASON_END_DATE):
    logger.warning("Outside of NBA season. The bot will wait until the next season.")
    # print("Outside of NBA season. The bot will wait until the next season.")
    return
  while True:
    # Check if today is still within the NBA seaso
    if not (SEASON_START_DATE <= date.today() <= SEASON_END_DATE):
      logger.info("NBA season ended. Shutting down the bot.")
      # print("NBA season ended. Shutting down the bot.")
      break

    # Check if the server is active
    # if not check_server_health():
    #   print("Waiting for server to become active...")
    #   time.sleep(30)  # Wait for 30 seconds before retrying
    #   continue  # Skip this loop iteration and retry

    game_data = fetch_game_data(game_date)

    if game_data:
      parsed_data = parse_data(game_data)
      store_to_postgresql(parsed_data)
    else:
      logger.info("No live data available.")
      # print("No live data available.")
    
    time.sleep(interval)  # Wait for the specified interval (in seconds)

########################
#####Execute Script#####
########################
if __name__ == "__main__":
  game_date = date.today().isoformat() #Format: YYYY-MM-DD
  poll_live_games(live_game_id, interval=30)  # Poll every minute (30 seconds)