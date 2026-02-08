var updateBtns = document.getElementsByClassName('update-cart')

for (i = 0; i < updateBtns.length; i++) {
	updateBtns[i].addEventListener('click', function () {
		var productId = this.dataset.product
		var action = this.dataset.action
		console.log('productId:', productId, 'Action:', action)
		console.log('USER:', user)

		if (user === 'AnonymousUser') {
			console.log('User is not authenticated')
			window.location.href = "/login/"
		} else {
			updateUserOrder(productId, action)
		}
	})
}

// Buy Now Logic
var buyNowBtns = document.getElementsByClassName('buy-now-btn')
for (i = 0; i < buyNowBtns.length; i++) {
	buyNowBtns[i].addEventListener('click', function () {
		var productId = this.dataset.product
		var action = this.dataset.action
		console.log('Buy Now - productId:', productId)

		if (user === 'AnonymousUser') {
			console.log('User is not authenticated')
			window.location.href = "/login/"
		} else {
			// Add to cart then redirect
			var url = '/update_item/'
			fetch(url, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken,
				},
				body: JSON.stringify({ 'productId': productId, 'action': action })
			})
				.then((response) => {
					return response.json();
				})
				.then((data) => {
					console.log('Data:', data)
					window.location.href = "/checkout/" // Redirect to Checkout
				});
		}
	})
}

function updateUserOrder(productId, action) {
	console.log('User is authenticated, sending data...')

	var url = '/update_item/'

	fetch(url, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-CSRFToken': csrftoken,
		},
		body: JSON.stringify({ 'productId': productId, 'action': action })
	})
		.then((response) => {
			return response.json();
		})
		.then((data) => {
			console.log('Data:', data)
			location.reload() // Reload to update cart count
		});
}
