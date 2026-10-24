<?php
declare(strict_types=1);
namespace AyurSutra;
use AyurSutra\Support\StoreInterface;
use Throwable;

final class Api {
    public function __construct(private readonly StoreInterface $store, private readonly string $adminToken) {}
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
        if ($raw===false || strlen($raw)>32768) self::respond(413, ['error'=>'Request too large']);
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
        if ($method==='GET' && preg_match('~^/books/([a-z0-9-]+)/verses$~D',$path,$m)) {
            $verses=array_values(array_filter($this->store->read('verses'),fn($v)=>($v['book_id']??'')===$m[1] && ($v['reviewed']??false)===true && (!array_key_exists('published',$v) || $v['published']===true)));
            $total=count($verses);
            $offset=max(0, (int)($_GET['offset']??0));$limit=min(250,max(1,(int)($_GET['limit']??100)));
            self::respond(200,['data'=>array_slice($verses,$offset,$limit),'total'=>$total,'limit'=>$limit,'offset'=>$offset]);
        }
        if ($method==='GET' && $path==='/articles') {
            $articles=array_values(array_filter($this->store->read('articles'),fn($v)=>($v['status']??'')==='published'));
            usort($articles,fn($a,$b)=>strcmp($b['published_at']??'',$a['published_at']??''));
            self::respond(200,['data'=>$articles]);
        }
        if (str_starts_with($path,'/admin/')) {
            $this->authorize();
            if ($method==='GET' && $path==='/admin/status') self::respond(200,['ok'=>true,'storage'=>'JSON file collections','role'=>'editor']);
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
