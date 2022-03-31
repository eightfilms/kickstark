import time

from tests.Signer import Signer
from tests.utils import to_uint

FALSE, TRUE = 0, 1

SOME_SIGNER = Signer(123456789987654321)

SOME_AMOUNT = to_uint(100)
SOME_AMOUNT_HALF = to_uint(50)

SOME_ID = 0
TOKEN_ID = to_uint(5042)

NOW_TIMESTAMP = int(time.time())
EARLIER_TIMESTAMP = NOW_TIMESTAMP - 7 * 60 * 60 * 24
SOME_LATER_TIMESTAMP = NOW_TIMESTAMP + 1 * 60 * 60
END_TIMESTAMP = NOW_TIMESTAMP + 1 * 60 * 60 * 24
