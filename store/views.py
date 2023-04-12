from django.shortcuts import render
from django.db.models import Q
from .models import *
from django.http import JsonResponse
import json
import datetime

from .utils import cookieCart, cartData, guestOrder

# Create your views here.
def categories_processor(request):
    data = cartData(request)
    cartItems = data['cartItems']
    return {'cartItems':cartItems, 'shipping': True}



def store(request):
    query = request.GET.get('query', '')
    price_from = request.GET.get('price_from', 0)
    price_to = request.GET.get('price_to', 100000)
    sorting = request.GET.get('sorting', '-name')
    #products = Product.objects.order_by('-name')
    products = Product.objects.filter(Q(name__icontains=query)).filter(price__gte=price_from).filter(price__lte=price_to)
    context = {'products': products.order_by(sorting),
               'query':query,
               'price_from':price_from,
               'price_to':price_to,
               'sorting':sorting}
    return render(request, 'store/store.html', context)

def cart(request):
    data = cartData(request)
    order = data['order']
    items = data['items']
    
    context = {'items': items, 'order': order}
    return render(request, 'store/cart.html', context)

def checkout(request):
    data = cartData(request)
    order = data['order']
    items = data['items']
    
    context = {'items': items, 'order': order}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    productId=data['productId']
    action=data['action']
    
    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(
            customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(
        order=order, product=product)
    if action == 'add':
        orderItem.quantity =(orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity =(orderItem.quantity - 1)
    orderItem.save()
    
    if orderItem.quantity <= 0:
        orderItem.delete()
    
    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(
            customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)
    
    total = float(data['form']['total'])
    order.transaction_id = transaction_id
        
    if total == order.get_cart_total:
        order.complete = True
    order.save()
    
    if order.shipping == True:
        ShippingAddress.objects.create(
            customer = customer,
            order = order,
            address = data['shipping']['address'],
            city = data['shipping']['city'],
            state = data['shipping']['state'],
            zipcode = data['shipping']['zipcode'],
        )
    
    return JsonResponse('Payment complete', safe=False)