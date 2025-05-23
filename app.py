import streamlit as st

if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

st.set_page_config(page_title="LLM Chatbot with Uploads", layout="wide")
st.title("🧊 Ai Content Generator")


st.sidebar.header("Upload Files")
uploaded_file = st.sidebar.file_uploader("Upload an image or document", type=["png", "jpg", "jpeg", "pdf", "txt", "docx"], accept_multiple_files=False)

if uploaded_file is not None:
    st.session_state.uploaded_files.append(uploaded_file)
    st.sidebar.success(f"Uploaded: {uploaded_file.name}")


if st.session_state.uploaded_files:
    st.sidebar.subheader("Uploaded Files")
    for f in st.session_state.uploaded_files:
        st.sidebar.write(f.name)


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("How can I help you today?"):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    def generate_answer(user_input, files):
        response = f"Received your message: '{user_input}'. You uploaded {len(files)} file(s)."
        return response

    response = generate_answer(prompt, st.session_state.uploaded_files)
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
