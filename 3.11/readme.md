此文件版本为安全加强版，放至htdocs文件夹下即可食用

修改密码请分别修改delete.php、hide.php、pin.php中的密码，默认密码是12203

防止访问其余文件请在.htaccess文件里添加如下内容：
# 阻止直接访问 data.json
<FilesMatch "12203data.json">
    Order Allow,Deny
    Deny from all
</FilesMatch>
# 阻止直接访问.js文件
<FilesMatch "(core|helper|api)\.js$">
    Require all denied
</FilesMatch>


# 允许访问 proxy.php
<Files "proxy.php">
    Order Allow,Deny
    Allow from all
</Files>