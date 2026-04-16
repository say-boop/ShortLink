import random
import string
from sqlalchemy.orm import Session
from app.models.link import Link


def generate_random_string(length: int = 6) -> str:
  alphabet = string.ascii_letters + string.digits
  random_string = random.choices(alphabet, k=length)
  result_string = "".join(random_string)
  
  return result_string

def generate_unique_short_code(db: Session, length: int = 6) -> str:
  while True:
    gen_code = generate_random_string(length)
    check_code_in_db = db.query(Link).filter(Link.short_code == gen_code).first()
    
    if not check_code_in_db:
      return gen_code

