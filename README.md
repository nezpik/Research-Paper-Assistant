# Research Paper Assistant

A web application that helps researchers organize and create research papers by searching and managing academic papers.

## Features

- Search for academic papers from various sources
- Organize papers into research sections
- Automatically generate literature reviews
- Create properly formatted research papers
- Reference management in APA style

## Deployment Instructions

### Local Development

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run the application:
```bash
python app.py
```

### Deploy to PythonAnywhere

1. Create a free account at [PythonAnywhere](https://www.pythonanywhere.com)

2. Once logged in:
   - Go to the "Files" tab
   - Upload all project files
   - Create a new virtual environment
   - Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the web app:
   - Go to the "Web" tab
   - Click "Add a new web app"
   - Choose "Flask" as your framework
   - Set the working directory to your project folder
   - Set FLASK_APP environment variable to "app.py"

4. Configure WSGI file:
   ```python
   import sys
   path = '/home/YOUR_USERNAME/Research-Paper-Assistant'
   if path not in sys.path:
       sys.path.append(path)
   
   from app import app as application
   ```

5. Reload the web app

Your application will be available at: `https://YOUR_USERNAME.pythonanywhere.com`

## Environment Variables

Create a `.env` file with the following variables:
```
SECRET_KEY=your_secret_key
DATABASE=papers.db
```

## Database Setup

The application will automatically create the SQLite database on first run.

## Usage

1. Search for papers using the search bar
2. Select papers you want to include
3. Choose a section (Introduction, Literature Review, etc.)
4. Click "Add to Paper" to add the selected papers
5. Edit paper title, authors, and abstract as needed
6. Download the final paper when ready
