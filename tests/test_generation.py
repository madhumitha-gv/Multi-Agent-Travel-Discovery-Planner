from unittest.mock import Mock
import pytest
import requests
from utils import mistral

@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setenv('HUGGINGFACEHUB_API_TOKEN', 'test-secret')
    monkeypatch.setenv('GEN_CANDIDATES', 'bad|org/first,auto|org/second')
    mistral._cooldown_until.clear()
    monkeypatch.setattr(mistral.time, 'sleep', lambda _: None)


def response(status=200, content='A useful plan'):
    return Mock(ok=status < 400, status_code=status, json=lambda: {'choices':[{'message':{'content':content}}]})


def test_fallback_and_router_model(monkeypatch):
    post=Mock(side_effect=[response(404), response()])
    monkeypatch.setattr(mistral.requests,'post',post)
    assert mistral.generate('trip') == 'A useful plan'
    assert post.call_args_list[0].kwargs['json']['model'] == 'org/first:bad'
    assert post.call_args_list[1].kwargs['json']['model'] == 'org/second'


def test_retry_transient(monkeypatch):
    post=Mock(side_effect=[response(503), response()])
    monkeypatch.setattr(mistral.requests,'post',post)
    assert mistral.generate('trip') == 'A useful plan'
    assert post.call_count == 2


@pytest.mark.parametrize('bad_content', [None, [], {}, '', '   '])
def test_malformed_content_falls_back(monkeypatch,bad_content):
    monkeypatch.setattr(mistral.requests,'post',Mock(side_effect=[response(content=bad_content),response()]))
    assert mistral.generate('trip') == 'A useful plan'


def test_auth_error_never_exposes_body(monkeypatch):
    post=Mock(return_value=response(401))
    monkeypatch.setattr(mistral.requests,'post',post)
    with pytest.raises(mistral.MistralError,match='temporarily unavailable'):
        mistral.generate('private prompt')
    assert post.call_count == 1
    with pytest.raises(mistral.MistralError):
        mistral.generate('trip')
    assert post.call_count == 1


def test_network_outage_and_cooldown(monkeypatch):
    post=Mock(side_effect=requests.Timeout('secret response'))
    monkeypatch.setattr(mistral.requests,'post',post)
    with pytest.raises(mistral.MistralError) as error:
        mistral.generate('trip')
    assert 'secret' not in str(error.value)
    assert post.call_count == 4
    with pytest.raises(mistral.MistralError):
        mistral.generate('trip')
    assert post.call_count == 4


def test_bad_settings_are_safe(monkeypatch):
    monkeypatch.setenv('GEN_TIMEOUT','nonsense')
    monkeypatch.setenv('GEN_CANDIDATES','garbage')
    with pytest.raises(mistral.MistralError):
        mistral.generate('trip')


def test_credit_exhaustion_skips_retry_and_fallback(monkeypatch):
    post=Mock(return_value=response(402))
    monkeypatch.setattr(mistral.requests,'post',post)
    with pytest.raises(mistral.MistralError):
        mistral.generate('trip')
    assert post.call_count == 1
