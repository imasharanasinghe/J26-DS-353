import json
import pandas as pd
import re
import os

def load_dataset(filepath):
    records = []
    with open(filepath, 'r') as f:
        for line in f:
            records.append(json.loads(line.strip()))
    return records

def clean_text(text):
    # Remove filler words and transcription noise
    text = re.sub(r"\b(um|uh|er|ah)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    return text.strip()

def chunk_text(text, chunk_size=200, overlap=50):
    """Split text into overlapping word chunks"""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = ' '.join(words[i:i+chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap  # overlap ensures boundary relations are caught
    return chunks

def prepare_corpus(filepaths):
    all_chunks = []
    for filepath in filepaths:
        records = load_dataset(filepath)
        for record in records:
            text = clean_text(record.get('text', ''))
            category = record.get('category', ['unknown'])[0]
            title = record.get('title', '')
            video_id = record.get('video_ID', '')

            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    'video_id': video_id,
                    'title': title,
                    'category': category,
                    'chunk_id': f"{video_id}_{i}",
                    'text': chunk
                })
    return pd.DataFrame(all_chunks)

if __name__ == "__main__":
    files = [
        'data/raw/Captions_algorithms_Princeton.json'
    ]
    df = prepare_corpus(files)
    df.to_csv('data/processed/chunks.csv', index=False)
    print(f"Total chunks created: {len(df)}")
    print(f"Sample:\n{df.head(3)}")