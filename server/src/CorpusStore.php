<?php
declare(strict_types=1);
namespace AyurSutra;

/** Immutable, attributed Sanskrit source editions kept separate from editable chapters. */
final class CorpusStore {
    public function __construct(private readonly string $directory) {}
    private function readFile(string $filename): array {
        if (!is_file($filename)) return [];
        $text=file_get_contents($filename);
        if ($text===false) return [];
        $parsed=json_decode($text,true,512,JSON_THROW_ON_ERROR);
        return is_array($parsed)?$parsed:[];
    }
    public function manifest(): array {return $this->readFile($this->directory.'/manifest.json');}
    private function valid(string $slug): bool {return preg_match('/^[a-z0-9-]+$/D',$slug)===1;}
    public function chapters(string $book,string $section): array {
        if (!$this->valid($book)||!$this->valid($section))return [];
        $sectionFile=$this->directory.'/sections/'.$book.'-'.$section.'.json';
        $path=is_file($sectionFile)?$sectionFile:$this->directory.'/'.$book.'.json';
        $data=$this->readFile($path);
        if (($data['book_id']??null)!==$book)return [];
        return array_values(array_filter($data['chapters']??[],static fn($c)=>($c['section_slug']??null)===$section));
    }
    public function chapter(string $book,string $section,string $slug): ?array {
        if (!$this->valid($slug))return null;
        foreach ($this->chapters($book,$section) as $c)if(($c['chapter_slug']??null)===$slug)return $c;
        return null;
    }
    public function chapterIndex(string $book): array {
        $items=[];
        foreach($this->manifest()['books']??[] as $b){
            if(($b['id']??null)===$book)foreach($b['sections']??[] as $s)foreach($s['chapters']??[] as $c){
                $items[($s['slug']??'').'/'.($c['slug']??'')]=[
                    'status'=>'source-edition','passage_count'=>(int)($c['passage_count']??0),
                    'source_title'=>$c['source_title']??null,
                ];
            }
        }
        return $items;
    }
    /** Bounded public search of original Sanskrit only. No private answers or editorial drafts. */
    public function search(string $query,int $limit): array {
        $matches=[];
        foreach($this->manifest()['books']??[] as $book){
            foreach($book['sections']??[] as $section){
                foreach($this->chapters($book['id'],$section['slug']) as $chapter){
                    $path='/library/'.$book['id'].'/'.$section['slug'].'/'.$chapter['chapter_slug'];
                    foreach($chapter['passages']??[] as $passage){
                        $s=trim((string)($passage['text_iast']??'').' '.(string)($passage['text_devanagari']??''));
                        if($s==='' || preg_match('/'.preg_quote($query,'/').'/iu',$s)!==1)continue;
                        $matches[]=['type'=>'passage','status'=>'source-edition',
                            'title'=>($chapter['source_title']??$chapter['title']).' · '.($passage['reference']??''),
                            'description'=>function_exists('mb_substr')?mb_substr($s,0,190):substr($s,0,190),
                            'path'=>$path.'#'.rawurlencode((string)$passage['id'])];
                        if(count($matches)>=$limit)return $matches;
                    }
                }
            }
        }
        return $matches;
    }
}
