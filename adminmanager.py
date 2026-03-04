async def price_validation(price):
    try:
        price = int(price)

        return True
    
    except:
        return False

async def stock_validation(stock):
    try:
        stock = int(stock)

        return True
    
    except:
        return False
