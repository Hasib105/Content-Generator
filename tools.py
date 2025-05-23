import os
import streamlit as st
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from google.ai.generativelanguage_v1beta.types import Tool as GenAITool
import requests
from PIL import Image
import base64
from io import BytesIO
import uuid

load_dotenv()

if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
else:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    max_retries=3,
    api_key=os.environ["GEMINI_API_KEY"],
)


def tavily_search(keyword: str) -> str:
    tavily = TavilySearchResults()
    return tavily.run(keyword)


def google_search(content: str) -> str:
    """Generates comprehensive and engaging content using the latest search results."""
    search_resp = llm.invoke(
        [HumanMessage(content=content)],
        tools=[GenAITool(google_search={})],
    )
    return search_resp.content


@tool
def generate_content_with_search(content: str, word_count: int = 300) -> str:
    """
    Generates high-quality content based on the latest search results for a keyword.
    
    Args:
        content: The topic or search term to generate content about
        word_count: Target word count for the generated content (default: 300)
        
    Returns:
        Researched, well-structured content based on latest information
    """
    try:
        search_result = google_search(content)
        
        system_prompt = "You are an expert content creator and researcher."
        human_prompt = f"""Create high-quality, informative content (approximately {word_count} words) based on these search results:
                        
        {search_result}
                                
        Focus on accuracy, relevance, and natural tone. Structure the content logically with 
        appropriate headings if needed. Synthesize the information into a coherent response 
        that addresses the content: "{content}".
        """
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
        )
        
        return response.content
    except Exception as e:
        return f"Error generating content: {str(e)}"


@tool
def generate_seo_hashtags(content: str) -> list:
    """Generates SEO-optimized hashtags based on the given content."""
    response = llm.invoke(
        [
            SystemMessage(
                content="""You are an SEO expert specializing in hashtag optimization for social media.
                Create 10-15 highly relevant hashtags that will maximize content discoverability.
                Include a mix of popular (high volume) and niche (low competition) hashtags.
                Focus on trending topics and search terms related to the content.
                Return ONLY the hashtags in a clean format, without explanations or numbering."""
            ),
            HumanMessage(content=f"Generate SEO-optimized hashtags for this content:\n\n{content}"),
        ]
    )
    
    hashtags = response.content.strip().replace('\n', ' ').split(' ')
    hashtags = [tag for tag in hashtags if tag.startswith('#')]
    
    return hashtags


def thumbnail_prompt(content: str) -> str:
    """Generates a high-quality thumbnail prompt for digital marketing content."""
    response = llm.invoke(
        [
            SystemMessage(
                content="""You are a professional digital marketing thumbnail designer.
                Create a compelling thumbnail prompt that will attract clicks and conversions.
                
                Your thumbnail prompts should include:
                - Clear focal subject that represents the marketing message
                - Vibrant, eye-catching colors appropriate for the brand
                - Professional lighting effects (soft shadows, highlights)
                - Balanced composition with strong visual hierarchy
                - Modern, clean aesthetic with appropriate depth of field
                - Space for text overlay if needed
                
                Keep the prompt between 30-40 words, focused on digital marketing best practices.
                Format as a detailed image prompt with style descriptors (photorealistic, 3D render, etc.)."""
            ),
            HumanMessage(content=f"Generate a high-quality thumbnail prompt for this digital marketing content:\n\n{content}"),
        ]
    )
    return response.content


def ensure_image_folder_exists():
    """Ensure the images folder exists."""
    image_folder = os.path.join(os.getcwd(), "images")
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    return image_folder


def save_image_from_url(image_url: str, filename: str) -> str:
    """Download and save image from URL to local images folder."""
    try:
        image_folder = ensure_image_folder_exists()
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Save image
        file_path = os.path.join(image_folder, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        return file_path
    except Exception as e:
        print(f"Error saving image: {str(e)}")
        return None


def save_image_from_base64(base64_data: str, filename: str) -> str:
    """Save base64 encoded image to local images folder."""
    try:
        image_folder = ensure_image_folder_exists()
        
        # Remove data URL prefix if present
        if base64_data.startswith('data:image'):
            base64_data = base64_data.split(',')[1]
        
        # Decode and save
        image_data = base64.b64decode(base64_data)
        file_path = os.path.join(image_folder, filename)
        
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        return file_path
    except Exception as e:
        print(f"Error saving base64 image: {str(e)}")
        return None


@tool
def generate_social_media_thumbnail(content: str) -> dict:
    """
    Generates a thumbnail image for social media based on marketing content.

    Args:
        content: The marketing content to visualize as a thumbnail

    Returns:
        A dictionary with image_path, description, and status
    """
    # Create a thumbnail-optimized prompt
    optimized_prompt = thumbnail_prompt(content)
    
    try:
        # Use the correct Gemini image generation model
        image_llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.0-flash-exp-image-generation",
            max_retries=3,
            api_key=os.environ["GEMINI_API_KEY"],
        )

        # Create the message for image generation
        message = {
            "role": "user",
            "content": f"Generate a professional social media thumbnail image: {optimized_prompt}",
        }
        
        # Generate image with proper config
        response = image_llm.invoke(
            [message],
            generation_config=dict(response_modalities=["TEXT", "IMAGE"]),
        )
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        filename = f"thumbnail_{unique_id}.png"
        
        # Extract image from response (following your working Colab code pattern)
        image_path = None
        
        if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 1:
            # Get the image part (usually index 1)
            image_part = response.content[1]
            
            if hasattr(image_part, 'get') and image_part.get("image_url"):
                # Extract base64 data from the image URL
                image_url = image_part.get("image_url").get("url")
                if "," in image_url:
                    image_base64 = image_url.split(",")[-1]
                    image_path = save_image_from_base64(image_base64, filename)
                else:
                    # Direct URL
                    image_path = save_image_from_url(image_url, filename)
            elif isinstance(image_part, dict) and "image_url" in image_part:
                # Alternative structure
                image_url = image_part["image_url"]["url"]
                if "," in image_url:
                    image_base64 = image_url.split(",")[-1]
                    image_path = save_image_from_base64(image_base64, filename)
                else:
                    image_path = save_image_from_url(image_url, filename)
        
        # Return result
        result = {
            'image_path': image_path,
            'description': optimized_prompt,
            'status': 'success' if image_path else 'failed',
            'filename': filename if image_path else None,
            'raw_response': str(type(response.content)) if hasattr(response, 'content') else 'No content'
        }
        
        return result

    except Exception as e:
        print(f"Error in generate_social_media_thumbnail: {str(e)}")
        return {
            'image_path': None,
            'description': f"Error generating thumbnail: {str(e)}",
            'status': 'error',
            'filename': None,
            'raw_response': str(e)
        }