from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1] / 'travel_planner' / 'app.py'


def test_landing_and_validation():
    app=AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    assert app.title[0].value=='Start with a feeling. Find your next trip.'
    app.button[0].click().run()
    assert 'at least 10 characters' in app.warning[0].value
    assert not app.exception


def test_example_prompt_populates_input():
    app=AppTest.from_file(str(APP)).run(timeout=30)
    app.selectbox[0].select('Food & history').run()
    assert 'local food' in app.text_area[0].value
    assert not app.exception


def test_partial_result_and_unavailable_weather_render():
    app=AppTest.from_file(str(APP))
    app.session_state['result']={
        'persona':['food'], 'top_destination':'Tokyo', 'weather_check_result':'ok',
        'final_destination':{'country':'Japan'},
        'weather_log':[{'city':'Tokyo','temperature':None,'condition':'unavailable','skipped':True}],
        'itinerary':'', 'culture_tips':'Etiquette tips', 'packing_list':'',
        'generation_errors':['itinerary','packing_list'],
    }
    app.run(timeout=30)
    assert not app.exception
    assert any('Tokyo' in s.value for s in app.subheader)
    assert app.warning
    assert any(b.label=='Retry missing sections' for b in app.button)


def test_all_rejected_with_missing_temperature_renders_choice():
    app=AppTest.from_file(str(APP))
    app.session_state['result']={
        'persona':['food'], 'top_destination':'Tokyo','weather_check_result':'fail',
        'weather_log':[{'city':'Tokyo','temperature':None,'condition':'unavailable','skipped':True}],
    }
    app.run(timeout=30)
    assert not app.exception
    assert any(b.label=='Approve destination & build guide' for b in app.button)


def test_approval_and_trace_are_visible_before_generation():
    app=AppTest.from_file(str(APP))
    app.session_state['result']={
        'persona':['beach'], 'top_destination':'Miami', 'weather_check_result':'ok',
        'awaiting_approval':True,
        'weather_log':[{'city':'Miami','temperature':23,'condition':'warm','skipped':False}],
    }
    app.session_state['trace_events']=[{'Operation':'Discovery','Elapsed (s)':1.0,'Event':'Destination shortlist: Miami'}]
    app.run(timeout=30)
    assert not app.exception
    assert any(b.label=='Approve destination & build guide' for b in app.button)
    assert any(s.value=='Agent workflow' for s in app.subheader)
    assert any(s.value=='Agent activity trace' for s in app.subheader)
    assert any('You decide' in i.value for i in app.info)


def test_approval_button_generates_and_records_human_decision(monkeypatch):
    from utils import limits, plan_generation
    limits._starts.clear()
    limits.release()
    monkeypatch.setattr(plan_generation, 'generate_sections', lambda state: {
        'itinerary':'Day 1: Beach walk', 'culture_tips':'Local etiquette',
        'packing_list':'Clothing and essentials', 'generation_errors':[],
    })
    app=AppTest.from_file(str(APP))
    app.session_state['result']={
        'user_input':'I love oceans', 'persona':['beach'], 'top_destination':'Miami',
        'weather_check_result':'ok', 'awaiting_approval':True,
        'weather_log':[{'city':'Miami','temperature':23,'condition':'warm','skipped':False}],
    }
    app.run(timeout=30)
    next(b for b in app.button if b.label=='Approve destination & build guide').click().run(timeout=30)
    assert not app.exception
    result=app.session_state['result']
    assert not result['awaiting_approval']
    assert result['itinerary']=='Day 1: Beach walk'
    assert any('Human approval: Miami' in event['Event'] for event in app.session_state['trace_events'])
    limits._starts.clear()
