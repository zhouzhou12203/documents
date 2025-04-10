<?php
$allowedFiles = ['core.js', 'helper.js', 'api.js']; // 允许加载的 JS 文件
$file = $_GET['file'] ?? ''; // 获取文件名

if (!in_array($file, $allowedFiles)) {
    http_response_code(403);
    exit('Access denied');
}

$filePath = __DIR__ . '/' . $file; // 构建文件路径
if (!file_exists($filePath)) {
    http_response_code(404);
    exit('File not found');
}

header('Content-Type: application/javascript');
readfile($filePath);
?>
