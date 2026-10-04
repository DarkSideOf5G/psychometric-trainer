export function pool(catalog, mode) {
 const subject=mode==='math'?'quantitative':mode;
 return catalog.questions.filter(q=>q.subject===subject);
}
export function chooseQuestion(rows, mastered, previous, random=Math.random) {
 let available=rows.filter(q=>!Object.hasOwn(mastered,q.id));
 if(available.length>1)available=available.filter(q=>q.id!==previous);
 return available.length ? available[Math.min(available.length-1,Math.floor(Math.max(0,random())*available.length))] : null;
}
export async function answerDigest(id,label,salt) {
 if(!Number.isInteger(label)||label<1||label>4)throw Error('Invalid answer');
 const bytes=new TextEncoder().encode(`${id}:${label}:${salt}`);
 const hash=await crypto.subtle.digest('SHA-256',bytes);
 return [...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,'0')).join('');
}
export async function checkAnswer(question,label) {return await answerDigest(question.id,label,question.salt)===question.check;}
export async function correctLabel(question) {for(let n=1;n<=4;n++)if(await checkAnswer(question,n))return n;throw Error('Invalid answer check');}
export function sanitizeProgress(value, allowed) {
 if(!value||value.version!==1||!value.mastered||typeof value.mastered!=='object'||Array.isArray(value.mastered))throw Error('Invalid progress');
 const mastered={},attempts={};
 for(const [id,time] of Object.entries(value.mastered))if(allowed.has(id)&&typeof time==='string'&&Number.isFinite(Date.parse(time)))mastered[id]=time;
 for(const [id,n] of Object.entries(value.attempts||{}))if(allowed.has(id)&&Number.isSafeInteger(n)&&n>=0&&n<=1000000)attempts[id]=n;
 return {version:1,mastered,attempts};
}
export class Progress {
 constructor(storage,key,allowed) {this.storage=storage;this.key=key;this.allowed=allowed;this.state={version:1,mastered:{},attempts:{}};this.persistent=true;this.load();}
 load() {try{const raw=this.storage.getItem(this.key);if(raw)this.state=sanitizeProgress(JSON.parse(raw),this.allowed);}catch{this.persistent=false;}return this.state;}
 write() {try{this.storage.setItem(this.key,JSON.stringify(this.state));this.persistent=true;}catch{this.persistent=false;}return this.persistent;}
 record(id,correct) {
  if(!this.allowed.has(id))throw Error('Unknown question');
  try{const saved=this.storage.getItem(this.key);if(saved){const prior=sanitizeProgress(JSON.parse(saved),this.allowed);this.state.mastered={...prior.mastered,...this.state.mastered};for(const [q,n] of Object.entries(prior.attempts))this.state.attempts[q]=Math.max(n,this.state.attempts[q]||0);}}catch{}
  this.state.attempts[id]=(this.state.attempts[id]||0)+1;if(correct)this.state.mastered[id]=new Date().toISOString();this.write();
 }
 import(value) {const other=sanitizeProgress(value,this.allowed);this.state.mastered={...this.state.mastered,...other.mastered};for(const [id,n] of Object.entries(other.attempts))this.state.attempts[id]=Math.max(n,this.state.attempts[id]||0);this.write();}
 reset() {this.state={version:1,mastered:{},attempts:{}};this.write();}
}
