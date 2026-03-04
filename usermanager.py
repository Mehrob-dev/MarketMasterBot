async def name_validation(name):
    
    if len(name) < 3:
        return False
    
    for c in name:
        if not c.isalpha():
            return False 
    
    return True

async def surname_validation(surname):

    if len(surname) < 3:
        return False
    
    for c in surname:
        if not c.isalpha():
            return False 
    
    return True

async def age_validation(age):

    try:
        age = int(age)
        if age < 6 or age > 100:
            return False

        return True

    except:
        return False

async def review_validation(review):
    try:
        review = int(review)
        if review < 0 or review > 5:
            return False
        
        else:
            return True
    
    except:
        return False
