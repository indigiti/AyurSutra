<?php
// Place this file at public_html/api/index.php; backend must be outside public_html.
declare(strict_types=1);
$root = getenv('AYURSUTRA_BACKEND_ROOT');
if (!$root || !is_dir($root.'/src')) { http_response_code(503); exit('API backend not configured'); }
require_once $root.'/src/StoreInterface.php';
require_once $root.'/src/FileStore.php';
require_once $root.'/src/CorpusStore.php';
require_once $root.'/src/SearchService.php';
require_once $root.'/src/Api.php';
(new \AyurSutra\Api(new \AyurSutra\Support\FileStore(getenv('AYURSUTRA_STORAGE_PATH') ?: $root.'/storage'), getenv('AYURSUTRA_ADMIN_TOKEN') ?: ''))->run();
