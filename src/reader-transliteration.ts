import {scriptMaps} from './reader-script-maps';
/** Automated display transliteration only: NEVER claim this is an original reviewed edition. */
const vowels:Record<string,[string,string]>={
 'ai':['ऐ','ै'],'au':['औ','ौ'],'ā':['आ','ा'],'ī':['ई','ी'],'ū':['ऊ','ू'],
 'ṝ':['ॠ','ॄ'],'ṛ':['ऋ','ृ'],'ḹ':['ॡ','ॣ'],'ḷ':['ऌ','ॢ'],
 'a':['अ',''],'i':['इ','ि'],'u':['उ','ु'],'e':['ए','े'],'o':['ओ','ो']
};
const consonants:Record<string,string>={
 'kṣ':'क्ष','jñ':'ज्ञ','kh':'ख','gh':'घ','ch':'छ','jh':'झ','ṭh':'ठ','ḍh':'ढ',
 'th':'थ','dh':'ध','ph':'फ','bh':'भ','k':'क','g':'ग','ṅ':'ङ','c':'च',
 'j':'ज','ñ':'ञ','ṭ':'ट','ḍ':'ड','ṇ':'ण','t':'त','d':'द','n':'न',
 'p':'प','b':'ब','m':'म','y':'य','r':'र','l':'ल','v':'व','ś':'श',
 'ṣ':'ष','s':'स','h':'ह','ḻ':'ळ'
};
const vowelsSorted=Object.keys(vowels).sort((a,b)=>b.length-a.length);
const consSorted=Object.keys(consonants).sort((a,b)=>b.length-a.length);
function matching(text:string,offset:number,keys:string[]){return keys.find(token=>text.startsWith(token,offset));}
export function romanToDevanagari(text:string):string{
 const original=text.normalize('NFC');
 const source=original.toLowerCase();
 let output='',i=0;
 while(i<source.length){
  const cons=matching(source,i,consSorted);
  if(cons){
   output+=consonants[cons];i+=cons.length;
   const vowel=matching(source,i,vowelsSorted);
   if(vowel){output+=vowels[vowel][1];i+=vowel.length;}
   else output+='्';
   continue;
  }
  const vowel=matching(source,i,vowelsSorted);
  if(vowel){output+=vowels[vowel][0];i+=vowel.length;continue;}
  const mark=source[i];
  if(mark==='ṃ'||mark==='ṁ')output+='ं';
  else if(mark==='ḥ')output+='ः';
  else if(mark==="'")output+='ऽ';
  else if(mark==='+')output+=' ';
  else if(source.startsWith('||',i)||source.startsWith('//',i)){output+='॥';i+=2;continue;}
  else if(mark==='|'||mark==='/')output+='।';
  else output+=original[i];
  i++;
 }
 return output;
}

export const readerScripts=[
 {id:'devanagari',label:'Devanagari',lang:'sa-Deva'},
 {id:'iast',label:'IAST (Roman)',lang:'sa-Latn'},
 {id:'telugu',label:'Telugu',lang:'sa-Telu'},
 {id:'tamil',label:'Tamil',lang:'sa-Taml'},
 {id:'malayalam',label:'Malayalam',lang:'sa-Mlym'},
 {id:'kannada',label:'Kannada',lang:'sa-Knda'},
 {id:'gujarati',label:'Gujarati',lang:'sa-Gujr'},
 {id:'bengali',label:'Bengali',lang:'sa-Beng'},
 {id:'gurmukhi',label:'Gurmukhi',lang:'sa-Guru'},
] as const;
export type ReaderScript=typeof readerScripts[number]['id'];
const devanagariVowels=new Map(Object.entries(vowels).map(([latin,[letter]])=>[letter,latin]));
const devanagariMarks=new Map(Object.entries(vowels).map(([latin,[,mark]])=>[mark,latin]));
const devanagariConsonants=new Map(Object.entries(consonants).filter(([,letter])=>letter.length===1).map(([latin,letter])=>[letter,latin]));
function devanagariToIast(text:string){
 const letters=Array.from(text.normalize('NFC'));
 const marks:Record<string,string>={'ं':'ṃ','ः':'ḥ','ँ':'m̐','ऽ':"'",'।':'|','॥':'||','ॐ':'oṃ'};
 let result='';
 for(let i=0;i<letters.length;i++){
  const letter=letters[i],next=letters[i+1],consonant=devanagariConsonants.get(letter);
  if(consonant){
   const vowel=devanagariMarks.get(next);
   if(next==='्'||vowel){result+=consonant+(vowel??'');i++;}
   else result+=consonant+'a';
  }else if(letter>='०'&&letter<='९')result+=String(letter.charCodeAt(0)-0x966);
  else result+=devanagariVowels.get(letter)??marks[letter]??letter;
 }
 return result;
}
export function renderSanskrit(deva:string,iast:string,script:ReaderScript):string{
 if(script==='iast')return iast||(deva?devanagariToIast(deva):'');
 const original=deva||romanToDevanagari(iast);
 if(script==='devanagari')return original;
 const map=scriptMaps[script];
 // Keep source characters with no equivalent rather than dropping them.
 return Array.from(original.normalize('NFC')).map((letter,index,letters)=>{
  const glyph=map[letter]??letter;
  if(script==='tamil'&&/[²³⁴]$/.test(glyph)&&devanagariConsonants.has(letter)){
   const next=letters[index+1];
   if(next==='्'||devanagariMarks.has(next))return glyph.slice(0,-1);
  }
  if(script==='tamil'&&(letter==='्'||devanagariMarks.has(letter))){
   const previous=map[letters[index-1]]??'';
   if(/[²³⁴]$/.test(previous)&&devanagariConsonants.has(letters[index-1]))return glyph+previous.slice(-1);
  }
  return glyph;
 }).join('');
}
