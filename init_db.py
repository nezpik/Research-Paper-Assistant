import sqlite3
import os

def init_test_db():
    # Remove existing database if it exists
    if os.path.exists('papers.db'):
        os.remove('papers.db')
    
    # Create new database
    conn = sqlite3.connect('papers.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT,
        authors TEXT,
        source TEXT,
        year INTEGER,
        citations INTEGER DEFAULT 0,
        abstract TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Insert test data
    test_papers = [
        (
            'Attention Is All You Need',
            'https://arxiv.org/abs/1706.03762',
            'Ashish Vaswani, Noam Shazeer, Niki Parmar',
            'arxiv',
            2017,
            123456,
            'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...'
        ),
        (
            'BERT: Pre-training of Deep Bidirectional Transformers',
            'https://arxiv.org/abs/1810.04805',
            'Jacob Devlin, Ming-Wei Chang, Kenton Lee',
            'arxiv',
            2018,
            98765,
            'We introduce a new language representation model called BERT...'
        ),
        (
            'Deep Learning in Neural Networks',
            'https://scholar.google.com/paper1',
            'John Smith, Jane Doe',
            'scholar',
            2020,
            5432,
            'This paper explores recent advances in deep learning...'
        ),
        (
            'Machine Learning Fundamentals',
            'https://ieee.org/paper2',
            'Robert Johnson, Emily Brown',
            'ieee',
            2021,
            3210,
            'A comprehensive review of machine learning principles...'
        ),
        (
            'Advanced Neural Networks',
            'https://acm.org/paper3',
            'Michael Wilson, Sarah Davis',
            'acm',
            2022,
            1234,
            'This study presents new techniques in neural network architecture...'
        )
    ]
    
    cursor.executemany('''
    INSERT INTO papers (title, url, authors, source, year, citations, abstract)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', test_papers)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database initialized with test data!")

if __name__ == '__main__':
    init_test_db()
