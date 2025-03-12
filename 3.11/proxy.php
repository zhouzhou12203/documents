<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json');

$dataFile = '12203data.json';
$entries = json_decode(file_get_contents($dataFile), true) ?? [];

// 过滤掉隐藏条目的真实文本，并移除 time, ipv4, ipv6 字段
$filteredEntries = array_map(function ($entry) {
    if ($entry['hidden']) {
        $entry['text'] = ''; //  隐藏 text 字段
    }

    // 移除不需要的字段
    
    //移除pinned和hidden会导致置顶和隐藏功能出现问题
    //unset($entry['time']);
    unset($entry['id']);
    unset($entry['ipv4']);
    unset($entry['ipv6']);


    return $entry;
}, $entries);

echo json_encode($filteredEntries, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
exit;
?>
