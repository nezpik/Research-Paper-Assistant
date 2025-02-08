import os
import sqlite3
import requests
from flask import Flask, render_template, request, redirect, url_for, g, jsonify, flash
import json
import arxiv
from datetime import datetime
import logging

app = Flask(__name__)
app.secret_key = 'your-secret-key-123'  # Add this line for flash messages
DATABASE = 'papers.db'
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyB-kbXJJ-HDW2jmqNBBz0JRo9nM6qRfbNs")
GEMINI_API_KEY_2 = os.environ.get('GEMINI_API_KEY_2', "AIzaSyC_6ToOp1Q6cEwwrJIhQnTOYmt33FgWITU")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, check_same_thread=False)
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
            db.executescript(f.read())
        db.commit()


@app.route('/')
def index():
    db = get_db()
    cur = db.execute('''
        SELECT id, title, url, authors, source, year, citations, abstract 
        FROM papers 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    papers = cur.fetchall()
    return render_template('index.html', papers=papers)


@app.route('/add', methods=['POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        link = request.form['link']
        section = request.form.get('section', 'Uncategorized')
        db = get_db()
        db.execute('insert into papers (title, link, section) values (?, ?, ?)', [title, link, section])
        db.commit()
        return redirect(url_for('index'))
    return render_template('index.html')


@app.route('/organize', methods=['GET', 'POST'])
def organize():
    predefined_sections = {
        'Literature Review': 'Summarize existing research and identify gaps.',
        'DMAIC': 'Define, Measure, Analyze, Improve, Control - structured problem-solving approach.',
        'Methodology': 'Describe the research methods used.',
        'Results': 'Present the findings of the research.',
        'Discussion': 'Interpret the results and discuss their implications.'
    }
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM papers')
        papers = cursor.fetchall()
        return render_template('organize.html', sections=predefined_sections, papers=papers)
    return render_template('organize.html', sections=predefined_sections)


@app.route('/outline', methods=['POST'])
def outline():
    section = request.form['section']
    methods = {
        'Literature Review': 'Systematic review, Meta-analysis',
        'DMAIC': 'Control charts, Regression analysis',
        'Methodology': 'Surveys, Experiments',
        'Results': 'Statistical analysis, Graphs',
        'Discussion': 'Comparative analysis, Interpretation of statistical significance'
    }
    outline = methods.get(section, 'No specific methods suggested.')
    return render_template('outline.html', section=section, outline=outline)


@app.route('/generate_text', methods=['POST'])
def generate_text():
    try:
        papers = json.loads(request.form.get('papers', '[]'))
        section = request.form.get('section', '')
        methodology = request.form.get('methodology', '')

        if not papers or not section:
            return jsonify({'error': 'Missing required parameters'}), 400

        # Combine information from all selected papers
        combined_info = []
        for paper in papers:
            paper_info = f"Title: {paper['title']}\n"
            paper_info += f"Authors: {paper['authors']}\n"
            paper_info += f"Abstract: {paper['abstract']}\n"
            paper_info += f"Link: {paper['link']}\n"
            combined_info.append(paper_info)

        # Create a prompt based on the section and methodology
        prompt = create_section_prompt(section, methodology, combined_info)
        
        # Generate text using the Gemini API
        response = generate_content(prompt)
        
        if response:
            return jsonify({'text': response})
        else:
            return jsonify({'error': 'Failed to generate text'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_section_prompt(section, methodology, paper_info):
    base_prompt = f"Based on the following research papers, generate content for the {section} section "
    if methodology:
        base_prompt += f"using the {methodology} methodology "
    base_prompt += "of a research paper. The content should be well-structured, academic in tone, "
    base_prompt += "and synthesize information from all provided papers:\n\n"
    
    # Add paper information
    base_prompt += "Research Papers:\n"
    for idx, info in enumerate(paper_info, 1):
        base_prompt += f"\nPaper {idx}:\n{info}\n"

    # Add section-specific instructions
    if section.lower() == 'introduction':
        base_prompt += "\nFor the Introduction section, provide context, state the research problem, and outline objectives."
    elif section.lower() == 'methodology':
        base_prompt += f"\nFor the Methodology section, describe the research approach"
        if methodology:
            base_prompt += f" using the {methodology} framework"
        base_prompt += ", including data collection and analysis methods."
    elif section.lower() == 'results':
        base_prompt += "\nFor the Results section, synthesize and present the key findings from the papers."
    elif section.lower() == 'discussion':
        base_prompt += "\nFor the Discussion section, interpret the results, compare findings, and discuss implications."
    elif section.lower() == 'conclusion':
        base_prompt += "\nFor the Conclusion section, summarize key points and suggest future research directions."

    base_prompt += "\n\nGenerate a cohesive, well-structured paragraph that integrates information from all papers."
    return base_prompt

def generate_content(prompt):
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY_2
    }

    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
        headers=headers,
        json={"contents": [{"parts": [{"text": prompt}]}]}
    )

    if response.status_code == 200:
        try:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
            else:
                return None
        except Exception as e:
            return None
    else:
        return None


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    source = request.args.get('source', 'all').lower()

    if not query:
        return render_template('index.html', papers=[])
    
    papers = []
    
    try:
        logger.info(f"Searching for query: {query}")
        
        # Check if results are cached in the database
        db = get_db()
        cur = db.execute('''
            SELECT title, authors, abstract, url, source, year, citations
            FROM papers
            WHERE query = ?
            AND created_at > datetime('now', '-1 day')
        ''', [query])
        cached_papers = cur.fetchall()
        
        if cached_papers:
            logger.info(f"Found {len(cached_papers)} cached results")
            papers = [dict(row) for row in cached_papers]
            return render_template('index.html', papers=papers, query=query)
        
        if source in ['all', 'arxiv']:
            logger.info("Searching arXiv...")
            # Search arXiv
            search = arxiv.Search(
                query=query,
                max_results=10,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            try:
                for result in search.results():
                    # Convert Author objects to strings
                    author_names = [str(author) for author in result.authors]
                    paper = {
                        'title': result.title,
                        'authors': ', '.join(author_names),
                        'abstract': result.summary,
                        'url': result.pdf_url,
                        'source': 'arXiv',
                        'year': result.published.year if result.published else None,
                        'citations': None
                    }
                    papers.append(paper)
                    logger.info(f"Found paper: {paper['title']}")
            except Exception as e:
                logger.error(f"Error fetching arXiv results: {str(e)}")
                flash("Error fetching results from arXiv. Please try again.")
        
        if not papers:
            flash("No papers found matching your search criteria.")
            return render_template('index.html', papers=[], query=query)
        
        # Store results in database
        db = get_db()
        for paper in papers:
            try:
                db.execute('''
                    INSERT OR REPLACE INTO papers 
                    (title, authors, abstract, url, source, year, citations, created_at, query)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    paper['title'],
                    paper['authors'],
                    paper['abstract'],
                    paper['url'],
                    paper['source'],
                    paper['year'],
                    paper['citations'],
                    datetime.now().isoformat(),
                    query
                ))
            except sqlite3.Error as e:
                logger.error(f"Database error: {str(e)}")
        db.commit()
        
        logger.info(f"Returning {len(papers)} papers")
        return render_template('index.html', papers=papers, query=query)

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        flash(f'An error occurred while searching: {str(e)}')
        return render_template('index.html', papers=[], query=query)


@app.route('/add_paper', methods=['POST'])
def add_paper():
    title = request.form.get('title')
    link = request.form.get('link')
    source = request.form.get('source')
    gemini_response = requests.post(
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro:generateContent',
        headers={'Content-Type': 'application/json'},
        params={'key': GEMINI_API_KEY},
        json={
            'contents': [{'parts': [{'text': f'Summarize the paper: {title}.\n Source: {source}.\n Link: {link}.\n Focus on the research context and main findings.'}]}]
        }
    )
    if gemini_response.status_code == 200:
        summary = gemini_response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No summary available')
    else:
        summary = f"Summary generation failed. Status Code: {gemini_response.status_code}, Response: {gemini_response.text}"

    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO papers (title, link, summary, source, section) VALUES (?, ?, ?, ?, ?)",
                   (title, link, summary, source, ""))
    db.commit()
    return redirect(url_for('index'))


@app.route('/generate_outline', methods=['GET'])
def generate_outline():
    section = request.args.get('section', '')
    outline = ""
    if section:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT title FROM papers WHERE section = ?", (section,))
        papers = [row[0] for row in cursor.fetchall()]
        if papers:
            outline = f"Outline for {section}:\n"
            outline += "Introduction: Briefly introduce the topic and the importance of the research.\n"
            outline += "Literature Review: Discuss the key papers in the field, including:\n" + "\n".join([f"- {paper}" for paper in papers]) + "\n"
            outline += "Methodology: Describe the research methods used in the papers.\n"
            outline += "Results: Summarize the main findings of the papers.\n"
            outline += "Discussion: Discuss the implications of the findings and identify areas for future research.\n"
            outline += "Conclusion: Summarize the main points of the outline and provide a concluding statement.\n"
    return render_template('outline.html', section=section, outline=outline)


@app.route('/generate_abstract', methods=['POST'])
def generate_abstract():
    content = request.form['content']
    
    prompt = {
        "contents": [{
            "parts": [{
                "text": f"""You are a PhD in software engineering and research methodology. 
                Based on the following research paper content: {content}
                
                Generate a concise and comprehensive abstract that summarizes the key points from all sections.
                The abstract should be academic in tone and follow standard research paper abstract conventions.
                Include the research objective, methodology, key findings, and implications."""
            }]
        }]
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY_2
    }

    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
        headers=headers,
        json=prompt
    )

    if response.status_code == 200:
        try:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                return jsonify({'text': text})
            else:
                return jsonify({'text': 'Error: No content generated'}), 500
        except Exception as e:
            return jsonify({'text': f'Error parsing response: {str(e)}'}), 500
    else:
        error_message = f'Error {response.status_code}: {response.text}'
        return jsonify({'text': error_message}), response.status_code


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

def generate_section_content(section, papers):
    """Generate appropriate content based on section type."""
    if section == "Introduction":
        return generate_introduction(papers)
    elif section == "Literature Review":
        return generate_literature_review(papers)
    elif section == "Methodology":
        return generate_methodology(papers)
    elif section == "Results":
        return generate_results(papers)
    elif section == "Discussion":
        return generate_discussion(papers)
    elif section == "Conclusion":
        return generate_conclusion(papers)
    else:
        return generate_default_section(section, papers)

def generate_literature_review(papers):
    """Generate a literature review section from the selected papers."""
    content = []
    themes = group_papers_by_theme(papers)
    
    for theme, theme_papers in themes.items():
        content.append(f"<h3>{theme}</h3>")
        content.append("<p>")
        
        # Generate overview of the theme
        content.append(f"Several researchers have investigated {theme.lower()}. ")
        
        # Add paper discussions
        for i, paper in enumerate(theme_papers):
            authors = get_author_last_names(paper['authors'])
            year = extract_year(paper['url']) or "n.d."
            
            if i == 0:
                content.append(f"{authors} ({year}) ")
            elif i == len(theme_papers) - 1:
                content.append(f"and {authors} ({year}) ")
            else:
                content.append(f"{authors} ({year}), ")
            
            # Add brief description of the paper's contribution
            abstract_summary = summarize_abstract(paper['abstract'])
            content.append(f"{abstract_summary}. ")
        
        content.append("</p>")
    
    return "\n".join(content)

def generate_introduction(papers):
    """Generate an introduction section."""
    content = ["<p>"]
    content.append("This research explores several key aspects of the field. ")
    
    # Add background from papers
    for paper in papers:
        authors = get_author_last_names(paper['authors'])
        year = extract_year(paper['url']) or "n.d."
        content.append(f"As demonstrated by {authors} ({year}), {summarize_abstract(paper['abstract'])}. ")
    
    content.append("</p>")
    return "\n".join(content)

def generate_methodology(papers):
    """Generate a methodology section."""
    content = ["<p>"]
    content.append("This research builds upon established methodological approaches in the field. ")
    
    for paper in papers:
        authors = get_author_last_names(paper['authors'])
        year = extract_year(paper['url']) or "n.d."
        content.append(f"Following the approach of {authors} ({year}), {extract_methodology(paper['abstract'])}. ")
    
    content.append("</p>")
    return "\n".join(content)

def generate_default_section(section, papers):
    """Generate default content for any section."""
    content = []
    
    for paper in papers:
        content.append(f"<h3>{paper['title']}</h3>")
        if paper['authors']:
            content.append(f"<p class='authors'>{paper['authors']}</p>")
        if paper['abstract']:
            content.append(f"<p>{paper['abstract']}</p>")
        if paper['url']:
            content.append(f"<p><a href='{paper['url']}' target='_blank'>Read Paper</a></p>")
        content.append("<hr>")
    
    return "\n".join(content)

def group_papers_by_theme(papers):
    """Group papers by common themes based on their abstracts."""
    themes = {
        "Theoretical Foundations": [],
        "Empirical Studies": [],
        "Methodological Approaches": [],
        "Applications and Implementations": []
    }
    
    for paper in papers:
        # Simple classification based on abstract keywords
        abstract = paper['abstract'].lower()
        if any(word in abstract for word in ['theory', 'framework', 'model', 'concept']):
            themes["Theoretical Foundations"].append(paper)
        elif any(word in abstract for word in ['study', 'survey', 'analysis', 'data']):
            themes["Empirical Studies"].append(paper)
        elif any(word in abstract for word in ['method', 'technique', 'approach', 'procedure']):
            themes["Methodological Approaches"].append(paper)
        else:
            themes["Applications and Implementations"].append(paper)
    
    # Remove empty themes
    return {k: v for k, v in themes.items() if v}

def get_author_last_names(authors_str):
    """Extract last names from authors string."""
    if not authors_str:
        return "Unknown Author"
    
    authors = authors_str.split(',')[0]  # Take first author if multiple
    names = authors.strip().split()
    return names[-1] if names else "Unknown"

def extract_year(url):
    """Extract year from paper URL or return None."""
    # Try to find a year pattern in the URL
    import re
    year_match = re.search(r'20\d{2}|19\d{2}', url)
    return year_match.group(0) if year_match else None

def format_reference(title, authors, year, url):
    """Format reference in APA style."""
    return f"{authors} ({year}). {title}. Retrieved from {url}"

def summarize_abstract(abstract):
    """Create a brief summary of the abstract."""
    if not abstract:
        return "contributed to the field"
    
    # Take first sentence or first 100 characters
    sentences = abstract.split('.')
    summary = sentences[0] if sentences else abstract[:100]
    return summary.strip()

def extract_methodology(abstract):
    """Extract methodology-related information from abstract."""
    if not abstract:
        return "used standard methodological approaches"
    
    # Look for methodology-related sentences
    sentences = abstract.split('.')
    for sentence in sentences:
        if any(word in sentence.lower() for word in ['method', 'approach', 'technique', 'procedure', 'analysis']):
            return sentence.strip()
    
    return "employed various research methods"

def generate_results(papers):
    """Generate a results section."""
    content = ["<p>"]
    content.append("This research presents several key findings. ")
    
    # Add results from papers
    for paper in papers:
        authors = get_author_last_names(paper['authors'])
        year = extract_year(paper['url']) or "n.d."
        content.append(f"As demonstrated by {authors} ({year}), {summarize_abstract(paper['abstract'])}. ")
    
    content.append("</p>")
    return "\n".join(content)

def generate_discussion(papers):
    """Generate a discussion section."""
    content = ["<p>"]
    content.append("This research has several implications. ")
    
    # Add discussion from papers
    for paper in papers:
        authors = get_author_last_names(paper['authors'])
        year = extract_year(paper['url']) or "n.d."
        content.append(f"As discussed by {authors} ({year}), {summarize_abstract(paper['abstract'])}. ")
    
    content.append("</p>")
    return "\n".join(content)

def generate_conclusion(papers):
    """Generate a conclusion section."""
    content = ["<p>"]
    content.append("In conclusion, this research has several key takeaways. ")
    
    # Add conclusion from papers
    for paper in papers:
        authors = get_author_last_names(paper['authors'])
        year = extract_year(paper['url']) or "n.d."
        content.append(f"As concluded by {authors} ({year}), {summarize_abstract(paper['abstract'])}. ")
    
    content.append("</p>")
    return "\n".join(content)


if __name__ == '__main__':
    init_db()
    # Use environment variables for configuration
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host=host, port=port, debug=debug)
