<?php
header('Content-Type: application/json');

$dataFile = __DIR__ . '/12203data.json';
$entryId = $_GET['id'] ?? '';

if (empty($entryId)) {
    http_response_code(400);
    exit(json_encode(['error' => '缺少 ID 参数']));
}

$entries = json_decode(file_get_contents($dataFile), true) ?? [];
$entry = null;

foreach ($entries as $e) {
    if ($e['id'] === $entryId) {
        $entry = $e;
        break;
    }
}

if (!$entry) {
    http_response_code(404);
    exit(json_encode(['error' => '未找到条目']));
}

if ($entry['hidden']) {
    echo json_encode(['text' => '']); // 内容隐藏时返回空字符串，禁止复制
} else {
    echo json_encode(['text' => $entry['text']]); // 未隐藏时返回原文
}
