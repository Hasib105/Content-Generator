import streamlit as st
from PIL import Image
import os
import base64
from io import BytesIO

# Import the tools and LLM setup
from llm import chat_with_tools, structured_llm
from tools import generate_content_with_search, generate_seo_hashtags, generate_social_media_thumbnail

# Page setup
st.set_page_config(page_title="Content Generator AI", layout="wide")
st.title("🚀 AI Content Generator")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "generated_content" not in st.session_state:
    st.session_state.generated_content = None
if "selected_tool" not in st.session_state:
    st.session_state.selected_tool = "generate_content"

# Sidebar for tool selection and options
st.sidebar.header("Content Generation Options")
tool_options = {
    "generate_content": "Generate Content with Search",
    "generate_complete_package": "Complete Package (Content + Hashtags + Thumbnail)"
}
selected_tool = st.sidebar.radio("Select Tool", options=list(tool_options.keys()), 
                                format_func=lambda x: tool_options[x])
st.session_state.selected_tool = selected_tool

# Word count slider for content generation
word_count = st.sidebar.slider("Word Count", min_value=100, max_value=1000, value=300, step=50)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Content Generator")
    content_topic = st.text_area("Enter your topic or keyword", height=100)
    
    generate_button = st.button("Generate Content", type="primary")
    
    if generate_button and content_topic:
        with st.spinner("Generating content..."):
            try:
                if st.session_state.selected_tool == "generate_content":
                    # Just generate content with search
                    content = generate_content_with_search.invoke(
                        {"content": content_topic, "word_count": word_count}
                    )
                    st.session_state.generated_content = {
                        "title": f"Content about: {content_topic}",
                        "content": content,
                        "hashtags": [],
                        "thumbnail": None  # Changed from thumbnail_url to thumbnail
                    }
                else:
                    # Generate complete package with structured output
                    st.info("Generating content...")
                    content = generate_content_with_search.invoke(
                        {"content": content_topic, "word_count": word_count}
                    )
                    
                    st.info("Generating hashtags...")
                    hashtags = generate_seo_hashtags.invoke({"content": content})
                    
                    st.info("Generating thumbnail...")
                    thumbnail_data = generate_social_media_thumbnail.invoke({"content": content})
                    
                    # Store the complete package
                    st.session_state.generated_content = {
                        "title": f"Content about: {content_topic}",
                        "content": content,
                        "hashtags": hashtags,
                        "thumbnail": thumbnail_data  # Changed from thumbnail_url to thumbnail
                    }
                    
                # Add to chat history
                st.session_state.messages.append({"role": "user", "content": f"Generate content about: {content_topic}"})
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"✅ Generated content about '{content_topic}'. See the results tab."
                })
                
            except Exception as e:
                st.error(f"Error generating content: {str(e)}")
    
    # Display chat history
    st.subheader("Generation History")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

with col2:
    st.subheader("Generated Results")
    
    if st.session_state.generated_content:
        content_data = st.session_state.generated_content
        
        # Display the title
        st.markdown(f"## {content_data['title']}")
        
        # Tabs for different content components
        content_tab, hashtags_tab, thumbnail_tab = st.tabs(["Content", "Hashtags", "Thumbnail"])
        
        with content_tab:
            st.markdown(content_data["content"])
            copy_content = st.button("Copy Content")
            if copy_content:
                st.toast("Content copied to clipboard!")
        
        with hashtags_tab:
            if content_data["hashtags"]:
                hashtags_text = " ".join(content_data["hashtags"])
                st.markdown(hashtags_text)
                copy_hashtags = st.button("Copy Hashtags")
                if copy_hashtags:
                    st.toast("Hashtags copied to clipboard!")
            else:
                st.info("No hashtags generated. Select 'Complete Package' to generate hashtags.")
        
        with thumbnail_tab:
            thumbnail_data = content_data.get("thumbnail")
            
            if thumbnail_data and isinstance(thumbnail_data, dict):
                if thumbnail_data.get("status") == "success" and thumbnail_data.get("image_path"):
                    try:
                        # Check if file exists
                        if os.path.exists(thumbnail_data["image_path"]):
                            # Display the image
                            st.image(thumbnail_data["image_path"], caption="Generated Thumbnail", use_container_width=True)
                            st.success(f"✅ Thumbnail saved as: {thumbnail_data['filename']}")
                            
                            # Download button
                            with open(thumbnail_data["image_path"], "rb") as file:
                                st.download_button(
                                    label="📥 Download Thumbnail",
                                    data=file.read(),
                                    file_name=thumbnail_data["filename"],
                                    mime="image/png"
                                )
                        else:
                            st.error(f"Image file not found at: {thumbnail_data['image_path']}")
                            
                    except Exception as e:
                        st.error(f"Error displaying thumbnail: {str(e)}")
                        
                elif thumbnail_data.get("status") == "error":
                    st.error("Failed to generate thumbnail")
                    st.error(f"Error: {thumbnail_data.get('description', 'Unknown error')}")
                    
                else:
                    st.warning("Thumbnail generation incomplete")
                        
            else:
                st.info("No thumbnail generated. Select 'Complete Package' to generate a thumbnail.")
                
    else:
        st.info("Enter a topic and click 'Generate Content' to see results here.")

# Footer
st.markdown("---")
st.caption("Powered by Google Gemini and LangChain")