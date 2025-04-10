// core.js
(function() {
    // 私有变量
    var dataFile = '12203data.json'; // 避免直接暴露
    var entriesDiv = document.getElementById('entries');
    var newText = document.getElementById('new-text');
    var newNote = document.getElementById('new-note');

    // loadEntries 加载条目
    function loadEntries() {
        fetch('proxy.php')
            .then(res => res.json())
            .then(data => {
                const sorted = data.sort((a, b) => {
                    if (a.pinned === b.pinned) {
                        return new Date(b.time) - new Date(a.time);
                    }
                    return a.pinned ? -1 : 1;
                });
                entriesDiv.innerHTML = sorted.map(entry => {
                     const isHidden = entry.hidden === true;
                     const textToDisplay = isHidden ? '*** 内容已隐藏 ***' : (entry.text || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    return `
                    <div class="entry ${entry.pinned ? 'pinned' : ''}"
                         data-id="${entry.id}"
                         onclick="MyApp.helper.toggleNote(this)">
                        <div class="entry-text ${entry.hidden ? 'hidden-text' : ''}">
                            ${textToDisplay}
                        </div>
                        <button class="copy-btn"
                                data-text="${(entry.text || '').replace(/"/g, '&quot;')}"
                                data-hidden="${isHidden}"
                                onclick="MyApp.helper.copyText(this)">复制
                        </button>
                        <button class="hide-btn" onclick="MyApp.api.toggleHidden('${entry.id}', ${entry.hidden})">
                            ${entry.hidden ? '取消隐藏' : '隐藏'}
                        </button>
                        <button class="pin-btn" onclick="MyApp.api.togglePin('${entry.id}', ${entry.pinned})">
                            ${entry.pinned ? '取消置顶' : '置顶'}
                        </button>
                        <button class="delete-btn" onclick="MyApp.api.deleteEntry('${entry.id}')">🗑️</button>
                        ${entry.note ? `<div class="entry-note">备注：${entry.note}</div>` : ''}
                    </div>
                `}).join('');
            });
    }

    // 保存条目
    function saveEntry() {
        const text = newText.value.trim();
        const note = newNote.value.trim();
        if (!text) return alert('文本内容不能为空');

        fetch('save.php', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: `text=${encodeURIComponent(text)}&note=${encodeURIComponent(note)}`
        }).then(() => {
            newText.value = '';
            newNote.value = '';
            loadEntries();
        });
    }
    MyApp.coreInit = function () {
        loadEntries();
    }
    window.saveEntry = saveEntry; // 暴露给 index.html
})();
