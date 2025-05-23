import os
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Optional
from pydantic import BaseModel, Field
from tools import generate_content_with_search, generate_seo_hashtags, generate_social_media_thumbnail

load_dotenv()

if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
else:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]


class ContentOutput(BaseModel):
    title: str = Field(description="The title of the generated content")
    content: str = Field(description="The main body of generated content")
    hashtags: List[str] = Field(default_factory=list, description="SEO optimized hashtags for social media")
    thumbnail_url: Optional[str] = Field(default=None, description="URL or data for the generated thumbnail image")


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    max_retries=3,
    api_key=os.environ["GEMINI_API_KEY"],
)

tools = [generate_content_with_search, generate_seo_hashtags, generate_social_media_thumbnail]
chat_with_tools = llm.bind_tools(tools)
structured_llm = llm.with_structured_output(ContentOutput)