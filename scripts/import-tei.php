<?php
/** Stages passages from a user-supplied, properly licensed SARIT TEI XML edition.
 * Does NOT publish or silently flatten scholarly metadata. Inspect staged output before approval.
 */
declare(strict_types=1);
if(PHP_SAPI!=='cli'){http_response_code(403);exit;}
if(!class_exists(DOMDocument::class)){fwrite(STDERR,"PHP DOM/XML extension required\n");exit(2);}
$registry=json_decode(file_get_contents(__DIR__.'/../docs/sources.json'),true,512,JSON_THROW_ON_ERROR);
if(($argc??0)!==3){fwrite(STDERR,"Usage: php scripts/import-tei.php <registered-source-id> <local-tei.xml>\n");exit(2);}
[$script,$sourceId,$file]=$argv;
$entry=null;foreach($registry as $source){if(($source['id']??'')===$sourceId){$entry=$source;break;}}
if(!$entry || $entry['format']!=='TEI XML'){fwrite(STDERR,"Source ID not registered for TEI import\n");exit(2);}
if(!is_readable($file)||filesize($file)>30*1024*1024){fwrite(STDERR,"Readable TEI file up to 30 MB required\n");exit(2);}
$xml=file_get_contents($file);if(stripos($xml,'<!DOCTYPE')!==false){fwrite(STDERR,"DTD is not permitted\n");exit(2);}
libxml_use_internal_errors(true);
$dom=new DOMDocument('1.0','UTF-8');
if(!$dom->loadXML($xml,LIBXML_NONET|LIBXML_COMPACT)){fwrite(STDERR,"Invalid TEI XML\n");exit(2);}
$xpath=new DOMXPath($dom);$xpath->registerNamespace('t','http://www.tei-c.org/ns/1.0');
if($xpath->query('/t:TEI/t:text/t:body')->length===0){fwrite(STDERR,"No TEI text body found\n");exit(2);}
$nodes=$xpath->query('//t:body//t:lg[not(ancestor::t:note)] | //t:body//t:p[not(ancestor::t:lg) and not(ancestor::t:note)]');
$passages=[];$ordinal=0;
foreach($nodes as $node){
 $clone=$node->cloneNode(true);
 if($clone instanceof DOMElement){
  $remove=[];foreach($clone->getElementsByTagNameNS('http://www.tei-c.org/ns/1.0','note') as $note)$remove[]=$note;
  foreach($remove as $note)$note->parentNode?->removeChild($note);
 }
 $text=trim(preg_replace('/\s+/u',' ',(string)$clone->textContent));if(mb_strlen($text)<5)continue;
 $division=[];$parent=$node->parentNode;
 while($parent instanceof DOMElement){if($parent->localName==='div'){$division[]=['type'=>$parent->getAttribute('type'),'n'=>$parent->getAttribute('n'),'id'=>$parent->getAttribute('xml:id')];}$parent=$parent->parentNode;}
 $division=array_reverse($division);$ordinal++;
 $passages[]=['id'=>$sourceId.'-'.str_pad((string)$ordinal,6,'0',STR_PAD_LEFT),'book_id'=>$entry['book_id'],'source_id'=>$sourceId,'sequence'=>$ordinal,'edition_path'=>$division,'reference'=>$node->getAttribute('n')?:null,'kind'=>$node->localName==='lg'?'verse_group':'prose','text_iast'=>$text,'reviewed'=>false,'published'=>false];
}
if(count($passages)<5){fwrite(STDERR,"Not enough text units; examine XML markup\n");exit(2);}
$stage=__DIR__.'/../server/storage/staging';if(!is_dir($stage))mkdir($stage,0750,true);
$out=$stage.'/'.$sourceId.'-'.gmdate('Ymd-His').'.json';
file_put_contents($out,json_encode(['source'=>$entry,'sha256'=>hash_file('sha256',$file),'imported_at'=>gmdate('c'),'passage_count'=>count($passages),'review_required'=>true,'passages'=>$passages],JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR));
chmod($out,0640);
echo "Staged ".count($passages)." text units to $out (not publicly published)\n";
