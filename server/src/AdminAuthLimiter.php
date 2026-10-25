<?php
declare(strict_types=1);
namespace AyurSutra;

/** Atomic, per-client failure throttle; store under private server storage. */
final class AdminAuthLimiter {
    private const WINDOW=900; // 15 minutes
    private const MAX_FAILURES=10;
    public function __construct(private readonly string $directory) {}
    /** Returns HTTP status 200, 401 or 429. Never trusts X-Forwarded-For. */
    public function evaluate(string $remoteAddress,bool $validToken): int {
        if(!is_dir($this->directory)&&!mkdir($this->directory,0750,true)&&!is_dir($this->directory)){
            throw new \RuntimeException('Cannot create auth limiter storage');
        }
        $path=$this->directory.'/'.hash('sha256',$remoteAddress).'.json';
        $handle=fopen($path,'c+');
        if($handle===false||!flock($handle,LOCK_EX))throw new \RuntimeException('Cannot lock auth limiter');
        try {
            rewind($handle);
            $old=stream_get_contents($handle);
            $state=$old?json_decode($old,true):null;
            $now=time();
            $begin=is_array($state)?(int)($state['window_started']??0):0;
            $failures=is_array($state)?(int)($state['failures']??0):0;
            if($begin<=0||$now-$begin>=self::WINDOW){$begin=$now;$failures=0;}
            if($failures>=self::MAX_FAILURES)return 429;
            if($validToken){$failures=0;$begin=$now;}else{$failures++;}
            $serialized=json_encode(['window_started'=>$begin,'failures'=>$failures],JSON_THROW_ON_ERROR);
            rewind($handle);if(!ftruncate($handle,0)||fwrite($handle,$serialized)===false||!fflush($handle)){
                throw new \RuntimeException('Cannot update auth limiter');
            }
            @chmod($path,0640);
            return $validToken?200:401;
        } finally {flock($handle,LOCK_UN);fclose($handle);}
    }
}
