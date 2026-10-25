<?php
// DigiOps layout: <app-home>/public_html/ayursutra/api/index.php
//                 <app-home>/private_html/ayursutra/{src,seeds,runtime}/
declare(strict_types=1);
$base=dirname(__DIR__,3);
$root=realpath($base.'/private_html/ayursutra');
if($root===false||!is_dir($root.'/src')||!is_dir($root.'/seeds')){
    http_response_code(503);header('Content-Type: application/json');
    echo '{"error":"Private AyurSutra backend unavailable"}';exit;
}
require_once $root.'/src/StoreInterface.php';
require_once $root.'/src/FileStore.php';
require_once $root.'/src/CorpusStore.php';
require_once $root.'/src/SearchService.php';
require_once $root.'/src/AdminAuthLimiter.php';
require_once $root.'/src/AdminIdentity.php';
require_once $root.'/src/AuditTrail.php';
require_once $root.'/src/SeedStorage.php';
require_once $root.'/src/Api.php';
$storage=$root.'/runtime/storage';
try{\AyurSutra\SeedStorage::ensure($root.'/seeds',$storage);}
catch(\Throwable $error){
    error_log('AyurSutra storage initialization: '.$error->getMessage());
    http_response_code(503);header('Content-Type: application/json');
    echo '{"error":"Private application storage unavailable"}';exit;
}
$_SERVER['AYURSUTRA_BASE_PATH']='/ayursutra';
(new \AyurSutra\Api(
    new \AyurSutra\Support\FileStore($storage),
    getenv('AYURSUTRA_ADMIN_TOKEN') ?: '',
    $storage,
    $root.'/seeds/corpus'
))->run();
