<?php
declare(strict_types=1);
namespace AyurSutra;
use AyurSutra\Support\StoreInterface;

/** Public read-only academy search. No unpublished data, answer keys or draft counts. */
final class SearchService {
    public function __construct(private readonly StoreInterface $store) {}
    private static function matches(string $haystack, string $needle): bool {
        // Unicode-aware; works on shared hosting without the optional mbstring extension.
        return preg_match('/'.preg_quote($needle, '/').'/iu', $haystack) === 1;
    }
    private static function excerpt(string $text, int $max=200): string {
        $text=trim(preg_replace('/\s+/u',' ', $text) ?? '');
        if (preg_match('/^.{0,'.$max.'}$/us', $text)) return $text;
        return preg_replace('/^(.{0,'.$max.'}).*$/us','$1…',$text) ?? '';
    }
    public function search(string $query, string $type='all', int $limit=20): array {
        $items=[];
        $include=static fn(string $test): bool => $type==='all' || $type===$test;
        if ($include('texts')) {
            foreach ($this->store->read('books') as $book) {
                $title=(string)($book['title']??'');
                if (self::matches($title.' '.($book['id']??''),$query)) {
                    $items[]=['type'=>'book','status'=>'catalogue','title'=>$title,'description'=>'Classical text catalogue; not a claim of a complete imported edition','path'=>'/library/'.rawurlencode($book['id'])];
                }
            }
            foreach ($this->store->read('verses') as $verse) {
                if (($verse['reviewed']??false)!==true || (($verse['published']??true)!==true)) continue;
                $source=implode(' ',array_map('strval',[$verse['reference']??'',$verse['text_iast']??'',$verse['text_devanagari']??'',$verse['translation_en']??'']));
                if (!self::matches($source,$query))continue;
                $id=(string)($verse['id']??'');$book=(string)($verse['book_id']??'');
                $items[]=['type'=>'verse','status'=>'sample','title'=>$book.' · '.($verse['reference']??''),'description'=>self::excerpt((string)($verse['text_devanagari']??$verse['text_iast']??'')),'path'=>'/library/'.rawurlencode($book).'#'.rawurlencode($id)];
            }
            foreach ($this->store->read('chapters') as $chapter) {
                if (($chapter['status']??'')!=='published') continue;
                $book=(string)$chapter['book_id'];$section=(string)$chapter['section_slug'];$slug=(string)$chapter['chapter_slug'];
                $url='/library/'.rawurlencode($book).'/'.rawurlencode($section).'/'.rawurlencode($slug);
                $title=(string)($chapter['title']??'Chapter');
                if(self::matches($title.' '.($chapter['id']??''),$query)){
                    $items[]=['type'=>'chapter','status'=>'published','title'=>$title,'description'=>count($chapter['passages']??[]).' published passages','path'=>$url];
                }
                foreach(($chapter['passages']??[]) as $passage){
                    $words=implode(' ',array_map('strval',[$passage['reference']??'',$passage['text_devanagari']??'',$passage['text_iast']??'',$passage['translation_en']??'',$passage['commentary']??'']));
                    foreach(($passage['key_terms']??[]) as $term) $words.=' '.($term['term']??'').' '.($term['definition']??'');
                    if(!self::matches($words,$query))continue;
                    $items[]=['type'=>'passage','status'=>'published','title'=>$title.' · '.($passage['reference']??''),'description'=>self::excerpt((string)($passage['text_devanagari']??$passage['text_iast']??'')),'path'=>$url.'#'.rawurlencode((string)($passage['id']??''))];
                }
            }
        }
        if ($include('notes')) {
            foreach($this->store->read('notes') as $note){
                if(($note['status']??'')!=='published')continue;
                $words=implode(' ',[$note['title']??'',$note['subject']??'',$note['body']??'']);
                if(!self::matches($words,$query))continue;
                $items[]=['type'=>'note','status'=>'published','title'=>(string)$note['title'],'description'=>self::excerpt((string)$note['body']),'path'=>'/notes/'.rawurlencode($note['slug'])];
            }
        }
        if ($include('exams')) {
            foreach($this->store->read('exams') as $paper){
                if(($paper['status']??'')!=='published')continue;
                if(!self::matches((string)$paper['title'],$query))continue;
                $items[]=['type'=>'exam','status'=>'published','title'=>(string)$paper['title'],'description'=>count($paper['questions']??[]).' verified practice questions','path'=>'/mcq/'.rawurlencode($paper['id'])];
            }
        }
        $total=count($items);
        return ['query'=>$query,'type'=>$type,'total'=>$total,'limit'=>$limit,'data'=>array_slice($items,0,$limit)];
    }
}
