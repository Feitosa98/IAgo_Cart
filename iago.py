import sqlite3
import re
import os
from datetime import datetime

IA_DB_PATH = "ia.db"

def get_ia_conn():
    conn = sqlite3.connect(IA_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_ia_db():
    conn = get_ia_conn()
    cur = conn.cursor()
    # Patterns table: Stores regexes learned for specific fields
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patterns (
            id INTEGER PRIMARY KEY,
            field_name TEXT NOT NULL,
            regex_pattern TEXT NOT NULL,
            example_match TEXT,
            weight INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def clean_text_for_regex(text):
    """Escapes regex special characters."""
    return re.escape(text)

def generate_context_regex(full_text, value, context_words=3):
    """
    Finds 'value' in 'full_text' and generates a regex based on preceding words.
    Example: "Matrícula número 12345" -> value="12345"
    Context: "Matrícula número"
    Regex: r"Matrícula\s+número\s+(\d+)"
    """
    if not value or len(value) < 2:
        return None
        
    # Normalize
    value_clean = value.strip()
    
    # Locate value in text
    # We use re.escape to find the exact string
    escaped_value = re.escape(value_clean)
    
    # Try to find match
    matches = list(re.finditer(escaped_value, full_text))
    if not matches:
        return None
        
    # Pick the first match for simplicity (or simplistic approach)
    match = matches[0]
    start, end = match.span()
    
    # Get context (preceding text)
    # Go back N characters looking for words
    preceding_chunk = full_text[max(0, start-50):start]
    
    # Split into words/tokens
    tokens = preceding_chunk.split()
    if not tokens:
        return None
        
    # Take last N tokens as context
    context_tokens = tokens[-context_words:]
    
    # Build regex pattern
    # Escape tokens but allow whitespace between them
    pattern_parts = [re.escape(t) for t in context_tokens]
    
    # The pattern: Context words + optional separator + CAPTURING GROUP (value)
    # We try to make the capturing group generic based on value type
    # If value is digits: (\d+)
    # If alphanumeric: (.+) ? Too broad. Let's start with strict capture.
    
    # Detecting matching group type
    if value_clean.isdigit():
        capture_group = r"(\d+)"
    elif re.match(r"^\d+[\.,]\d+$", value_clean): # formatting number
        capture_group = r"([\d\.,]+)"
    else:
        # Fallback to mostly safe characters, stopping at newline
        capture_group = r"([^\n]+)"
        
    # Join context
    context_regex = r"\s+".join(pattern_parts)
    
    # Final Regex
    # Case insensitive flag (?i) at start
    full_regex = f"(?i){context_regex}\\s*[:.\-]?\\s*{capture_group}"
    
    return full_regex

def learn(full_text, current_data):
    """
    Analyzes current_data against full_text to learn patterns.
    current_data: dict of field -> value
    """
    if not full_text:
        return 0
        
    conn = get_ia_conn()
    cur = conn.cursor()
    count = 0
    now = datetime.now().isoformat()
    
    # Fields intended for IAGO
    target_fields = [
        "NUMERO_REGISTRO", "NOME_LOGRADOURO", "BAIRRO", 
        "CIDADE", "LOTE", "QUADRA", "SETOR"
    ]
    
    for field in target_fields:
        # Check map keys (case insensitive or direct)
        # Assuming current_data keys are matching target_fields or lowercase
        val = current_data.get(field) or current_data.get(field.lower())
        
        if val:
            val_str = str(val).strip()
            regex = generate_context_regex(full_text, val_str)
            
            if regex:
                # Check if exists
                cur.execute("SELECT id, weight FROM patterns WHERE field_name=? AND regex_pattern=?", (field, regex))
                existing = cur.fetchone()
                
                if existing:
                    # Reinforce
                    cur.execute("UPDATE patterns SET weight = weight + 1 WHERE id=?", (existing['id'],))
                else:
                    # Learn new
                    # Privacy Update: Do NOT store the actual value (val_str) in the AI DB.
                    # Store a generic placeholders or the regex signature to ensure no PII leaks if DB is shared.
                    anonymized_example = f"Pattern for {field}" 
                    cur.execute("INSERT INTO patterns (field_name, regex_pattern, example_match, created_at) VALUES (?, ?, ?, ?)",
                                (field, regex, anonymized_example, now))
                    count += 1
    
    conn.commit()
    conn.close()
    return count

def analyze(full_text):
    """
    Applies learned patterns to text.
    Returns dict of extracted fields.
    """
    if not full_text:
        return {}
        
    conn = get_ia_conn()
    cur = conn.cursor()
    # Get all patterns ordered by weight desc
    cur.execute("SELECT field_name, regex_pattern FROM patterns ORDER BY weight DESC")
    rows = cur.fetchall()
    conn.close()
    
    results = {}
    
    for r in rows:
        field = r["field_name"]
        # Skip if we already found a high-confidence match? 
        # For now, let's keep the first match (highest weight)
        if field in results:
            continue
            
        pattern = r["regex_pattern"]
        try:
            match = re.search(pattern, full_text)
            if match:
                # Group 1 is the value
                val = match.group(1).strip()
                results[field] = val
        except re.error:
            # Bad regex from bad learning? Ignore
            pass
            
    return results
