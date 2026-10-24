<?php
declare(strict_types=1);
require_once __DIR__.'/../server/src/StoreInterface.php';
require_once __DIR__.'/../server/src/FileStore.php';
use AyurSutra\Support\FileStore;
$temp=sys_get_temp_dir().'/ayursutra-test-'.bin2hex(random_bytes(6));
try{
  $store=new FileStore($temp);
  assert($store->read('sample')===[]);
  $saved=$store->mutate('sample',fn($items)=>[...$items,['id'=>'first']]);
  if(count($saved)!==1||$store->read('sample')[0]['id']!=='first')throw new Exception('Storage test failed');
  try{$store->read('../unsafe');throw new Exception('Path validation failed');}catch(RuntimeException $expected){}
  echo "PASS: atomic JSON storage, read, and path validation\n";
}finally{
  foreach(glob($temp.'/*')?:[] as $f)unlink($f);
  if(is_dir($temp))rmdir($temp);
}
