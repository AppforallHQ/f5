import django
django.setup()


import sys
usage = """\
Usage: batch-create-promo-code.py NUM TYPE PARTNER

NUM:        number of codes to be generated
TYPE:       PromoType label
PARTNER:    name of the partner
"""

if len(sys.argv) != 4:
    print usage
    exit(1)

num = int(sys.argv[1])
label = sys.argv[2]
partner = sys.argv[3]
from pprint import pprint

from plans.models import PromoCode, PromoType

for promocode in PromoCode.generate(num,label,partner):
    print promocode.code
