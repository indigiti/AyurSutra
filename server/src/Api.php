<?php
declare(strict_types=1);
namespace AyurSutra;
use AyurSutra\Support\StoreInterface;
use Throwable;

final class Api {
    private readonly CorpusStore $corpus;
    public function __construct(private readonly StoreInterface $store, private readonly string $adminToken) {
        $storage=getenv('AYURSUTRA_STORAGE_PATH') ?: dirname(__DIR__).'/storage';
        $this->corpus=new CorpusStore(getenv('AYURSUTRA_CORPUS_PATH') ?: rtrim($storage,'/').'/corpus');
    }
    private static function respond(int $status, array $body): never {
        http_response_code($status);
        header('Content-Type: application/json; charset=utf-8');
        header('X-Content-Type-Options: nosniff');
        header('Cache-Control: no-store');
        echo json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
        exit;
    }
    private static function body(): array {
        $raw=file_get_contents('php://input');
        if ($raw===false || strlen($raw)>1500000) self::respond(413, ['error'=>'Request too large']);
        try {$data=json_decode($raw,true,64,JSON_THROW_ON_ERROR);} catch (Throwable) {self::respond(400,['error'=>'Invalid JSON']);}
        if (!is_array($data) || array_is_list($data)) self::respond(400,['error'=>'Expected JSON object']);
        return $data;
    }
    private function authorize(): void {
        $authorization=$_SERVER['HTTP_AUTHORIZATION'] ?? ($_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '');
        $provided=str_starts_with($authorization,'Bearer ')?substr($authorization,7):'';
        if (strlen($this->adminToken)<32 || !hash_equals($this->adminToken,$provided)) self::respond(401,['error'=>'Unauthorized']);
    }
    public function run(): never {
        try {$this->dispatch();} catch (Throwable $e) {
            error_log('AyurSutra API: '.$e->getMessage());
            self::respond(500,['error'=>'Internal server error']);
        }
    }
    private function dispatch(): never {
        $path=parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
        $path='/'.trim((string)$path,'/');
        if (str_starts_with($path,'/api/v1/')) $path=substr($path,7);
        $method=strtoupper($_SERVER['REQUEST_METHOD']??'GET');
        if ($method==='OPTIONS') self::respond(405,['error'=>'CORS preflight not supported; use same origin']);
        if ($method==='GET' && $path==='/status') self::respond(200,['ok'=>true,'version'=>'0.1.0','storage'=>'json-files','database'=>false]);
        if ($method==='GET' && $path==='/books') self::respond(200,['data'=>$this->store->read('books')]);
        if ($method==='GET' && $path==='/corpus/status') self::respond(200,['data'=>$this->corpus->manifest()]);
        if ($method==='GET' && $path==='/search') {
            $query=trim((string)($_GET['q']??''));$type=(string)($_GET['type']??'all');
            if (strlen($query)>400 || !preg_match('/^.{2,120}$/us',$query) || !in_array($type,['all','texts','notes','exams'],true))self::respond(422,['error'=>'Enter 2–120 characters and a valid search category']);
            $limit=min(40,max(1,(int)($_GET['limit']??20)));
            self::respond(200,(new SearchService($this->store,$this->corpus))->search($query,$type,$limit));
        }
        if ($method==='GET' && preg_match('~^/books/([a-z0-9-]+)/verses$~D',$path,$m)) {
            $verses=array_values(array_filter($this->store->read('verses'),fn($v)=>($v['book_id']??'')===$m[1] && ($v['reviewed']??false)===true && (!array_key_exists('published',$v) || $v['published']===true)));
            $total=count($verses);
            $offset=max(0, (int)($_GET['offset']??0));$limit=min(250,max(1,(int)($_GET['limit']??100)));
            self::respond(200,['data'=>array_slice($verses,$offset,$limit),'total'=>$total,'limit'=>$limit,'offset'=>$offset]);
        }
        // Chapter passages stay private until an editor explicitly publishes the imported chapter.
        if ($method==='GET' && preg_match('~^/chapters/([a-z0-9-]+)/([a-z0-9-]+)/([a-z0-9-]+)$~D',$path,$m)) {
            $chapterId=$m[1].'/'.$m[2].'/'.$m[3];
            foreach($this->store->read('chapters') as $chapter) if(($chapter['id']??'')===$chapterId && ($chapter['status']??'')==='published') {
                self::respond(200,['data'=>$chapter]);
            }
            $source=$this->corpus->chapter($m[1],$m[2],$m[3]);
            if($source!==null)self::respond(200,['data'=>$source]);
            self::respond(404,['error'=>'Published chapter not found']);
        }
        // Public read APIs. Content status is explicit: catalogue entries are not published papers.
        if ($method==='GET' && $path==='/sections') {
            $book=trim((string)($_GET['book_id']??''));
            $items=$this->store->read('sections');
            if ($book!=='') $items=array_values(array_filter($items,fn($v)=>($v['book_id']??'')===$book));
            $published=[];
            foreach($this->store->read('chapters') as $chapter)if(($chapter['status']??'')==='published') $published[$chapter['id']]=$chapter;
            $sourceIndexes=[];
            foreach($items as $section) {
                $id=$section['book_id'];
                if(!isset($sourceIndexes[$id]))$sourceIndexes[$id]=$this->corpus->chapterIndex($id);
            }
            foreach($items as &$section)foreach($section['chapters'] as &$chapter){
                $key=$section['book_id'].'/'.$section['slug'].'/'.$chapter['slug'];
                $sourceKey=$section['slug'].'/'.$chapter['slug'];
                if(isset($sourceIndexes[$section['book_id']][$sourceKey])){
                    $source=$sourceIndexes[$section['book_id']][$sourceKey];
                    $chapter['status']='source-edition';$chapter['passage_count']=$source['passage_count'];
                    if(empty($chapter['title'])&&$source['source_title'])$chapter['title']=$source['source_title'];
                }
                if(isset($published[$key])){$chapter['status']='published';$chapter['title']=$published[$key]['title'];$chapter['passage_count']=count($published[$key]['passages']??[]);}
            }
            unset($section,$chapter);
            self::respond(200,['data'=>$items]);
        }
        if ($method==='GET' && $path==='/exams') {
            $items=array_map(static function(array $x):array {unset($x['questions']);$x['available_count']=($x['status']??'')==='published'?($x['published_count']??0):0;return $x;},$this->store->read('exams'));
            self::respond(200,['data'=>$items]);
        }
        if ($method==='GET' && preg_match('~^/exams/([a-z0-9-]+)$~D',$path,$m)) {
            foreach($this->store->read('exams') as $exam)if(($exam['id']??'')===$m[1]) {
                if(($exam['status']??'')!=='published')self::respond(200,['data'=>['id'=>$exam['id'],'title'=>$exam['title'],'status'=>$exam['status'],'expected_count'=>$exam['expected_count'],'available_count'=>0,'questions'=>[]]]);
                $public=array_map(static fn($q)=>['id'=>$q['id'],'question'=>$q['question'],'options'=>$q['options'],'subject'=>$q['subject']??'General'],$exam['questions']);
                self::respond(200,['data'=>['id'=>$exam['id'],'title'=>$exam['title'],'status'=>'published','expected_count'=>$exam['expected_count'],'available_count'=>count($public),'questions'=>$public]]);
            }
            self::respond(404,['error'=>'Exam not found']);
        }
        if ($method==='POST' && preg_match('~^/exams/([a-z0-9-]+)/score$~D',$path,$m)) {
            $data=self::body();$answers=$data['answers']??null;
            if(!is_array($answers)||count($answers)>250)self::respond(422,['error'=>'Invalid answer sheet']);
            foreach($this->store->read('exams') as $exam)if(($exam['id']??'')===$m[1]&&($exam['status']??'')==='published'){
                $score=0;$review=[];
                foreach($exam['questions'] as $q){$a=$answers[$q['id']]??null;$right=$q['answer'];if($a===$right)$score++;$review[]=['id'=>$q['id'],'answer'=>$right,'selected'=>is_int($a)?$a:null,'explanation'=>$q['explanation']??''];}
                self::respond(200,['data'=>['score'=>$score,'total'=>count($review),'review'=>$review]]);
            }
            self::respond(404,['error'=>'Published exam not found']);
        }
        if ($method==='GET' && $path==='/notes') {
            $notes=array_values(array_filter($this->store->read('notes'),static fn($x)=>($x['status']??'')==='published'));
            self::respond(200,['data'=>$notes]);
        }
        if ($method==='GET' && preg_match('~^/notes/([a-z0-9-]+)$~D',$path,$m)) {
            foreach($this->store->read('notes') as $note)if(($note['slug']??'')===$m[1]&&($note['status']??'')==='published')self::respond(200,['data'=>$note]);
            self::respond(404,['error'=>'Note not found']);
        }
        if ($method==='GET' && $path==='/articles') {
            $articles=array_values(array_filter($this->store->read('articles'),fn($v)=>($v['status']??'')==='published'));
            usort($articles,fn($a,$b)=>strcmp($b['published_at']??'',$a['published_at']??''));
            self::respond(200,['data'=>$articles]);
        }
        if (str_starts_with($path,'/admin/')) {
            $this->authorize();
            if ($method==='GET' && $path==='/admin/status') self::respond(200,['ok'=>true,'storage'=>'JSON file collections','role'=>'editor']);
            if ($method==='GET' && $path==='/admin/import-status') {
                $chapters=$this->store->read('chapters');$exams=$this->store->read('exams');$notes=$this->store->read('notes');
                $count=static fn($items,$status)=>count(array_filter($items,static fn($v)=>($v['status']??'')===$status));
                self::respond(200,['data'=>[
                    'chapters'=>['draft'=>$count($chapters,'draft'),'published'=>$count($chapters,'published'),'total'=>count($chapters)],
                    'exams'=>['draft'=>$count($exams,'draft'),'published'=>$count($exams,'published'),'indexed'=>count($exams)],
                    'notes'=>['draft'=>$count($notes,'draft'),'published'=>$count($notes,'published'),'total'=>count($notes)],
                ]]);
            }
            // Browser-friendly single-chapter JSON import. Large collections use the offline migration manifest.
            if ($method==='POST' && $path==='/admin/chapters/import') {
                $b=self::body();
                $book=$b['book_id']??null;$sectionSlug=$b['section_slug']??null;$chapterSlug=$b['chapter_slug']??null;
                foreach([$book,$sectionSlug,$chapterSlug] as $key)if(!is_string($key)||!preg_match('/^[a-z0-9]+(?:-[a-z0-9]+)*$/D',$key))self::respond(422,['error'=>'Invalid book, section, or chapter slug']);
                $section=null;$chapterIndex=null;
                foreach($this->store->read('sections') as $candidate){
                    if(($candidate['book_id']??'')===$book && ($candidate['slug']??'')===$sectionSlug){
                        $section=$candidate;
                        foreach($candidate['chapters']??[] as $c)if(($c['slug']??'')===$chapterSlug)$chapterIndex=$c;
                    }
                }
                if(!$section||!$chapterIndex)self::respond(422,['error'=>'Chapter is not in the indexed classical library']);
                $source=$b['source_url']??'';
                if(!is_string($source)||strlen($source)>2000||!filter_var($source,FILTER_VALIDATE_URL)||parse_url($source,PHP_URL_SCHEME)!=='https')self::respond(422,['error'=>'HTTPS source URL required']);
                $passages=$b['passages']??null;
                if(!is_array($passages)||!array_is_list($passages)||count($passages)<1||count($passages)>300)self::respond(422,['error'=>'Upload 1–300 passages per chapter (offline importer supports more)']);
                $normalized=[];
                foreach($passages as $index=>$p){
                    if(!is_array($p))self::respond(422,['error'=>'Invalid passage']);
                    $ref=$p['reference']??'';$dev=$p['text_devanagari']??'';$iast=$p['text_iast']??'';
                    if(!is_string($ref)||trim($ref)===''||strlen($ref)>100||!is_string($dev)||!is_string($iast)||trim($dev.$iast)===''||strlen($dev)>40000||strlen($iast)>40000)self::respond(422,['error'=>'Missing or invalid source text at passage '.($index+1)]);
                    $translation=$p['translation_en']??'';$commentary=$p['commentary']??'';$terms=$p['key_terms']??[];
                    if(!is_string($translation)||strlen($translation)>15000||!is_string($commentary)||strlen($commentary)>120000||!is_array($terms)||!array_is_list($terms)||count($terms)>50)self::respond(422,['error'=>'Invalid commentary or terminology']);
                    $cleanTerms=[];
                    foreach($terms as $term){if(!is_array($term)||!is_string($term['term']??null)||!is_string($term['definition']??null)||strlen($term['term'])>200||strlen($term['definition'])>2000)self::respond(422,['error'=>'Invalid key term']);$cleanTerms[]=['term'=>$term['term'],'definition'=>$term['definition']];}
                    $normalized[]=['id'=>substr(hash('sha256',$book.'/'.$sectionSlug.'/'.$chapterSlug.'/'.$index.'/'.$ref),0,20),'reference'=>trim($ref),'text_devanagari'=>trim($dev),'text_iast'=>trim($iast),'translation_en'=>trim($translation),'commentary'=>trim($commentary),'key_terms'=>$cleanTerms];
                }
                $id=$book.'/'.$sectionSlug.'/'.$chapterSlug;
                $title=$b['title']??($chapterIndex['title']??null);
                if(!is_string($title)||!trim($title)||strlen($title)>240)$title='Chapter '.($chapterIndex['number']??'');
                $record=['id'=>$id,'book_id'=>$book,'section_slug'=>$sectionSlug,'chapter_slug'=>$chapterSlug,'chapter_number'=>$chapterIndex['number'],'title'=>$title,'source_url'=>$source,'passages'=>$normalized,'source_hash'=>hash('sha256',json_encode($normalized,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR)),'status'=>'draft'];
                $preserved=false;
                $this->store->mutate('chapters',static function($items)use($record,&$preserved){
                    foreach($items as $i=>$entry)if(($entry['id']??'')===$record['id']){
                        if(($entry['status']??'')==='published'){$preserved=true;return $items;}
                        $items[$i]=$record;return $items;
                    }
                    $items[]=$record;return $items;
                });
                if($preserved)self::respond(409,['error'=>'Published chapter is protected from overwrite']);
                self::respond(201,['ok'=>true,'id'=>$id,'passage_count'=>count($normalized),'status'=>'draft']);
            }
            if ($method==='GET' && $path==='/admin/chapters') {
                $items=array_map(static function($c){unset($c['passages']);return $c;},$this->store->read('chapters'));
                self::respond(200,['data'=>$items]);
            }
            if ($method==='POST' && $path==='/admin/chapters/publish') {
                $payload=self::body();$id=$payload['id']??null;
                if(!is_string($id)||!preg_match('~^[a-z0-9-]+/[a-z0-9-]+/[a-z0-9-]+$~D',$id))self::respond(422,['error'=>'Invalid chapter ID']);
                // An editor must attest to specific source and rights checks before publication.
                // This is recorded provenance, not a claim of independent scholarly peer review.
                $review=$payload['review']??null;
                if(!is_array($review)||array_is_list($review))self::respond(422,['error'=>'An editorial review record is required']);
                $reviewer=trim((string)($review['reviewer']??''));
                $edition=trim((string)($review['edition']??''));
                $notes=trim((string)($review['notes']??''));
                if(strlen($reviewer)<3||strlen($reviewer)>120||strlen($edition)<3||strlen($edition)>240||strlen($notes)>2000
                   ||($review['text_checked']??false)!==true||($review['rights_confirmed']??false)!==true)
                    self::respond(422,['error'=>'Reviewer, source edition, text check and reuse-rights confirmation are mandatory']);
                $found=false;
                $this->store->mutate('chapters',static function($items)use($id,&$found,$reviewer,$edition,$notes){
                    foreach($items as &$item) if(($item['id']??'')===$id && !empty($item['passages'])) {
                        $found=true;
                        // Keep an immutable snapshot of who attested to which imported text.
                        $item['editorial_review']=[
                            'reviewer'=>$reviewer,'edition'=>$edition,'notes'=>$notes,
                            'text_checked'=>true,'rights_confirmed'=>true,
                            'source_url'=>$item['source_url']??'','source_hash'=>$item['source_hash']??'',
                            'reviewed_at'=>gmdate('c')
                        ];
                        $item['status']='published';$item['published_at']=gmdate('c');break;
                    }
                    unset($item);return $items;
                });
                if(!$found)self::respond(404,['error'=>'Imported chapter with passages not found']);
                self::respond(200,['ok'=>true,'id'=>$id]);
            }
            if ($method==='GET' && $path==='/admin/exams') self::respond(200,['data'=>array_map(static function($e){$e['imported_count']=count($e['questions']??[]);unset($e['questions']);return $e;},$this->store->read('exams'))]);
            if ($method==='POST' && preg_match('~^/admin/exams/([a-z0-9-]+)/import$~D',$path,$m)) {
                $body=self::body();$questions=$body['questions']??null;
                if(!is_array($questions)||!array_is_list($questions)||count($questions)>250) self::respond(422,['error'=>'Provide an array of no more than 250 questions']);
                $found=false;$invalid=null;$protected=false;
                $this->store->mutate('exams',function($items)use($m,$questions,&$found,&$invalid,&$protected){
                    foreach($items as &$e)if($e['id']===$m[1]){
                        $found=true;
                        if(($e['status']??'')==='published'){$protected=true;break;}
                        if(count($questions)!==(int)$e['expected_count']){$invalid='Question total must match expected paper size';break;}
                        $ids=[];$validated=[];
                        foreach($questions as $i=>$q){
                            if(!is_array($q)||!is_string($q['question']??null)||trim($q['question'])===''||strlen($q['question'])>4000||!is_array($q['options']??null)||count($q['options'])!==4||!array_is_list($q['options'])||!is_int($q['answer']??null)||$q['answer']<0||$q['answer']>3||!is_string($q['explanation']??null)||strlen($q['explanation'])>8000){$invalid='Invalid question at index '.$i;break;}
                            if(count(array_filter($q['options'],fn($opt)=>is_string($opt)&&trim($opt)!==''&&strlen($opt)<2000))!==4){$invalid='Invalid option at index '.$i;break;}
                            $id=(string)($q['id']??($m[1].'-'.($i+1)));if(!preg_match('/^[a-z0-9-]{3,80}$/D',$id)||isset($ids[$id])){$invalid='Duplicate or invalid question id at index '.$i;break;}$ids[$id]=true;
                            $validated[]=['id'=>$id,'question'=>trim($q['question']),'options'=>array_values($q['options']),'answer'=>$q['answer'],'explanation'=>$q['explanation'],'subject'=>substr((string)($q['subject']??'General'),0,80)];
                        }
                        if($invalid===null){$e['questions']=$validated;$e['status']='draft';$e['published_count']=0;$e['imported_at']=gmdate('c');}
                        break;
                    }
                    unset($e);return $items;
                });
                if(!$found) self::respond(404,['error'=>'Exam set not found']);
                if($protected) self::respond(409,['error'=>'Published exam is protected from overwrite']);
                if($invalid!==null) self::respond(422,['error'=>$invalid]);
                self::respond(200,['ok'=>true,'status'=>'draft','imported_count'=>count($questions)]);
            }
            if ($method==='POST' && preg_match('~^/admin/exams/([a-z0-9-]+)/publish$~D',$path,$m)) {
                $found=false;$ready=false;
                $this->store->mutate('exams',function($items)use($m,&$found,&$ready){foreach($items as &$e)if($e['id']===$m[1]){$found=true;$ready=count($e['questions']??[])===(int)$e['expected_count'];if($ready){$e['status']='published';$e['published_count']=count($e['questions']);}break;}unset($e);return $items;});
                if(!$found)self::respond(404,['error'=>'Exam not found']);if(!$ready)self::respond(422,['error'=>'A complete validated paper is required']);
                self::respond(200,['ok'=>true]);
            }
            if ($method==='GET' && $path==='/admin/notes') self::respond(200,['data'=>$this->store->read('notes')]);
            if ($method==='POST' && $path==='/admin/notes') {
                $b=self::body();$title=trim((string)($b['title']??''));$body=trim((string)($b['body']??''));$subject=trim((string)($b['subject']??''));$level=trim((string)($b['level']??'BAMS'));
                if(!$title||strlen($title)>240||!$body||strlen($body)>250000||!$subject||strlen($subject)>120||!in_array($level,['BAMS','MD','MS'],true))self::respond(422,['error'=>'Invalid note fields']);
                $slug=strtolower(trim(preg_replace('/[^a-z0-9]+/i','-',$title),'-'));if(!$slug) $slug='note';
                if(!empty($b['source_url'])&&(!filter_var($b['source_url'],FILTER_VALIDATE_URL)||parse_url($b['source_url'],PHP_URL_SCHEME)!=='https')) self::respond(422,['error'=>'Note source must be a valid HTTPS URL']);
                $note=['id'=>bin2hex(random_bytes(10)),'slug'=>$slug.'-'.bin2hex(random_bytes(3)),'title'=>$title,'subject'=>$subject,'level'=>$level,'body'=>$body,'source_url'=>(string)($b['source_url']??''),'status'=>'draft','created_at'=>gmdate('c')];
                $this->store->mutate('notes',function($items)use($note){$items[]=$note;return $items;});self::respond(201,['data'=>$note]);
            }
            if ($method==='POST' && preg_match('~^/admin/notes/([a-f0-9]{20})/publish$~D',$path,$m)) {
                $found=false;$this->store->mutate('notes',function($items)use($m,&$found){foreach($items as &$x)if($x['id']===$m[1]){$found=true;$x['status']='published';$x['published_at']=gmdate('c');break;}unset($x);return $items;});
                if(!$found)self::respond(404,['error'=>'Note not found']);self::respond(200,['ok'=>true]);
            }
            if ($method==='GET' && $path==='/admin/articles') self::respond(200,['data'=>$this->store->read('articles')]);
            if ($method==='POST' && $path==='/admin/articles') {
                $body=self::body();$title=trim((string)($body['title']??''));$summary=trim((string)($body['summary']??''));
                $url=trim((string)($body['source_url']??''));$category=(string)($body['category']??'Research');
                $validUrl=filter_var($url,FILTER_VALIDATE_URL) && parse_url($url,PHP_URL_SCHEME)==='https';
                if ((function_exists('mb_strlen')?mb_strlen($title):strlen($title))>180 || (function_exists('mb_strlen')?mb_strlen($summary):strlen($summary))>700 || !$title || !$validUrl || !in_array($category,['Research','Learning','Classical literature'],true)) self::respond(422,['error'=>'Invalid title, summary, source URL or category']);
                $item=['id'=>bin2hex(random_bytes(12)),'title'=>$title,'summary'=>$summary,'source_url'=>$url,'category'=>$category,'status'=>'draft','created_at'=>gmdate('c'),'published_at'=>''];
                $this->store->mutate('articles',function($items)use($item){$items[]=$item;return $items;});
                self::respond(201,['data'=>$item]);
            }
            if ($method==='POST' && preg_match('~^/admin/articles/([a-f0-9]{24})/publish$~D',$path,$m)) {
                $found=false;
                $this->store->mutate('articles',function($items)use($m,&$found){foreach($items as &$item){if(($item['id']??'')===$m[1]){$found=true;$item['status']='published';$item['published_at']=gmdate('c');}}unset($item);return $items;});
                if (!$found) self::respond(404,['error'=>'Article not found']);
                self::respond(200,['ok'=>true]);
            }
        }
        self::respond(404,['error'=>'Route not found']);
    }
}
