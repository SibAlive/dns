document.addEventListener('DOMContentLoaded', function() {
    // Функция для получения CSRF-токена
    function getCookie(name) {
        let value = "; " + document.cookie;
        let parts = value.split("; " + name + "=");
        if (parts.length === 2) return parts.pop().split(";").shift();
    }

    document.addEventListener('click', function(event) {
        const target = event.target.closest('.favorite-toggle-btn');
        if (!target) return;
        event.preventDefault();

        const productId = target.dataset.productId;
        console.log('Отправка AJAX для productId', productId);

        fetch(window.toggleFavoriteUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken || getCookie('csrf_token')
            },
            body: JSON.stringify({product_id: productId})
        })
        .then(response => {
            if (!response.ok) throw new Error('Ошибка HTTP ' + response.status);
            return response.json();
        })
        .then(data => {
            if(data.status === 'added') {
                target.classList.add('is-fav');
            } else if(data.status === 'removed') {
                target.classList.remove('is-fav');
            }
        })
        .catch(error => console.error('Ошибка запроса:', error));
    });
});