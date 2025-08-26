# 域名扫描器

一个强大的域名可用性检查工具，使用 Go 语言编写。

## 快速开始

### 使用预编译二进制文件
```bash
./domain-scanner [选项]
```

## 基本选项

- `-l int`: 域名长度（默认：3）
- `-s string`: 域名后缀（默认：.li）
- `-p string`: 域名模式：
  - `d`: 纯数字（例如：123.li）
  - `D`: 纯字母（例如：abc.li）
  - `a`: 字母数字混合（例如：a1b.li）
- `-workers int`: 并发工作线程数（默认：10）
- `-delay int`: 查询间隔（毫秒）（默认：1000）
- `-config string`: 配置文件路径（默认：config.toml）
