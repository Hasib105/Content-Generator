import os
import streamlit as st
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from google.ai.generativelanguage_v1beta.types import Tool as GenAITool

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
        [HumanMessage(content=content)],  # Wrap the string content in HumanMessage
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
                # Get search results
                search_result = google_search(content)
                
                # Create prompt with system and human messages
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


@tool
def generate_social_media_thumbnail(content: str) -> str:
    """
    Generates a thumbnail image and description for social media based on marketing content.
    Saves image locally and returns the local path.
    """
    optimized_prompt = thumbnail_prompt(content)

    try:
        image_llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.0-flash-exp-image-generation",
            max_retries=3,
            api_key=os.environ["GEMINI_API_KEY"],
        )

        message = {
            "role": "user",
            "content": optimized_prompt,
        }

        response = image_llm.invoke(
            [message],
            generation_config=dict(response_modalities=["TEXT", "IMAGE"]),
        )

        # Simulated: replace with your actual image output method
        image_data = getattr(response, "image_bytes", None)
        description = getattr(response, "content", "")

        if image_data:
            # Save image
            image_folder = ensure_image_folder_exists()
            filename = f"thumbnail_{hash(content) % 100000}.png"
            image_path = os.path.join(image_folder, filename)

            with open(image_path, "wb") as f:
                f.write(image_data)

            markdown = f"## Thumbnail Design\n![Generated Thumbnail]({image_path})\n\n{description}\n\n"
            markdown += f"*Based on content topic: \"{content[:50]}...\"*"

            return image_path  # Return local image path for Streamlit display

        return "Thumbnail generation failed: No image returned."

    except Exception as e:
        print(f"Error in generate_social_media_thumbnail: {str(e)}")
        return f"Error generating thumbnail: {str(e)}"