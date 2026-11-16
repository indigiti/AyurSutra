import {test,expect} from '@playwright/test';

test('public home and chapter navigation render without server errors',async({page})=>{
  await page.goto('/');
  await expect(page.getByRole('heading',{name:/Ancient wisdom/i})).toBeVisible();
  await page.goto('/library/charaka-samhita/sutrasthanam/dirghanjivitiya');
  await expect(page.getByRole('navigation',{name:'Chapter navigation'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Save chapter'})).toBeVisible();
  await page.getByRole('button',{name:'Save chapter'}).click();
  await expect(page.getByRole('button',{name:'Saved'})).toBeVisible();
  await page.goto('/my-library');
  await expect(page.getByText('Saved', {exact:false}).first()).toBeVisible();
  await expect(page.getByRole('link',{name:/Open chapter/i})).toBeVisible();
});

test('API restricts editorial data and serves attributed source text',async({request})=>{
  const denied=await request.get('http://127.0.0.1:8000/api/v1/admin/status');
  expect(denied.status()).toBe(401);
  const status=await request.get('http://127.0.0.1:8000/api/v1/status');
  expect(status.ok()).toBeTruthy();
  const chapter=await request.get('http://127.0.0.1:8000/api/v1/chapters/charaka-samhita/sutrasthanam/dirghanjivitiya');
  expect(chapter.ok()).toBeTruthy();
  const parsed=await chapter.json();
  expect(parsed.data.passages.length).toBeGreaterThan(0);
});

test('MCQ catalogue does not pretend unavailable papers are published',async({page})=>{
  await page.goto('/mcq');
  await expect(page.getByText('IMPORT PENDING').first()).toBeVisible();
  await page.goto('/mcq/demo');
  await expect(page.getByText('QUESTION 1 OF 3')).toBeVisible();
  await page.getByRole('button',{name:/Finish & review answers/i}).click();
  await expect(page.getByText('PRACTICE COMPLETE')).toBeVisible();
});


test('source-inspired chapter reader allows search, transliteration and passage bookmarks',async({page})=>{
 await page.goto('/library/sushruta-samhita/sutrasthanam/vedotpattyadhyayah');
 await expect(page.getByRole('region',{name:'Classical Sanskrit reader'})).toBeVisible();
 await expect(page.getByRole('heading',{level:1})).toContainText('वेदोत्पत्त्यध्यायः');
 await expect(page.getByRole('group',{name:'Text script'}).getByRole('button',{name:/Devanagari/i})).toBeEnabled();
 await expect(page.getByRole('button',{name:'Telugu'})).toBeEnabled();
 for(const [name,id,characters] of [
  ['IAST (Roman)','iast',/[āṃḥ]/u],['Telugu','telugu',/[\u0c00-\u0c7f]/u],['Tamil','tamil',/[\u0b80-\u0bff]/u],
  ['Malayalam','malayalam',/[\u0d00-\u0d7f]/u],['Kannada','kannada',/[\u0c80-\u0cff]/u],['Gujarati','gujarati',/[\u0a80-\u0aff]/u],
  ['Bengali','bengali',/[\u0980-\u09ff]/u],['Gurmukhi','gurmukhi',/[\u0a00-\u0a7f]/u],
 ] as const){
  await page.getByRole('button',{name,exact:true}).click();
  await expect(page).toHaveURL(url=>url.searchParams.get('script')===id);
  await expect(page.locator('.source-shloka-text').first()).toHaveText(characters);
 }
 await page.reload();
 await expect(page.getByRole('button',{name:'Gurmukhi',exact:true})).toHaveAttribute('aria-pressed','true');
 await page.getByRole('search').getByRole('textbox',{name:/Search passage text/i}).fill('this phrase is not in the source');
 await page.getByRole('search').getByRole('button',{name:'Search'}).click();
 await expect(page.getByRole('heading',{name:'No matching passages'})).toBeVisible();
 await page.getByRole('button',{name:'Show all passages'}).click();
 await expect(page.locator('.source-shloka-card').first()).toBeVisible();
 await page.getByRole('button',{name:'Save passage'}).first().click();
 await page.goto('/my-library');
 await expect(page.getByRole('link',{name:'Open passage'}).last()).toBeVisible();
});

test('Classical Texts links all five books and searches the text corpus',async({page})=>{
 await page.goto('/library');
 await expect(page.getByRole('heading',{name:'Classical Texts',exact:true})).toBeVisible();
 await expect(page.locator('.classical-grid article')).toHaveCount(5);
 for(const [name,slug] of [['Sushruta Samhita','sushruta-samhita'],['Charaka Samhita','charaka-samhita'],['Ashtanga Hridaya','ashtanga-hridaya'],['Ashtanga Sangraha','ashtanga-sangraha'],['Madhava Nidana','madhava-nidana']]){
  await expect(page.getByRole('link',{name:'Read '+name,exact:true})).toHaveAttribute('href',new RegExp('/library/'+slug+'$'));
 }
 await page.getByLabel('Search across all classical texts').fill('अथातो');
 await page.getByRole('search',{name:'Search all classical texts'}).getByRole('button',{name:'Search',exact:true}).click();
 await expect(page).toHaveURL(/\/search\?q=.*&type=texts$/);
});
test('global commentary and individual cards are independent, and terms stay visible',async({page})=>{
 await page.route('**/api/v1/chapters/sushruta-samhita/sutrasthanam/vedotpattyadhyayah',route=>route.fulfill({json:{data:{
  title:'Fixture',status:'published',source_url:'https://example.com',passages:['a','b'].map((id,index)=>({
   id,reference:String(index+1),adhikarana:'Test grouping',text_devanagari:index?'अथातो':'',text_iast:'',translation_en:'',
   commentary_sanskrit:'अथातो',commentary_en:'Fixture commentary '+id,key_terms:[{term:'अथ',iast:'atha',definition:'Fixture term'}]
  }))
 }}}));
 await page.goto('/library/sushruta-samhita/sutrasthanam/vedotpattyadhyayah?script=telugu');
 const cards=page.locator('.source-shloka-card');
 await expect(cards).toHaveCount(2);
 await expect(cards.first().locator('.source-shloka-text')).toHaveCount(0);
 await expect(cards.nth(1).getByText('View original',{exact:true})).toBeVisible();
 await expect(page.getByText('Fixture term',{exact:true})).toHaveCount(2);
 await page.getByRole('button',{name:'Show commentary',exact:true}).click();
 await expect(page.getByText('Fixture commentary a',{exact:true})).toBeVisible();
 await expect(page.getByText('Fixture commentary b',{exact:true})).toBeVisible();
 await cards.first().getByRole('button',{name:/Hide commentary/i}).click();
 await expect(page.getByText('Fixture commentary a',{exact:true})).toHaveCount(0);
 await expect(page.getByText('Fixture commentary b',{exact:true})).toBeVisible();
 await expect(cards.first().getByText('Fixture term',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Hide commentary',exact:true}).click();
 await expect(page.getByText('Fixture commentary b',{exact:true})).toHaveCount(0);
});
