// api.js
(function() {
    MyApp.api = {
        deleteEntry: function(id) {
            const password = prompt('请输入管理员密码：');
            if (!password) return;

            fetch('delete.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `id=${id}&password=${encodeURIComponent(password)}`
            })
            .then(response => response.text())
            .then(result => {
                if (result === 'OK') {
                    MyApp.coreInit(); // 刷新列表
                } else {
                    alert('删除失败: ' + result);
                }
            });
        },
        toggleHidden:function (id, isHidden) {
            const password = prompt('请输入管理员密码：');
            if (!password) return;

            fetch('hide.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `id=${id}&hidden=${!isHidden}&password=${encodeURIComponent(password)}`
            }).then(() =>  MyApp.coreInit());
        },
        togglePin:function (id, isPinned) {
            const password = prompt('请输入管理员密码：');
            if (!password) return;

            fetch('pin.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `id=${id}&pinned=${!isPinned}&password=${encodeURIComponent(password)}`
            }).then(() =>  MyApp.coreInit());
        }
    };
})();
