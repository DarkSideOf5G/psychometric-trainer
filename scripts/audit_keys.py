import json,hashlib,pathlib
app=pathlib.Path(__file__).resolve().parents[1]
keys={k['question_id']:k['correct_choice_id'].rsplit('-c',1)[1] for k in json.loads((app.parent/'question-bank/private-answer-keys.json').read_text())}
n=0
for f in (app/'site/data/exams').glob('*.json'):
 for q in json.loads(f.read_text())['questions'].values():
  expected=hashlib.sha256(f"{q['id']}:{keys[q['id']]}:{q['salt']}".encode()).hexdigest()
  assert expected==q['check'],q['id']
  n+=1
assert n==8532,n
(app/'reports/key-audit.json').write_text(json.dumps({'questions':n,'all_match_original_keys':True}))
print(f'{n} answer checks match the original official keys')
