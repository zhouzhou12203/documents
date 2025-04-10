<?php
class RateLimiter {
    private $cachePath;
    private $maxRequests;
    private $period;
    private $ip;

    public function __construct($ip, $cacheDir, $maxRequests, $period) {
        $this->ip = $ip;
        $this->cachePath = rtrim($cacheDir, '/').'/'.md5($ip);
        $this->maxRequests = $maxRequests;
        $this->period = $period;
    }

    public function check() {
        $now = time();
        $data = ['count' => 1, 'time' => $now];

        clearstatcache(); // 清除文件状态缓存
        if (file_exists($this->cachePath)) {
            $content = file_get_contents($this->cachePath);
            $file = json_decode($content, true) ?? [];
            
            if ($file && ($now - $file['time'] < $this->period)) {
                if ($file['count'] >= $this->maxRequests) {
                    return false; // 直接拒绝
                }
                $data['count'] = $file['count'] + 1;
            }
        }

        // 原子化写入操作
        if (!file_put_contents($this->cachePath, json_encode($data), LOCK_EX)) {
            error_log("频率限制器写入失败: ".$this->cachePath);
            return false; // 写入失败时保守拒绝
        }
        
        return $data['count'] <= $this->maxRequests;
    }
}