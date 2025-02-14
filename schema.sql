DROP TABLE IF EXISTS papers;
DROP TABLE IF EXISTS sections;

CREATE TABLE papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    abstract TEXT,
    url TEXT,
    query TEXT,
    section TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Insert some sample data
INSERT INTO papers (title, authors, abstract, url, query, created_at) VALUES
('An Introduction to Machine Learning', 'John Smith, Jane Doe', 'This paper provides a comprehensive introduction to machine learning concepts.', 'https://example.com/ml-intro', '', datetime('now')),
('Deep Learning Fundamentals', 'Alice Johnson', 'A detailed overview of deep learning principles and architectures.', 'https://example.com/dl-fundamentals', '', datetime('now')),
('Neural Networks in Practice', 'Bob Wilson, Carol Brown', 'Practical applications of neural networks in real-world scenarios.', 'https://example.com/nn-practice', '', datetime('now'));
