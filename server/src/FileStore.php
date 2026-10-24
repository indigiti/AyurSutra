<?php
declare(strict_types=1);
namespace AyurSutra\Support;
use RuntimeException;
final class FileStore implements StoreInterface {
    public function __construct(private readonly string $basePath) {}
    private function file(string $collection): string {
        if (!preg_match('/^[a-z][a-z0-9_-]*$/D', $collection)) throw new RuntimeException('Invalid collection');
        if (!is_dir($this->basePath)) mkdir($this->basePath, 0750, true);
        return rtrim($this->basePath, '/').'/'.$collection.'.json';
    }
    public function read(string $collection): array {
        $file = $this->file($collection);
        if (!is_file($file)) return [];
        $text = file_get_contents($file);
        if ($text === false) throw new RuntimeException('Cannot read collection');
        $json = json_decode($text, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($json) || !array_is_list($json)) throw new RuntimeException('Invalid JSON collection');
        return $json;
    }
    public function mutate(string $collection, callable $fn): array {
        $file = $this->file($collection);
        $lock = fopen($file.'.lock', 'c');
        if (!$lock || !flock($lock, LOCK_EX)) throw new RuntimeException('Storage busy');
        try {
            $entries = $this->read($collection);
            $result = $fn($entries);
            if (!is_array($result) || !array_is_list($result)) throw new RuntimeException('Invalid collection update');
            $temp = tempnam($this->basePath, '.atomic-');
            if (!$temp) throw new RuntimeException('Cannot create temporary file');
            try {
                $encoded = json_encode($result, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
                if (file_put_contents($temp, $encoded."\n") === false) throw new RuntimeException('Cannot save file');
                chmod($temp, 0640);
                if (!rename($temp, $file)) throw new RuntimeException('Cannot replace file');
            } finally { if (is_file($temp)) unlink($temp); }
            return $result;
        } finally { flock($lock, LOCK_UN); fclose($lock); }
    }
}
