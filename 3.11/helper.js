// helper.js
(function() {
    MyApp.helper = {
        toggleNote: function(element) {
            const note = element.querySelector('.entry-note');
            note.style.display = note.style.display === 'none' ? 'block' : 'none';
        },
        copyText:function (button) {
            const isHidden = button.dataset.hidden === 'true';
            const textToCopy = isHidden ?
                '*** 内容已隐藏 ***' :
                button.dataset.text.replace(/&quot;/g, '"');

            const textarea = document.createElement('textarea');
            textarea.value = textToCopy;
            textarea.style.position = 'fixed';
            document.body.appendChild(textarea);

            if (navigator.clipboard) {
                navigator.clipboard.writeText(textarea.value)
                    .then(() => MyApp.helper.showAlert('✅ 已复制到剪贴板'))
                    .catch(() => MyApp.helper.showAlert('❌ 复制失败 (权限被拒绝)'));
            } else {
                textarea.select();
                try {
                    const success = document.execCommand('copy');
                    MyApp.helper.showAlert(success ? '✅ 已复制！' : '❌ 复制失败');
                } catch {
                    MyApp.helper.showAlert('❌ 复制操作不被支持');
                }
            }

            document.body.removeChild(textarea);
        },
        showAlert:function (msg) {
            const alertBox = document.createElement('div');
            alertBox.style = 'position:fixed; top:20px; right:20px; padding:10px; background:#4CAF50; color:white; border-radius:5px;';
            alertBox.textContent = msg;
            document.body.appendChild(alertBox);
            setTimeout(() => alertBox.remove(), 2000);
        }
    }
})();
