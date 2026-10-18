from unittest.mock import Mock
import pytest
from utils import mistral

@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY','private-test-key')
    monkeypatch.setenv('HUGGINGFACEHUB_API_TOKEN','hf-test-key')
    monkeypatch.setenv('GEN_CANDIDATES','gemini|gemini-2.5-flash,auto|org/fallback')
    mistral._cooldown_until.clear()
    monkeypatch.setattr(mistral.time,'sleep',lambda _:None)


def gemini(content='A complete answer'):
    return Mock(ok=True,status_code=200,json=lambda:{'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':content}]}}]})


def hf():
    return Mock(ok=True,status_code=200,json=lambda:{'choices':[{'message':{'content':'HF answer'}}]})


def test_same_signature_routes_to_gemini(monkeypatch):
    post=Mock(return_value=gemini())
    monkeypatch.setattr(mistral.requests,'post',post)
    assert mistral.generate('trip', max_tokens=400, temperature=.3)=='A complete answer'
    call=post.call_args
    assert call.kwargs['headers']=={'x-goog-api-key':'private-test-key'}
    assert call.kwargs['json']['generationConfig']['maxOutputTokens']==400
    assert 'key=' not in call.args[0]
    assert post.call_count==1


@pytest.mark.parametrize('status',[429,401,403])
def test_gemini_failure_falls_through_and_cools_only_gemini(monkeypatch,status):
    post=Mock(side_effect=[Mock(ok=False,status_code=status),hf(),hf()])
    monkeypatch.setattr(mistral.requests,'post',post)
    assert mistral.generate('trip')=='HF answer'
    assert post.call_count==2
    assert mistral.generate('second trip')=='HF answer'
    assert post.call_count==3
    assert all('router.huggingface.co' in c.args[0] for c in post.call_args_list[1:])


def test_gemini_503_retries_then_falls_back(monkeypatch):
    post=Mock(side_effect=[Mock(ok=False,status_code=503),Mock(ok=False,status_code=503),hf()])
    monkeypatch.setattr(mistral.requests,'post',post)
    assert mistral.generate('trip')=='HF answer'
    assert post.call_count==3


def test_missing_gemini_credential_still_uses_hf(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY')
    post=Mock(return_value=hf())
    monkeypatch.setattr(mistral.requests,'post',post)
    assert mistral.generate('trip')=='HF answer'
    assert post.call_count==1


def test_bad_first_candidate_then_gemini(monkeypatch):
    monkeypatch.setenv('GEN_CANDIDATES','bogus|fake/model,gemini|gemini-2.5-flash')
    post=Mock(side_effect=[Mock(ok=False,status_code=404),gemini()])
    monkeypatch.setattr(mistral.requests,'post',post)
    assert mistral.generate('trip')=='A complete answer'
    assert post.call_count==2


def test_hf_auth_failure_does_not_disable_gemini(monkeypatch):
    monkeypatch.setenv('GEN_CANDIDATES','auto|org/model,gemini|gemini-2.5-flash')
    post=Mock(side_effect=[Mock(ok=False,status_code=401),gemini()])
    monkeypatch.setattr(mistral.requests,'post',post)
    assert mistral.generate('trip')=='A complete answer'


def test_time_budget_reserved_for_fallback(monkeypatch):
    monkeypatch.setenv('GEN_TIMEOUT','60')
    monkeypatch.setenv('GEN_TOTAL_TIMEOUT','40')
    post=Mock(side_effect=[Mock(ok=False,status_code=503),Mock(ok=False,status_code=503),hf()])
    monkeypatch.setattr(mistral.requests,'post',post)
    assert mistral.generate('trip')=='HF answer'
    assert post.call_args_list[0].kwargs['timeout'] <= 10
    assert post.call_args_list[-1].kwargs['timeout'] > 0
