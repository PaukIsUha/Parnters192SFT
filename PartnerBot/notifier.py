from configs import NOTIFIER_CONFIGS
import requests
import httpx

NOTIFIES_IS_ACTIVE = False


async def register_send(name, phone, email, field_info):
    if not NOTIFIES_IS_ACTIVE:
        return

    payload = {
        "data": {
            "name": name,
            "phone": phone,
            "email": email,
            "field_info": field_info
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(NOTIFIER_CONFIGS.register_url(), json=payload)
        print(r.status_code, r.text)
    except ValueError:
        print("Нет подключения к Notifier Service")


async def reg_send(username):
    if not NOTIFIES_IS_ACTIVE:
        return

    payload = {
        "data": {
            "username": username,
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(NOTIFIER_CONFIGS.reg_url(), json=payload)
        print(r.status_code, r.text)
    except ValueError:
        print("Нет подключения к Notifier Service")


async def contact_send(username, name, phone, email, field_info):
    if not NOTIFIES_IS_ACTIVE:
        return

    payload = {
        "data": {
            "username": username,
            "name": name,
            "phone": phone,
            "email": email,
            "field_info": field_info
        }
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(NOTIFIER_CONFIGS.contact_url(), json=payload)
    print(r.status_code, r.text)


async def products_send(name, phone, email, field_info):
    if not NOTIFIES_IS_ACTIVE:
        return

    payload = {
        "data": {
            "name": name,
            "phone": phone,
            "email": email,
            "field_info": field_info
        }
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(NOTIFIER_CONFIGS.products_url(), json=payload)
    print(r.status_code, r.text)


async def start_edu_send(username, name, phone, email, field_info):
    if not NOTIFIES_IS_ACTIVE:
        return

    payload = {
        "data": {
            "username": username,
            "name": name,
            "phone": phone,
            "email": email,
            "field_info": field_info
        }
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(NOTIFIER_CONFIGS.start_edu_url(), json=payload)
    print(r.status_code, r.text)


async def finish_edu_send(username, name, phone, email, field_info):
    if not NOTIFIES_IS_ACTIVE:
        return

    payload = {
        "data": {
            "username": username,
            "name": name,
            "phone": phone,
            "email": email,
            "field_info": field_info
        }
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(NOTIFIER_CONFIGS.finish_edu_url(), json=payload)
    print(r.status_code, r.text)


async def get_indiv_send(username, name, phone, email, field_info):
    if not NOTIFIES_IS_ACTIVE:
        return

    payload = {
        "data": {
            "username": username,
            "name": name,
            "phone": phone,
            "email": email,
            "field_info": field_info
        }
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(NOTIFIER_CONFIGS.get_indiv_url(), json=payload)
    print(r.status_code, r.text)
