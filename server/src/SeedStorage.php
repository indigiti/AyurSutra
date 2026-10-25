<?php
declare(strict_types=1);
namespace AyurSutra;

final class SeedStorage {
    private const COLLECTIONS=['articles','books','chapters','exams','notes','sections','verses'];

    /** Initializes private runtime data on first request without overwriting any existing collection. */
    public static function ensure(string $seedDirectory,string $storageDirectory): void {
        if(!is_dir($seedDirectory))throw new \RuntimeException('Missing private application seed bundle');
        $base=dirname($storageDirectory);
        if(!is_dir($base)&&!mkdir($base,0750,true)&&!is_dir($base))
            throw new \RuntimeException('Cannot create private application runtime');
        $lock=fopen($base.'/.bootstrap.lock','c+');
        if(!$lock||!flock($lock,LOCK_EX))throw new \RuntimeException('Runtime initialization locked');
        try{
            if(!is_dir($storageDirectory)&&!mkdir($storageDirectory,0750,true)&&!is_dir($storageDirectory))
                throw new \RuntimeException('Private storage initialization failed');
            foreach(self::COLLECTIONS as $collection){
                $target=$storageDirectory.'/'.$collection.'.json';
                if(is_file($target))continue; // Never replace editorial data on deploy or rollback.
                $source=$seedDirectory.'/'.$collection.'.json';
                if(!is_file($source))throw new \RuntimeException('Missing application collection seed');
                $staged=tempnam($storageDirectory,'.seed-');
                if($staged===false)throw new \RuntimeException('Cannot stage private collection seed');
                try{
                    if(!copy($source,$staged)||!chmod($staged,0640)||!rename($staged,$target))
                        throw new \RuntimeException('Cannot create private collection');
                }finally{if(is_file($staged))unlink($staged);}
            }
        }finally{flock($lock,LOCK_UN);fclose($lock);}
    }
}
