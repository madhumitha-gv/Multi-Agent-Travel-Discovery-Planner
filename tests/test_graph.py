"""Exercise real LangGraph routing with deterministic model boundaries."""
import importlib
import sys
import types
from unittest.mock import Mock
import pytest


@pytest.fixture
def graph(monkeypatch):
    persona=types.ModuleType('agents.persona_agent')
    persona.run=lambda state,text: ['food','history']
    destination=types.ModuleType('agents.destination_agent')
    destination.run=lambda state: [{'name':name,'country':name,'lat':0,'lng':0,'score':.8} for name in ['A','B','C']]
    monkeypatch.setitem(sys.modules,'agents.persona_agent',persona)
    monkeypatch.setitem(sys.modules,'agents.destination_agent',destination)
    for module in ['langgraph_setup.nodes','langgraph_setup.trip_flow_graph','langgraph_setup.run_graph']:
        monkeypatch.delitem(sys.modules,module,raising=False)
    nodes=importlib.import_module('langgraph_setup.nodes')
    runner=importlib.import_module('langgraph_setup.run_graph')
    from utils import plan_generation
    monkeypatch.setattr(plan_generation.itinerary_agent,'run',Mock(return_value='Day 1: Explore'))
    monkeypatch.setattr(plan_generation.culture_agent,'cultural_tips',Mock(return_value='Culture'))
    monkeypatch.setattr(plan_generation.packing_agent,'generate_packing_list',Mock(return_value='Packing'))
    return nodes,runner,plan_generation


def test_backtracking_and_complete_plan(graph,monkeypatch):
    nodes,runner,agents=graph
    monkeypatch.setattr(nodes,'fetch_apparent_temperature',Mock(side_effect=[35,23]))
    events=[]
    result=runner.run_trip_planner('food and history',events.append)
    assert result['top_destination']=='B'
    assert len(result['weather_log'])==2
    assert result['itinerary']=='Day 1: Explore'
    assert result['generation_errors']==[]
    assert events


def test_all_rejected_never_calls_writing_agents(graph,monkeypatch):
    nodes,runner,agents=graph
    monkeypatch.setattr(nodes,'fetch_apparent_temperature',lambda *args: 35)
    result=runner.run_trip_planner('food and history')
    assert result['itinerary']==''
    assert result['weather_check_result']=='fail'
    agents.itinerary_agent.run.assert_not_called()
    agents.culture_agent.cultural_tips.assert_not_called()


def test_weather_outage_is_not_reported_as_comfortable(graph,monkeypatch):
    nodes,runner,_=graph
    monkeypatch.setattr(nodes,'fetch_apparent_temperature',lambda *args: None)
    result=runner.run_trip_planner('food and history')
    assert all(e['condition']=='unavailable' and e['skipped'] for e in result['weather_log'])
    assert result['itinerary']==''


def test_partial_generation_retains_successes(graph,monkeypatch):
    nodes,runner,agents=graph
    monkeypatch.setattr(nodes,'fetch_apparent_temperature',lambda *args:23)
    monkeypatch.setattr(agents.culture_agent,'cultural_tips',lambda city:'Error generating cultural tips: unavailable')
    result=runner.run_trip_planner('food and history')
    assert result['itinerary']=='Day 1: Explore'
    assert result['packing_list']=='Packing'
    assert result['culture_tips']==''
    assert result['generation_errors']==['culture_tips']


def test_approval_gate_checks_all_candidates_and_does_not_generate(graph,monkeypatch):
    nodes,runner,agents=graph
    monkeypatch.setattr(nodes,'fetch_apparent_temperature',lambda *args:23)
    result=runner.run_trip_planner('food and history',require_approval=True)
    assert result['awaiting_approval']
    assert result['weather_check_result']=='ok'
    assert len(result['weather_log'])==3
    assert result['itinerary']==''
    agents.itinerary_agent.run.assert_not_called()
    agents.culture_agent.cultural_tips.assert_not_called()


def test_unsupported_requirements_never_reach_weather_or_writers(graph,monkeypatch):
    nodes,runner,agents=graph
    monkeypatch.setattr(nodes.destination_agent, 'run', lambda state: [])
    weather=Mock()
    monkeypatch.setattr(nodes,'fetch_apparent_temperature',weather)
    result=runner.run_trip_planner('quiet beaches, no cities',require_approval=True)
    assert result['all_recommendations']==[]
    assert 'No sufficiently supported' in result['matching_message']
    assert not result.get('awaiting_approval')
    weather.assert_not_called()
    agents.itinerary_agent.run.assert_not_called()
