
```markdown
# PDF Information Extractor

A modern web application that extracts key information from PDF resumes and documents. The application uses AI-powered Named Entity Recognition (NER) and pattern matching to identify and extract names.

## Features

- 📄 PDF file upload and processing
- 🤖 AI-powered information extraction using Hungarian NER model
- 🌍 International phone number support
- 📱 Responsive modern UI
- 🎯 Confidence scoring for extracted information
- 🔍 Detailed information display with formatting

## Project Structure


.
├── .streamlit/        # Streamlit configuration
└── backend/           # Python PDF processing module
    └── ai_pdf_parser.py  # Core PDF parsing logic


## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <project-directory>


2. **Install Python Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
  

3. **Start the Streamlit App**
   ```bash
   streamlit run backend/ai_pdf_parser.py
  

4. **Access the Application**
   - Open your browser and navigate to the URL provided by Streamlit
   - The application should now be running and ready to use

## Usage

1. Click the "Choose File" button to select a PDF file
2. The application will automatically process the file
3. View extracted information in the respective tabs:
   - Name
   - Phone Number
   - Address
   - Role
4. Each field shows a confidence score indicating the reliability of the extraction

## Technical Details

### PDF Processing
- Uses Python with spaCy for NLP
- Multiple PDF text extraction methods (PDFPlumber, PyPDF2)
- Pattern matching with regular expressions
- Named Entity Recognition (NER)

## Troubleshooting

If you encounter any issues:

1. Ensure all dependencies are correctly installed
2. Check if Python versions meet the requirements
3. Verify that the necessary models are properly downloaded

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
```


