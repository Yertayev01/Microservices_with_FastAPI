from fastapi import FastAPI
from redis_om import get_redis_connection, HashModel
from fastapi.middlleware.cors import CORSMiddleware
from fastapi.background import BackgroundTasks
from starlette.requests import Request
import requests, time

app = FastAPI()

app.middleware(
    CORSMiddleware,
    allow_origins = ['*'],
    allow_methods = ['*'],
    allow_headers = ['*']
)

# this should be different database
redis = get_redis_connection(
    host = "redis-19347.c309.us-east-2-1.ec2.cloud.redislabs.com",
    port = 19347,
    password = "E4nFlFqx3ai519j3rhWLGDkgR656UvgI",
    decode_responses = True
)

class Order(HashModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str #pending, completed, refunded

    class Meta:
        database = redis

@app.get('/orders/{pk}')
def get(pk: str):
    
    #redis.xadd('refund_order', order.dict(), '*') 
    return Order.get(pk)

@app.post('/orders')
async def create(request: Request, background_tasks: BackgroundTasks): #id and quantity
    body = await request.json()

    req = requests.get('http://localhost:8000/products/%s' % body['id'])

    product = req.json()

    order = Order(
        product_id = body['id'],
        price = product['price'],
        fee = 0.2 * product['price'],
        total = 1.2 * product['price'],
        quantity = body['quantity'],
        status = 'pending'
    )
    order.save()

    background_tasks.add_task(order_completed, order)
    
    return order


def order_completed(order: Order):

    time.sleep(5)
    
    order.status = 'completed'
    
    order.save()

    redis.xadd('order_completed', order.dict(), '*')