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
    /** Normalizes IAST diacritics for accent-tolerant searching without altering Devanagari. */
    private static function normalize(string $value): string {
        $value=function_exists('mb_strtolower')?mb_strtolower($value,'UTF-8'):strtolower($value);
        return strtr($value,[
            'ā'=>'a','ī'=>'i','ū'=>'u','ṛ'=>'r','ṝ'=>'r','ḷ'=>'l','ḹ'=>'l',
            'ṅ'=>'n','ñ'=>'n','ṇ'=>'n','ṭ'=>'t','ḍ'=>'d','ś'=>'s','ṣ'=>'s',
            'ṃ'=>'m','ṁ'=>'m','ḥ'=>'h','ḻ'=>'l',
        ]);
    }
    private static function tokens(string $query): array {
        preg_match_all('/[\p{L}\p{M}\p{N}]+/u',self::normalize($query),$matches);
        return array_values(array_unique(array_filter($matches[0]??[],static fn($x)=>$x!=='')));
    }
    /** Returns null if no valid prebuilt index exists; the unindexed search remains functional. */
    private function candidates(string $query): ?array {
        $root=getenv('AYURSUTRA_SEARCH_INDEX_PATH') ?: dirname($this->directory).'/search-index';
        $metaFile=$root.'/meta.json';
        if(!is_file($metaFile)||!is_file($this->directory.'/manifest.json'))return null;
        $meta=$this->readFile($metaFile);
        if(($meta['schema']??null)!==1 || ($meta['manifest_sha256']??'')!==hash_file('sha256',$this->directory.'/manifest.json'))return null;
        $terms=self::tokens($query);
        if(!$terms)return null;
        $common=null;
        foreach($terms as $term){
            $prefix=substr(hash('sha256',$term),0,2);
            $file=$root.'/'.$prefix.'.json';
            if(!is_file($file))return null;
            $index=$this->readFile($file);
            $ids=$index[$term]??[];
            if(!is_array($ids))return null;
            $set=array_fill_keys($ids,true);
            $common=$common===null?$set:array_intersect_key($common,$set);
            if(!$common)break;
        }
        // Preserve substring search semantics when the exact-token index has no matches.
        return $common?:null;
    }
    /** Bounded public search of attributed Sanskrit. Never exposes private editorial data. */
    public function search(string $query,int $limit): array {
        $matches=[];$candidateIds=$this->candidates($query);
        $needle=self::normalize($query);
        $sectionIds=null;
        if($candidateIds!==null){
            $sectionIds=[];
            foreach($candidateIds as $id=>$_){$parts=explode('/',$id);if(count($parts)===3)$sectionIds[$parts[0].'/'.$parts[1]]=true;}
        }
        foreach($this->manifest()['books']??[] as $book){
            foreach($book['sections']??[] as $section){
                if($sectionIds!==null&&!isset($sectionIds[$book['id'].'/'.$section['slug']]))continue;
                foreach($this->chapters($book['id'],$section['slug']) as $chapter){
                    $key=$book['id'].'/'.$section['slug'].'/'.$chapter['chapter_slug'];
                    if($candidateIds!==null&&!isset($candidateIds[$key]))continue;
                    $path='/library/'.$key;
                    foreach($chapter['passages']??[] as $passage){
                        $s=trim((string)($passage['text_iast']??'').' '.(string)($passage['text_devanagari']??''));
                        if($s==='' || !str_contains(self::normalize($s),$needle))continue;
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
