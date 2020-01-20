def init_cookie(cp :str='cookie_config') -> dict:
    try:
        cf = open(cp)
    except FileNotFoundError:
        print('W : No cookie file found!')
        return {}

    source = cf.read().replace('\n', '')

    try:
        r_items = source.split('; ')
        kv_items = []

        for item in r_items:
            k, v = item.split('=', 1)
            kv_items.append((k, v))

        return {k:v for k, v in kv_items}
    except (IndexError, ValueError):
        print('W : invalid cookie file!')
        return {}
