from unittest.mock import patch
from utils.media import evidence_image
calls=[]
def old(image, width=None, use_column_width=False): calls.append(use_column_width)
def middle(image, width=None, use_container_width=False): calls.append(use_container_width)
def current(image, width='content'): calls.append(width)
for api, expected in [(old,True),(middle,True),(current,'stretch')]:
    with patch('utils.media.st.image',api): evidence_image('evidence.png')
    assert calls[-1] == expected
print('PASS: old, intermediate and current image API signatures')
