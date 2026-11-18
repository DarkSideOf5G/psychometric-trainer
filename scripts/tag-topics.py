#!/usr/bin/env python3
"""Assign broad, provisional topics from private extracted text; publish IDs only.

Optional topic-overrides.json maps question IDs to topic ID lists (including []).
No extracted question text or answer data is published.
"""
import collections
import json
import re
import sqlite3
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
RULES = {
    'geometry': r'משולש|מעגל|רדיוס|קוטר|זווית|זוויות|מלבן|ריבוע|מרובע|מקבילית|טרפז|מעוין|מצולע|קוביי|קוביה|תיבה|גליל|מנסרה|פירמידה|שטח|היקף|נפח|אלכסו|פיתגורס',
    'numbers': r'זוגי|ראשוני|שלמים|שלם|שארית|מתחלק|ספרות|ספרה|עוקבים|מחלקים|מכפלות|חיובי|שלילי',
    'probability': r'הסתברות|סיכוי|באקראי|אפשרויות|סידורים|צירופים|להגריל|הגרלה|קובייה הוגנת|מטבע הוגן',
    'statistics': r'ממוצע|חציון|שכיח|התפלגות|סטיית תקן',
    'sequences': r'סדרה|סדרות|האיבר|איברים|חוקיות|דפוס',
    'data': r'תרשים|גרף|גרפים|טבלה|בטבלה|הטבלה|דיאגרמ',
    'word': r'שקלים|שקל|מחיר|מחירו|מחירה|קנה|קנתה|קנו|מכר|מכירה|הנחה|התייקר|רווח|הפסד|מהירות|קמ"ש|קילומטר|נסע|נסעה|הספק|בריכה|ברז|תערובת|תמיסה|גילו|גילה|גילם|פועלים|עובדים|יחס בין',
    'algebra': r'משווא|ביטוי|ביטויים|חזקה|חזקות|שורש|שבר|אחוז|ערך מוחלט|[a-zA-Z]\s*[+−=<>]|[=<>]\s*[a-zA-Z]',
}

def main():
    path = APP / 'site/data/catalog.json'
    catalog = json.loads(path.read_text())
    with sqlite3.connect(f'file:{APP.parent}/question-bank/questions.sqlite?mode=ro', uri=True) as db:
        texts = dict(db.execute('SELECT id,raw_text FROM questions'))
        contexts = dict(db.execute('SELECT id,text FROM contexts'))
    overrides_path = APP / 'topic-overrides.json'
    overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    counts = collections.Counter()
    for q in catalog['questions']:
        if q['subject'] != 'quantitative':
            continue
        # Chart contexts are essential: individual questions may only say "according to the data".
        batch_path = APP / f'site/data/exams/{q["exam"]}.json'
        if q['exam'] not in batches:
            batches[q['exam']] = json.loads(batch_path.read_text())
        record = batches[q['exam']]['questions'][q['id']]
        text = texts.get(q['id'], '') or ''
        tags = [key for key, pattern in RULES.items() if re.search(pattern, text)]
        shared = ' '.join(contexts.get(cid, '') or '' for cid in record['contexts'] if '-group-' in cid)
        if re.search(RULES['data'], shared) and 'data' not in tags:
            tags.append('data')
        tags = overrides.get(q['id'], tags)
        if not isinstance(tags, list) or any(t not in RULES for t in tags):
            raise ValueError(f'Invalid topics for {q["id"]}')
        q['topics'] = list(dict.fromkeys(tags))
        counts.update(q['topics'] or ['unclassified'])
    path.write_text(json.dumps(catalog, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(json.dumps(counts, ensure_ascii=False, indent=2))

batches = {}
if __name__ == '__main__':
    main()
