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
 const source=text.normalize('NFC').toLowerCase();
 let output='',i=0;
 while(i<source.length){
  const cons=matching(source,i,consSorted);
  if(cons){
   output+=consonants[cons];i+=cons.length;
   const vowel=matching(source,i,vowelsSorted);
   if(vowel){output+=vowels[vowel][1];i+=vowel.length;}
   else if(!['ṃ','ṁ','ḥ'].some(x=>source.startsWith(x,i)))output+='्';
   continue;
  }
  const vowel=matching(source,i,vowelsSorted);
  if(vowel){output+=vowels[vowel][0];i+=vowel.length;continue;}
  const mark=source[i];
  if(mark==='ṃ'||mark==='ṁ')output+='ं';
  else if(mark==='ḥ')output+='ः';
  else if(mark==="'")output+='ऽ';
  else if(mark==='+')output+=' ';
  else if(mark==='|')output+='।';
  else output+=text[i];
  i++;
 }
 return output;
}
