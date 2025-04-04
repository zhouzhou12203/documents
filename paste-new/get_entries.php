<?php
header('Content-Type: application/json');

$dataFile = __DIR__ . '/12203data.json';
$entries = json_decode(file_get_contents($dataFile), true) ?? [];

$result = array_map(function($entry) {
    if ($entry['hidden']) {
        return [
            'id' => $entry['id'],
            'text' => $entry['text'], // 返回原始文本
            'note' => $entry['note'], // 返回备注
            'displayText' => '*** 内容已隐藏 ***',
            'hidden' => true,
            'pinned' => $entry['pinned']
        ];
    } else {
        return [
            'id' => $entry['id'],
            'text' => $entry['text'], // 返回原始文本
            'note' => $entry['note'], // 返回备注
            'displayText' => $entry['text'],
            'hidden' => false,
            'pinned' => $entry['pinned']
        ];
    }
}, $entries);

echo json_encode($result, JSON_UNESCAPED_UNICODE);
