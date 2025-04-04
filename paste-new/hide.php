<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

header('Content-Type: text/plain');
$dataFile = __DIR__ . '/12203data.json';


// 密码验证（复用删除密码）
$password = $_POST['password'] ?? '';
if ($password !== 'zhouzhou12203') {
    http_response_code(401);
    exit('错误：管理员密码错误');
}

// 获取参数
$id = $_POST['id'] ?? '';
$hidden = filter_var($_POST['hidden'], FILTER_VALIDATE_BOOLEAN);

// 更新数据
$entries = json_decode(file_get_contents($dataFile), true) ?? [];
foreach ($entries as &$entry) {
    if ($entry['id'] === $id) {
        $entry['hidden'] = $hidden;
        break;
    }
}

file_put_contents($dataFile, json_encode($entries, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
echo 'OK';
