<?php
declare(strict_types=1);
require_once __DIR__.'/../src/StoreInterface.php';
require_once __DIR__.'/../src/FileStore.php';
require_once __DIR__.'/../src/Api.php';
use AyurSutra\Api;
use AyurSutra\Support\FileStore;
// Configure through web-server environment, never frontend files or client-side JavaScript.
$token = getenv('AYURSUTRA_ADMIN_TOKEN') ?: '';
$storage = getenv('AYURSUTRA_STORAGE_PATH') ?: __DIR__.'/../storage';
(new Api(new FileStore($storage), $token))->run();
