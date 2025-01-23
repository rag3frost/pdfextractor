import streamlit as st
from backend.ai_pdf_parser import AIPDFParser
import os
import tempfile

st.set_page_config(
    page_title="PDF Information Extractor",
    page_icon="📄",
    layout="wide"
)

st.title("PDF Information Extractor")
st.markdown("""
This app extracts key information from PDF resumes and documents using AI-powered Named Entity Recognition.
""")

# File upload
uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])

if uploaded_file is not None:
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    try:
        with st.spinner('Extracting information...'):
            # Process the PDF
            parser = AIPDFParser(tmp_file_path)
            info = parser.extract_information()

            # Display results in columns
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Extracted Information")
                if info['name']:
                    st.write("**Name:**", info['name'])
                if info['phone']:
                    st.write("**Phone:**", info['phone'])
                if info['address']:
                    st.write("**Address:**", info['address'])
                if info['role']:
                    st.write("**Role:**", info['role'])

            with col2:
                st.subheader("Confidence Scores")
                for field, score in info['confidence'].items():
                    st.progress(score, text=f"{field.title()}: {score:.2%}")

    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")

    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

# Add footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit and Hugging Face Transformers") 