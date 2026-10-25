<?php
declare(strict_types=1);
namespace AyurSutra;

/** Shared-secret identity resolver; role configuration never reaches the frontend. */
final class AdminIdentity {
    public const LEVELS = ['viewer'=>1,'editor'=>2,'publisher'=>3,'admin'=>4];

    /** New deployments set AYURSUTRA_ADMIN_USERS_JSON to a JSON array of id, role, sha256(token). */
    public static function resolve(string $bearer,string $legacyToken): ?array {
        if (strlen($bearer)<32 || strlen($bearer)>512) return null;
        $config=getenv('AYURSUTRA_ADMIN_USERS_JSON');
        if (is_string($config) && trim($config)!=='') {
            $users=json_decode($config,true);
            if(!is_array($users)||!array_is_list($users)||count($users)>100)
                throw new \RuntimeException('Invalid admin credentials configuration');
            $digest=hash('sha256',$bearer);
            $seen=[];
            foreach($users as $user) {
                $id=$user['id']??null;$role=$user['role']??null;$hash=$user['sha256']??null;
                if(!is_string($id)||preg_match('/^[a-zA-Z0-9_-]{3,64}$/D',$id)!==1||isset($seen[$id])||
                   !is_string($role)||!isset(self::LEVELS[$role])||!is_string($hash)||preg_match('/^[a-f0-9]{64}$/D',$hash)!==1)
                    throw new \RuntimeException('Invalid admin account');
                $seen[$id]=true;
                if(hash_equals($hash,$digest))return ['id'=>$id,'role'=>$role];
            }
            return null; // Reject legacy token whenever named credentials are configured.
        }
        if(strlen($legacyToken)>=32 && hash_equals($legacyToken,$bearer))
            return ['id'=>'legacy-owner','role'=>'admin'];
        return null;
    }
}
