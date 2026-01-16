import redis
r = redis.Redis(host='localhost', port=16379, db=0)
r.set('test_key', 'Hello Redis')
print("Redis连接成功，取值结果:", r.get('test_key').decode('utf-8'))