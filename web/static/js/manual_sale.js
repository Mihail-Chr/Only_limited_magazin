(function () {
    const form = document.getElementById('manual-sale-form');
    const search = document.getElementById('product-search');
    const select = document.getElementById('product-select');
    const qty = document.getElementById('quantity');
    const stockHint = document.getElementById('stock-hint');
    const alertBox = document.getElementById('alert-box');
    const toggleNotes = document.getElementById('toggle-notes');
    const notes = document.getElementById('notes');

    // Поиск по названию: фильтруем options
    search.addEventListener('input', function () {
        const q = this.value.toLowerCase();
        for (const opt of select.options) {
            if (!opt.value) continue;
            const text = opt.textContent.toLowerCase();
            opt.hidden = q && !text.includes(q);
        }
    });

    // При выборе товара — показать доступный остаток и max для quantity
    select.addEventListener('change', function () {
        const opt = this.options[this.selectedIndex];
        const stock = opt.dataset.stock ? parseInt(opt.dataset.stock, 10) : 0;
        if (opt.value) {
            stockHint.textContent = `Доступно: ${stock}`;
            qty.max = stock;
            if (parseInt(qty.value, 10) > stock) qty.value = stock;
        } else {
            stockHint.textContent = '';
            qty.removeAttribute('max');
        }
    });

    function applyFilters() {
        const query = document.getElementById('search-input').value.toLowerCase().trim();
        const platformFilter = document.getElementById('platform-filter').value;

        document.querySelectorAll('#seller-table tbody tr').forEach(row => {
            const name = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
            const offerId = row.querySelector('td:nth-child(1)').textContent.toLowerCase();
            const platform = row.dataset.platform;

            const matchesSearch = name.includes(query) || offerId.includes(query);
            const matchesPlatform = !platformFilter || platform === platformFilter;

            if (matchesSearch && matchesPlatform) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    document.getElementById('search-input').addEventListener('input', applyFilters);    

    // Переключение заметок
    toggleNotes.addEventListener('click', function () {
        notes.style.display = notes.style.display === 'none' ? 'block' : 'none';
    });

    // Сабмит через fetch — чтобы обработать alert без перезагрузки
    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        alertBox.style.display = 'none';
        const data = new FormData(form);
        try {
            const resp = await fetch('/seller/manual_sale', {
                method: 'POST',
                body: data,
            });
            const json = await resp.json();
            if (json.ok) {
                window.location.href = '/seller/manual_sales';
            } else {
                alertBox.textContent = json.error || 'Ошибка';
                alertBox.style.display = 'block';
                if (json.redirect) {
                    const a = document.createElement('a');
                    a.href = json.redirect;
                    a.textContent = 'Перейти к Кладовщику → Инвентаризация';
                    a.style.display = 'inline-block';
                    a.style.marginTop = '8px';
                    alertBox.appendChild(a);
                }
            }
        } catch (err) {
            alertBox.textContent = 'Сетевая ошибка: ' + err.message;
            alertBox.style.display = 'block';
        }
    });
})();