<?php
declare(strict_types=1);
namespace AyurSutra;

/** Minimal event-only operational record. Does not log token, request body, or answer keys. */
final class AuditTrail {
    private readonly string $path;
    public function __construct(string $storage) {
        $directory=rtrim($storage,'/').'/private/audit';
        if (!is_dir($directory)&&!mkdir($directory,0750,true)&&!is_dir($directory))
            throw new \RuntimeException('Private audit directory unavailable');
        $this->path=$directory.'/events.jsonl';
    }
    public function append(array $identity,string $method,string $path,int $status): void {
        $event=[
            'at'=>gmdate('c'),'actor'=>$identity['id'],'role'=>$identity['role'],
            'method'=>$method,'path'=>$path,'status'=>$status,
        ];
        $encoded=json_encode($event,JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES)."\n";
        $handle=fopen($this->path,'ab');
        if($handle===false||!flock($handle,LOCK_EX))throw new \RuntimeException('Audit storage unavailable');
        try {
            $length=strlen($encoded);
            if(fwrite($handle,$encoded)!==$length||!fflush($handle))throw new \RuntimeException('Audit write failed');
            @chmod($this->path,0640);
        } finally {flock($handle,LOCK_UN);fclose($handle);}
    }
    public function latest(int $limit=50): array {
        if(!is_file($this->path))return [];
        $size=filesize($this->path);
        if($size===false)return [];
        $handle=fopen($this->path,'rb');
        if($handle===false)throw new \RuntimeException('Audit read failed');
        try {
            $offset=max(0,$size-262144);
            if($offset>0)fseek($handle,$offset);
            $text=stream_get_contents($handle);
        } finally {fclose($handle);}
        if($text===false)return [];
        $lines=explode("\n",trim($text));
        if($offset>0)array_shift($lines); // Discard a partial initial line.
        $result=[];
        foreach(array_slice($lines,-min(100,max(1,$limit))) as $line){
            $row=json_decode($line,true);
            if(is_array($row))$result[]=$row;
        }
        return array_reverse($result);
    }
}
