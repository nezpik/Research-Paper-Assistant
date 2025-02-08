import os
import sqlite3
import requests
from flask import Flask, render_template, request, redirect, url_for, g, jsonify, flash
import json
import arxiv
from datetime import datetime
import logging
from deepseek import DeepSeekAPI

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-dev-key')  # Change this in production
DATABASE = 'papers.db'

# Initialize DeepSeek API
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

if not DEEPSEEK_API_KEY:
    logger.warning("DeepSeek API key not found in environment variables. Some features may not work.")

deepseek_client = DeepSeekAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.executescript(f.read().decode('utf8'))

@app.route('/')
def index():
    return render_template('index.html')

def generate_text(prompt, max_tokens=1000):
    """Generate text using DeepSeek API"""
    try:
        response = deepseek_client.chat_completion(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response
    except Exception as e:
        logger.error(f"Error generating text with DeepSeek: {str(e)}")
        return None

def create_section_prompt(section, methodology, paper_info):
    """Create a prompt for generating section content"""
    base_prompt = f"Write a {section} section for a research paper. "
    
    if section == "Literature Review":
        base_prompt += "Analyze and synthesize the following papers, grouping them by themes and highlighting key findings: "
    elif section == "Methodology":
        base_prompt += f"Describe the following methodology: {methodology}. "
    
    base_prompt += "Here are the relevant papers:\n\n"
    
    for paper in paper_info:
        base_prompt += f"Title: {paper['title']}\n"
        base_prompt += f"Authors: {paper['authors']}\n"
        base_prompt += f"Abstract: {paper['abstract']}\n\n"
    
    base_prompt += f"\nWrite a coherent {section} that incorporates these papers appropriately."
    return base_prompt

def generate_content(prompt):
    """Generate content using DeepSeek API with proper formatting"""
    try:
        content = generate_text(prompt)
        if content:
            # Format the content with proper academic styling
            formatted_content = content.replace('\n', '<br>')
            return formatted_content
        return "Error generating content. Please try again."
    except Exception as e:
        logger.error(f"Error in generate_content: {str(e)}")
        return "Error generating content. Please try again."

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('query', '')
        if not query:
            flash('Please enter a search query')
            return redirect(url_for('index'))

        try:
            # Search in database first
            db = get_db()
            cached_results = db.execute(
                'SELECT * FROM papers WHERE query = ?',
                (query,)
            ).fetchall()

            if cached_results:
                results = []
                for row in cached_results:
                    results.append({
                        'title': row['title'],
                        'authors': row['authors'],
                        'abstract': row['abstract'],
                        'url': row['url']
                    })
                return jsonify({'results': results})

            # If not in database, search arXiv
            search = arxiv.Search(
                query=query,
                max_results=10,
                sort_by=arxiv.SortCriterion.Relevance
            )

            results = []
            for paper in search.results():
                paper_data = {
                    'title': paper.title,
                    'authors': ', '.join([author.name for author in paper.authors]),
                    'abstract': paper.summary,
                    'url': paper.pdf_url
                }
                results.append(paper_data)

                # Cache the results
                try:
                    db.execute('''
                        INSERT INTO papers (title, authors, abstract, url, query, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        paper_data['title'],
                        paper_data['authors'],
                        paper_data['abstract'],
                        paper_data['url'],
                        query,
                        datetime.now().isoformat()
                    ))
                except sqlite3.Error as e:
                    logger.error(f"Database error while caching paper: {str(e)}")

            db.commit()
            return jsonify({'results': results})

        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return redirect(url_for('index'))

@app.route('/add_selected_papers', methods=['POST'])
def add_selected_papers():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
            
        selected_papers = data.get('papers', [])
        section = data.get('section', '')
        
        if not selected_papers:
            return jsonify({'error': 'No papers selected'}), 400
        
        if not section:
            return jsonify({'error': 'No section specified'}), 400
        
        # Generate content based on section type
        content = generate_section_content(section, selected_papers)
        
        # Store papers in database with section
        db = get_db()
        references = []
        for paper in selected_papers:
            try:
                db.execute('''
                    INSERT OR REPLACE INTO papers 
                    (title, authors, abstract, url, section, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    paper['title'],
                    paper['authors'],
                    paper['abstract'],
                    paper['url'],
                    section,
                    datetime.now().isoformat()
                ))
                
                # Generate reference in APA format
                year = extract_year(paper['url']) or "n.d."
                reference = format_reference(paper['title'], paper['authors'], year, paper['url'])
                references.append(reference)
                
            except sqlite3.Error as e:
                logger.error(f"Database error while adding paper: {str(e)}")
                return jsonify({'error': f'Database error: {str(e)}'}), 500
                
        db.commit()
        
        return jsonify({
            'success': True,
            'content': content,
            'references': references
        })
        
    except Exception as e:
        logger.error(f"Error adding selected papers: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Include all the helper functions from the original app.py
# (generate_section_content, generate_literature_review, etc.)

if __name__ == '__main__':
    init_db()
    # Use environment variables for configuration
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host=host, port=port, debug=debug)
