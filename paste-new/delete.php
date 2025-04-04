<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

header('Content-Type: text/plain');
$dataFile = __DIR__ . '/12203data.json';


// 密码验证（示例密码：12203）
define('ADMIN_PWD', password_hash('zhouzhou12203', PASSWORD_DEFAULT));
if (!password_verify($_POST['password'], ADMIN_PWD)) {
    http_response_code(401);
    exit('错误：管理员密码错误');
}

// 获取要删除的ID
$idToDelete = $_POST['id'] ?? '';
if (empty($idToDelete)) {
    http_response_code(400);
    exit('错误：缺少ID参数');
}

// 加载并过滤数据
$entries = json_decode(file_get_contents($dataFile), true) ?? [];
$newEntries = array_values(array_filter($entries, fn($e) => $e['id'] !== $idToDelete));

// 保存数据
if (file_put_contents($dataFile, json_encode($newEntries, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE))) {
    echo 'OK';
} else {
    http_response_code(500);
    exit('错误：文件写入失败');
}
