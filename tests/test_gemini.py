from unittest.mock import Mock
import json
import pytest
from utils import gemini
from utils.mistral import MistralError

@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY','private-test-key')
    gemini._cooldown_until=0
    monkeypatch.setattr(gemini.time,'sleep',lambda _:None)


def good(content=None):
    return Mock(ok=True,status_code=200,json=lambda:{'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(content or {'itinerary':'Two days','culture_tips':'Etiquette','packing_list':'Essentials'})}]}}]})


def test_three_sections_use_one_call(monkeypatch):
    post=Mock(return_value=good())
    monkeypatch.setattr(gemini.requests,'post',post)
    result=gemini.generate_guide({'top_destination':'Tokyo','persona':['food']})
    assert result['generation_errors']==[]
    assert post.call_count==1
    payload=post.call_args.kwargs['json']
    assert set(payload['generationConfig']['responseSchema']['required'])==set(gemini.KEYS)
    assert post.call_args.kwargs['headers']=={'x-goog-api-key':'private-test-key'}
    assert 'key=' not in post.call_args.args[0]


def test_quota_does_not_retry_or_leak(monkeypatch):
    post=Mock(return_value=Mock(ok=False,status_code=429))
    monkeypatch.setattr(gemini.requests,'post',post)
    with pytest.raises(MistralError,match='quota'):
        gemini.generate_guide({'top_destination':'Tokyo'})
    assert post.call_count==1
    with pytest.raises(MistralError):
        gemini.generate_guide({'top_destination':'Tokyo'})
    assert post.call_count==1


def test_retry_only_requested_sections(monkeypatch):
    post=Mock(return_value=good({'itinerary':'Two days'}))
    monkeypatch.setattr(gemini.requests,'post',post)
    result=gemini.generate_guide({'top_destination':'Tokyo'},only=['itinerary'])
    assert result['itinerary']=='Two days'
    assert 'culture_tips' not in result
    assert post.call_args.kwargs['json']['generationConfig']['responseSchema']['required']==['itinerary']


def test_malformed_and_truncated_response_rejected(monkeypatch):
    post=Mock(return_value=Mock(ok=True,status_code=200,json=lambda:{'candidates':[{'finishReason':'MAX_TOKENS'}]}))
    monkeypatch.setattr(gemini.requests,'post',post)
    with pytest.raises(MistralError):
        gemini.generate_guide({'top_destination':'Tokyo'})
