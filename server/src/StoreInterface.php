<?php
declare(strict_types=1);
namespace AyurSutra\Support;

/** Persistence contract: JSON today, MariaDB adapter later. */
interface StoreInterface {
    public function read(string $collection): array;
    public function mutate(string $collection, callable $fn): array;
}
