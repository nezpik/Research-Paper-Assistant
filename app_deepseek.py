import os
import sqlite3
import requests
from flask import Flask, render_template, request, redirect, url_for, g, jsonify, flash, session
import json
import arxiv
from datetime import datetime
import logging

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-dev-key')  # Change this in production
DATABASE = 'papers.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/')
def index():
    return render_template('index.html')

def deepseek_generate(prompt):
    try:
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            logger.error("DEEPSEEK_API_KEY not found in environment variables")
            return None

        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a research paper writing assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            logger.error("Unexpected response format from DeepSeek API")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling DeepSeek API: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error in deepseek_generate: {str(e)}")
        return None

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    logger.info(f"Search query received: '{query}'")
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
            return render_template('search_results.html', papers=results, query=query)

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
        return render_template('search_results.html', papers=results, query=query)

    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('index'))

@app.route('/add_selected_papers', methods=['POST'])
def add_selected_papers():
    try:
        data = request.get_json()
        if not data or 'papers' not in data or 'section' not in data:
            return jsonify({'success': False, 'error': 'Invalid request data'})

        papers = data['papers']
        section = data['section']

        # Store selected papers in session
        if 'selected_papers' not in session:
            session['selected_papers'] = {}
        
        if section not in session['selected_papers']:
            session['selected_papers'][section] = []
        
        session['selected_papers'][section].extend(papers)
        session.modified = True

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error adding selected papers: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate_section', methods=['POST'])
def generate_section():
    try:
        data = request.get_json()
        if not data or 'section' not in data:
            return jsonify({'success': False, 'error': 'Invalid request data'})

        section = data['section']
        if 'selected_papers' not in session or section not in session['selected_papers']:
            return jsonify({'success': False, 'error': 'No papers selected for this section'})

        papers = session['selected_papers'][section]
        
        # Prepare the prompt for DeepSeek
        prompt = f"Based on the following papers, generate a {section} section for a research paper. Make it comprehensive and well-structured:\n\n"
        for paper in papers:
            prompt += f"Title: {paper['title']}\n"
            prompt += f"Authors: {paper['authors']}\n"
            prompt += f"Abstract: {paper['abstract']}\n\n"

        # Call DeepSeek API to generate the section
        generated_text = deepseek_generate(prompt)
        
        if generated_text is None:
            return jsonify({'success': False, 'error': 'Failed to generate text'})

        # Store the generated text in the session
        if 'generated_sections' not in session:
            session['generated_sections'] = {}
        session['generated_sections'][section] = generated_text
        session.modified = True

        return jsonify({
            'success': True, 
            'generated_text': generated_text,
            'message': f'{section} section generated successfully'
        })

    except Exception as e:
        logger.error(f"Error generating section: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    init_db()
    # Use environment variables for configuration
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host=host, port=port, debug=debug)
