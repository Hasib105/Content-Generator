import getpass
import os
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
else:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

if "TAVILY_API_KEY" not in os.environ:
    os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
else:
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    max_retries=3,
)

image_llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash-exp-image-generation",
    max_retries=3,
)

