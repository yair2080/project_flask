# app.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import requests
import logging
import os

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://user:password@db/questions_db')

app = Flask(__name__)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class QA(Base):
    __tablename__ = 'qa'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)

def get_openai_response(question):
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": question}],
        "max_tokens": 150
    }
    logger.debug(f"Sending request to OpenAI API: {data}")
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    logger.debug(f"Received response from OpenAI API: {response.status_code}")
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        logger.error(f"OpenAI API error: {response.text}")
        return None

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        logger.debug(f"Received data: {data}")
        question = data.get('question')
        if not question:
            logger.warning("No question provided")
            return jsonify({"error": "No question provided"}), 400

        logger.debug(f"Sending question to OpenAI: {question}")
        answer = get_openai_response(question)
        if answer is None:
            logger.error("Failed to get answer from OpenAI API")
            return jsonify({"error": "Failed to get answer from OpenAI API"}), 500

        logger.debug(f"Received answer from OpenAI: {answer}")

        db = SessionLocal()
        try:
            qa = QA(question=question, answer=answer)
            db.add(qa)
            db.commit()
            db.refresh(qa)
            logger.info(f"Saved QA pair with id {qa.id}")
            return jsonify({"id": qa.id, "question": qa.question, "answer": qa.answer})
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            return jsonify({"error": "Database error"}), 500
        finally:
            db.close()
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Unexpected error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200