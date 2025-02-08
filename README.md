# Pistology-RA0

A powerful research assistant that helps researchers organize and create professional research papers. This tool assists in searching academic papers, generating literature reviews, and organizing research content in a structured format.

## Features

- 🔍 **Smart Paper Search**: Search and fetch academic papers from various sources
- 📚 **Automatic Literature Review**: Generate structured literature reviews based on selected papers
- 📝 **Section Management**: Organize papers into different sections (Introduction, Literature Review, Methodology, etc.)
- 🎨 **Professional Formatting**: Output your research in a professionally formatted academic style
- 📊 **Theme Analysis**: Automatically group papers by themes for better organization
- 📑 **Reference Management**: Automatic APA-style reference generation

## Installation Guide

### Prerequisites

1. **Python**: Make sure you have Python 3.8 or higher installed
   ```bash
   python --version
   ```
   If not installed, download it from [Python's official website](https://www.python.org/downloads/)

2. **Git**: Required to clone the repository
   ```bash
   git --version
   ```
   If not installed, download it from [Git's official website](https://git-scm.com/downloads)

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/nezpik/Pistology-RA0.git
   cd Pistology-RA0
   ```

2. **Create a Virtual Environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/MacOS
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Choose Your AI Backend**
   This application supports two AI backends:
   
   a) **Google Gemini (Default)**
   - Get your API keys from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Use `app.py`
   - Configure in `.env`:
     ```bash
     GEMINI_API_KEY=your-gemini-api-key
     GEMINI_API_KEY_2=your-gemini-api-key-2
     ```

   b) **DeepSeek V3**
   - Get your API key from [DeepSeek Platform](https://platform.deepseek.com/api_keys)
   - Use `app_deepseek.py`
   - Configure in `.env`:
     ```bash
     DEEPSEEK_API_KEY=your-deepseek-api-key
     ```

5. **Set Up Environment Variables**
   Create a new file named `.env` in the project root directory with the following content:
   ```bash
   # Required for session management
   SECRET_KEY=your-secret-key-here

   # Database configuration
   DATABASE=papers.db

   # Choose ONE of these API configurations:
   
   # Option 1: Gemini API Keys (for app.py)
   GEMINI_API_KEY=your-gemini-api-key
   GEMINI_API_KEY_2=your-gemini-api-key-2
   
   # Option 2: DeepSeek API Key (for app_deepseek.py)
   DEEPSEEK_API_KEY=your-deepseek-api-key
   ```

   **Important**: Never commit your `.env` file to version control. The `.env` file is listed in `.gitignore` to prevent accidental commits.

6. **Initialize the Database**
   ```bash
   python init_db.py
   ```

### Running the Application

1. **Start the Server**
   
   For Gemini version (default):
   ```bash
   python app.py
   ```
   
   For DeepSeek version:
   ```bash
   python app_deepseek.py
   ```

2. **Access the Application**
   Open your web browser and go to:
   ```
   http://localhost:5000
   ```

## Usage Guide

### 1. Searching for Papers
- Enter your search query in the search bar
- Click "Search" to fetch relevant papers
- Results will show paper titles, authors, and abstracts

### 2. Adding Papers to Your Research
- Select papers by clicking the checkboxes
- Choose a section (e.g., Literature Review, Methodology)
- Click "Add to Paper" to include them in your research

### 3. Generating Literature Reviews
- Select relevant papers
- Choose "Literature Review" as the section
- The system will automatically:
  - Group papers by themes
  - Generate coherent summaries
  - Create proper citations
  - Format the content professionally

### 4. Managing Your Paper
- Edit the title, authors, and abstract
- Organize content into sections
- Review and edit generated content
- Add or remove papers as needed

### 5. References
- References are automatically generated in APA format
- Each added paper is properly cited in the text
- A complete reference list is maintained

## Troubleshooting

### Common Issues

1. **Database Errors**
   ```bash
   # Reset the database
   rm papers.db
   python init_db.py
   ```

2. **Missing API Keys**
   - Verify your `.env` file contains valid API keys
   - Check the respective API dashboard for key status
   - For Gemini: Visit Google AI Studio
   - For DeepSeek: Visit DeepSeek Platform

3. **Dependencies Issues**
   ```bash
   # Reinstall dependencies
   pip uninstall -r requirements.txt -y
   pip install -r requirements.txt
   ```

### Getting Help

If you encounter any issues:
1. Check the logs in the terminal
2. Verify all environment variables are set correctly
3. Ensure you're using a supported Python version
4. Create an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - Your Python version
   - Your operating system
   - Which AI backend you're using (Gemini or DeepSeek)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
