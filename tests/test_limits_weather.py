import contextvars
import pytest
from utils import limits
from utils.weather_utils import get_current_weather
from logger import log, bind_progress, reset_progress


def test_session_and_global_admission(monkeypatch):
    monkeypatch.setenv('SESSION_PLANS_PER_HOUR','1')
    monkeypatch.setenv('GLOBAL_PLANS_PER_HOUR','2')
    monkeypatch.setenv('GLOBAL_PLANS_PER_MINUTE','30')
    limits._starts.clear()
    limits.release()
    starts=limits.admit([])
    with pytest.raises(limits.LimitError,match='Another trip'):
        limits.admit([])
    limits.release()
    with pytest.raises(limits.LimitError,match="You've reached"):
        limits.admit(starts)
    limits.admit([])
    limits.release()
    with pytest.raises(limits.LimitError,match='hourly capacity'):
        limits.admit([])
    limits._starts.clear()


@pytest.mark.parametrize('temp,expected', [(None,'unavailable'),(float('nan'),'unavailable'),(float('inf'),'unavailable'),(15,'chilly'),(22,'warm'),(28,'hot')])
def test_weather_boundaries(temp,expected):
    assert get_current_weather(temp)==expected


def test_progress_is_request_local():
    a,b=[],[]
    def emit(target):
        token=bind_progress(target.append)
        try:
            log('only mine')
        finally:
            reset_progress(token)
    contextvars.Context().run(emit,a)
    contextvars.Context().run(emit,b)
    log('unbound')
    assert a==b==['only mine']
