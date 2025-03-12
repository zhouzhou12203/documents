<?php
date_default_timezone_set('Asia/Shanghai'); // 根据你的实际时区调整
require_once 'RateLimiter.php';

// 获取客户端真实IP
function getClientIP() {
    $trustedProxies = ['10.0.0.0/8']; // 根据实际代理配置
    
    $ip = $_SERVER['REMOTE_ADDR'];
    
    // 检测是否为IPv6地址
    $isIPv6 = strpos($ip, ':') !== false;
    
    if (isset($_SERVER['HTTP_X_FORWARDED_FOR']) && 
        in_array($ip, $trustedProxies)) {
        $ips = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
        $ip = trim(end($ips));
        $isIPv6 = strpos($ip, ':') !== false;
    }
    
    // 尝试获取IPv4地址
    $ipv4 = filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4);
    if (!$ipv4) {
        $ipv4 = '0.0.0.0';
    }
    
    // 尝试获取IPv6地址
    $ipv6 = filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV6);
    if (!$ipv6) {
        $ipv6 = '::';
    }
    
    return [
        'ipv4' => $ipv4,
        'ipv6' => $ipv6
    ];
}


$clientIP = getClientIP();

// 准备频率限制缓存目录
$cacheDir = __DIR__.'/ip_cache/';
if (!is_dir($cacheDir)) {
    mkdir($cacheDir, 0755, true);
}

// 执行频率限制检查（立即退出模式）
try {
    $limiter = new RateLimiter($ip, $cacheDir, 5, 60); // 60秒内最多5次
    if (!$limiter->check()) {
        http_response_code(429);
        exit('请求过于频繁，请等待1分钟后重试');
    }
} catch (Exception $e) {
    error_log("频率限制错误: ".$e->getMessage());
    http_response_code(500);
    exit('系统限流服务暂时不可用');
}

// 启用错误提示（部署时可关闭）
error_reporting(E_ALL);
ini_set('display_errors', 1);

header('Content-Type: text/plain'); // 设置响应类型

$dataFile = __DIR__ . '/12203data.json'; // 数据文件路径

// 获取并清理输入数据
$now = new DateTime('now', new DateTimeZone('Asia/Shanghai'));
$text = isset($_POST['text']) ? trim($_POST['text']) : '';
$note = isset($_POST['note']) ? trim($_POST['note']) : '';
$pinned = isset($_POST['pinned']) ? filter_var($_POST['pinned'], FILTER_VALIDATE_BOOLEAN) : false;

// 验证必填字段
if (empty($text)) {
    http_response_code(400);
    exit('错误：文本内容不能为空');
}

// 加载现有数据
$entries = [];
if (file_exists($dataFile)) {
    $fileContent = file_get_contents($dataFile);
    $entries = json_decode($fileContent, true) ?? [];
}

// 添加新条目
$newEntry = [
    'id' => uniqid(),
    'text' => htmlspecialchars($text, ENT_QUOTES, 'UTF-8'),
    'note' => htmlspecialchars($note, ENT_QUOTES, 'UTF-8'),
    'pinned' => $pinned,
    'time' => $now->format('Y-m-d H:i:s'),
    'hidden' => false, // 新增hidden字段
    'ipv4' => $clientIP['ipv4'],
    'ipv6' => $clientIP['ipv6']
];

array_push($entries, $newEntry);

// 保存数据
try {
    $result = file_put_contents(
        $dataFile,
        json_encode($entries, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)
    );
    
    if ($result === false) {
        throw new Exception('文件写入失败');
    }
    
    echo 'OK'; // 返回成功响应
} catch (Exception $e) {
    http_response_code(500);
    exit('服务器错误：'.$e->getMessage());
}

// 添加输入验证
$maxLength = 2000;
if (mb_strlen($text) > $maxLength) {
    http_response_code(413);
    exit("文本长度超过{$maxLength}字符限制");
}

if (preg_match('/<script/i', $text)) {
    http_response_code(400);
    exit("包含非法内容");
}
