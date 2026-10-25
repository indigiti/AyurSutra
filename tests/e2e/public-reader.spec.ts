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
 await expect(page.getByRole('heading',{level:1})).toContainText('1.');
 await expect(page.getByRole('group',{name:'Text script'}).getByRole('button',{name:/Devanagari/i})).toBeEnabled();
 await expect(page.getByRole('button',{name:'Telugu'})).toBeDisabled();
 await page.getByRole('search').getByRole('textbox',{name:/Search passage text/i}).fill('this phrase is not in the source');
 await page.getByRole('search').getByRole('button',{name:'Search'}).click();
 await expect(page.getByRole('heading',{name:'No matching passages'})).toBeVisible();
 await page.getByRole('button',{name:'Show all passages'}).click();
 await expect(page.locator('.source-shloka-card').first()).toBeVisible();
 await page.getByRole('button',{name:'Save passage'}).first().click();
 await page.goto('/my-library');
 await expect(page.getByRole('link',{name:'Open passage'}).last()).toBeVisible();
});
